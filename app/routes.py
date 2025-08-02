# flask_app/routes.py

from flask import (
    render_template, jsonify, request, redirect, url_for, abort, flash
)
from flask_login import (
    login_user, current_user, logout_user, login_required
)
import json
import os
from app.forms import LoginForm, SignupForm
import stripe
from pydantic import BaseModel
from ast import literal_eval
from flask_wtf.csrf import generate_csrf, CSRFProtect
from app import app, db, bcrypt, csrf # Assuming 'app', 'db', 'bcrypt', 'csrf' are initialized in app/__init__.py
from app.models import User, QuestionHistory, Assessment, AssessmentResult
from backend.log_helper.report import log_message
# Import async versions of your processing functions
from werkzeug.utils import secure_filename
import uuid
from backend.pipeline.pipe import process_article, process_document, process_yt
from datetime import timedelta

UPLOAD_FOLDER = os.path.join(app.root_path, 'uploads') # Create an 'uploads' directory
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# --- Pydantic Models ---
class FileInput(BaseModel):
    # If the file is uploaded via FormData, file_path might not be directly from JSON.
    # This Pydantic model is typically for JSON body parsing.
    # For file uploads, Flask's request.files is used.
    # If file_path here means a path on the server already, then it's fine.
    # Assuming it's a conceptual path, or you handle actual file upload elsewhere.
    file_path: str
    num_questions: int = 10

class URLInput(BaseModel):
    url: str
    num_questions: int = 10


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = SignupForm()
    if request.method == 'POST':
        print(request.form)
        username = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_pw)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))  # Redirect to pricing if already logged in

    form = LoginForm()
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember-me') == 'on'  # Checkbox returns 'on' when checked

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=remember)
            flash('Login successful', 'success')
            return redirect(url_for('pricing'))

        # If we get here, login failed
        flash('Invalid email or password', 'danger')

    return render_template('login.html', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('login'))


def load_questions(topic_filename="questions.json"):
    data_path = os.path.join(app.root_path, 'data', topic_filename)
    try:
        file = open(data_path, 'a', encoding='utf-8')
        file.close()
        with open(data_path, 'r', encoding='utf-8') as f:
            log_message("File found, loading file for rendering")
            return json.load(f)
    except FileNotFoundError:
        log_message(f"Error: File '{topic_filename}' not found.", "error")
        return None
    except json.JSONDecodeError:
        log_message(f"Error decoding JSON from {topic_filename}. Check file format.", 'error')
        return None

@app.route('/forgot-password')
def forgot_password():
    return render_template('error.html', message="This page hasn't been populated yet")

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate')
@login_required
def generate():
    return render_template('generate.html')


@app.route('/questions')
@app.route('/questions/<topic>')
@login_required
def show_questions(topic="questions.json"):
    questions_data = load_questions(topic)
    if questions_data:
        if 'topic' not in questions_data or 'questions' not in questions_data:
            return render_template('error.html', message=f"Invalid JSON structure for '{topic}'."), 500
        log_message(f"Questions data from routes: \n\n\n\n\n: {questions_data}\n\n")
        return render_template('questions.html', topic_data=questions_data)
    else:
        return render_template('error.html', message=f"No questions found for '{topic}' or file not accessible."), 404


@app.route('/payment')
@login_required
def payment():
    return render_template('payment.html')


@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')

@app.route('/pricing')
def pricing():
    return render_template('pricing.html', config=app.config)


@app.route('/create-checkout-session', methods=['POST'])
def create_checkout_session():
    try:
        data = request.get_json()
        price_id = data.get('priceId')

        if not price_id:
            return jsonify({'error': 'Price ID is required'}), 400

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription',
            success_url=url_for('payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('payment_cancel', _external=True),
        )
        return jsonify({'checkout_url': checkout_session.url})
    except stripe.error.StripeError as e:
        log_message(f"Stripe Error: {e}", 'error')
        # Return JSON error for API endpoint
        return jsonify({'error': f"A Stripe error occurred: {e.user_message}"}), 500
    except Exception as e:
        log_message(f"Server Error in checkout session: {e}", 'error')
        # Return JSON error for API endpoint
        return jsonify({'error': f"An internal server error occurred: {str(e)}"}), 500


@app.route('/payment-success')
def payment_success():
    session_id = request.args.get('session_id')
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            log_message(f"Payment successful for session: {session.id}, Customer: {session.customer_details.email}")
            return render_template('payment_status.html', status='success', session=session)
        except stripe.error.StripeError as e:
            log_message(f"Error retrieving Stripe session: {e}", 'error')
            return render_template('payment_status.html', status='error', message='Failed to retrieve payment details.'), 400
    return redirect(url_for('index'))


@app.route('/payment-cancel')
def payment_cancel():
    return render_template('payment_status.html', status='cancelled', message='Payment was cancelled.')


@app.route("/api/generate/file", methods=['POST'])
@csrf.exempt
def generate_questions_from_file_api():
    """
    Generates questions from an uploaded file.
    Accepts multipart/form-data with a 'file' and 'numQuestions'.
    """
    try:
        # Check if the 'file' part is in the request
        if 'file' not in request.files:
            log_message(f"No file part in the request.", 'error')
            return jsonify({"error": "No file part in the request"}), 400

        uploaded_file = request.files['file']
        
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if uploaded_file.filename == '':
            log_message(f"No selected file.", 'error')
            return jsonify({"error": "No selected file"}), 400

        # Secure the filename to prevent directory traversal attacks
        filename = secure_filename(uploaded_file.filename)
        title = filename.split(".")[0]
        # Define the full path where the file will be saved
        file_path_on_server = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save the uploaded file temporarily
        uploaded_file.save(file_path_on_server)
        log_message(f"File '{filename}' saved temporarily to {file_path_on_server}", 'info')

        # Get numQuestions from the form data (not JSON body)
        num_questions_str = request.form.get('numQuestions')
        if not num_questions_str:
            # Clean up the uploaded file if numQuestions is missing
            os.remove(file_path_on_server)
            log_message(f"numQuestions not provided in form data.", 'error')
            return jsonify({"error": "Number of questions (numQuestions) is required."}), 400

        try:
            num_questions = int(num_questions_str)
            if not (1 <= num_questions <= 20):
                # Clean up the uploaded file if numQuestions is invalid
                os.remove(file_path_on_server)
                return jsonify({"error": "Number of questions must be between 1 and 20."}), 400
        except ValueError:
            # Clean up the uploaded file if numQuestions is not an integer
            os.remove(file_path_on_server)
            log_message(f"Invalid numQuestions value: {num_questions_str}", 'error')
            return jsonify({"error": "Number of questions must be an integer."}), 400

        # --- Await the async process_document function ---
        # Now pass the path to the temporarily saved file
        try:
            questions = process_document(file_path_on_server, num_questions)
            if not questions and not title: # Check if no content was extracted
                log_message(f"Document '{file_path_on_server}' processed, but no questions/title extracted.", 'info')
                return jsonify({"error": "Document processing failed to extract content or title."}), 400

            response_data = {"topic": title, "questions": questions[:num_questions]}
        except Exception as e:
            log_message(f"An error occurred while processing the document: {e}", "error")
            return jsonify({"error": f"Failed to process document: {e}. Please check the file content."}), 400
        finally:
            # --- IMPORTANT: Clean up the temporarily saved file ---
            if os.path.exists(file_path_on_server):
                os.remove(file_path_on_server)
                log_message(f"Cleaned up temporary file: {file_path_on_server}", 'info')

        
        # Save the JSON response to a file (this part remains the same)
        output_file_path = os.path.join(app.root_path, "data", "questions.json")
        with open(output_file_path, "w", encoding='utf-8') as f:
            try:
                json.dump(response_data, f, indent=2)
                log_message(f"Successfully dumped data to {output_file_path}")
            except Exception as e:
                log_message(f"Error while dumping JSON to file {output_file_path}: {e}", "error")

        if current_user.is_authenticated and (questions != [] and bool(title)):
            history = QuestionHistory(
                user_id=current_user.id,
                title=title,
                questions=json.dumps(questions)
            )
            db.session.add(history)
            db.session.commit()
        return jsonify(response_data)

    except Exception as e:
        log_message(f"Error in /api/generate/file: {e}", 'error')
        return jsonify({"error": f"An unexpected server error occurred during file processing: {str(e)}"}), 500

@app.route("/api/generate/url", methods=['POST'])
@csrf.exempt
def generate_questions_from_url_api():
    """
    Generates questions from a given URL.
    Accepts JSON body.
    """
    questions = None
    title = None

    try:
        try:
            input_data = URLInput(**request.json)
            log_message("Input data fetched")
        except Exception as e:
            log_message(f"Invalid request body: {e}", 'error')
            return jsonify({"error": f"Invalid request body: {e}"}), 400

        url = input_data.url
        num_questions = input_data.num_questions

        if not url.startswith(("http://", "https://")):
            log_message(f"Invalid URL format received: {url}", 'error')
            return jsonify({"error": "Invalid URL format. URL must start with http:// or https://", "status_code": 400}), 400

        if "youtu" in url:
            try:
                # --- Await the async process_yt function ---
                response_tuple = process_yt(url=url, num_questions=num_questions)
                log_message(f"Youtube response raw: {response_tuple}")
                try:
                    questions, title = response_tuple
                except (TypeError, ValueError) as e:
                    log_message(f"Error unpacking YouTube response: {e}. Raw response: {response_tuple}", "error")
                    return jsonify({"error": "Internal processing error: Could not unpack YouTube data.", "status_code": 500}), 500
            except Exception as e:
                log_message(f"Could not process Youtube link: {e}" , 'error')
                return jsonify({"error": f"Failed to process YouTube link: {e}. Check the URL and try again."}), 400
        else:
            try:
                # --- Await the async process_article function ---
                response_tuple = process_article(url=url, num_questions=num_questions)
                log_message(f"Article response raw: {response_tuple}")
                try:
                    questions, title = response_tuple
                except (TypeError, ValueError) as e:
                    log_message(f"Error unpacking article response: {e}. Raw response: {response_tuple}", "error")
                    return jsonify({"error": "Internal processing error: Could not unpack article data.", "status_code": 500}), 500

                # Specific condition for when the link "withstood the Inquisition"
                if not questions and not title:
                    log_message(f"Link '{url}' could not be processed for questions. Returning JSON error.", 'error')
                    return jsonify({"error": "The link you entered withstood the Inquisition. Try another link!"}), 400
            except Exception as e:
                log_message(f"Could not process article: {e}", 'error')
                return jsonify({"error": f"Failed to process article. Please check the URL or try again later."}), 400

        # Final check to ensure questions and title are not None/empty
        if not questions or not title:
            log_message("Question generation resulted in no questions or title, but no explicit error occurred.", 'error')
            return jsonify({"error": "Question generation failed: No content or title could be extracted. Please try a different URL.", "status_code": 500}), 500

        response_data = {"topic": title, "questions": questions}

        # Save the JSON response to a file
        output_file_path = os.path.join(app.root_path, "data", "questions.json")
        with open(output_file_path, "w", encoding='utf-8') as f:
            try:
                json.dump(response_data, f, indent=2)
                log_message(f"Successfully dumped data to {output_file_path}")
            except Exception as e:
                log_message(f"Error while dumping JSON to file {output_file_path}: {e}", "error")

        if current_user.is_authenticated and (questions != [] and bool(title)):
            history = QuestionHistory(
                user_id=current_user.id,
                title=title,
                questions=json.dumps(questions)
            )
            db.session.add(history)
            db.session.commit()
        return jsonify(response_data)

    except Exception as e:
        log_message(f"An unexpected error occurred in /api/generate/url: {e}", 'critical')
        return jsonify({"error": f"An unexpected server error occurred: {str(e)}", "status_code": 500}), 500

@app.route("/history")
@login_required
def view_history():
    history_records = QuestionHistory.query.filter_by(
        user_id=current_user.id,
    ).order_by(QuestionHistory.created_at.desc()).all()
    return render_template("history.html", records = history_records)


@app.route('/load_record/<int:record_id>')
@login_required
def load_history_record(record_id):
    record = QuestionHistory.query.filter_by(id=record_id, user_id=current_user.id).first_or_404()

    # Check if a file already exists
    if record.filename:
        return redirect(url_for('show_questions', topic=record.filename))

    # Decode questions from DB
    try:
        questions_data = json.loads(record.questions)
    except json.JSONDecodeError:
        flash("Invalid questions format in database.", "error")
        return redirect(url_for('view_history'))

    # Create a safe, unique filename
    safe_title = secure_filename(record.title) or "untitled"
    unique_id = str(uuid.uuid4())[:8]
    filename = f"user_{current_user.id}_{safe_title}_{unique_id}.json"
    filepath = os.path.join(app.root_path, 'data', filename)

    # Save the questions to the file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "topic": record.title,
                "questions": questions_data
            }, f, indent=2, ensure_ascii=False)
    except IOError:
        flash("Could not save questions file.", "error")
        return redirect(url_for('view_history'))

    # Save filename to the database
    record.filename = filename
    db.session.commit()

    # Redirect to view questions
    return redirect(url_for('show_questions', topic=filename))

@app.route('/retrieveassessments', methods=['GET'])
def retrieve_assessments():
    try:
        assessments = Assessment.query.all()
        
        if not assessments:
            return jsonify([]), 200
        
        result = []
        for a in assessments:
            result.append({
                "title": a.name,
                "subject": a.code,
                "duration": f"{a.duration_hour}h {a.duration_minute}m"
            })
        return jsonify(result), 200

    except Exception as e:
        app.logger.error(f"Error retrieving assessments: {e}")
        return jsonify({"error": "Failed to fetch assessments."}), 500

   
@app.route('/assessmentdetails/<int:assessment_id>', methods=['GET'])
def get_assessment_details(assessment_id):
    try:
        assessment = Assessment.query.get_or_404(assessment_id)
        results = AssessmentResult.query.filter_by(assessment_id=assessment_id).all()

        if not results:
            return jsonify({"error": "No results for this assessment."}), 404

        total_students = len(results)
        total_score = sum(r.score for r in results)
        passed_count = sum(1 for r in results if r.score >= 50)

        average_score = round(total_score / total_students, 2)
        pass_rate = round((passed_count / total_students) * 100, 2)

        students_data = [
            {"name": r.student_name, "regNo": r.reg_no, "score": r.score}
            for r in results
        ]

        response = {
            "title": assessment.name,
            "metrics": {
                "average_score": average_score,
                "pass_rate": pass_rate,
                "total_questions": 50  # Replace with dynamic count if needed
            },
            "students": students_data
        }

        return jsonify(response), 200

    except Exception as e:
        app.logger.error(f"Error retrieving assessment details: {e}")
        return jsonify({"error": "Internal server error."}), 500


@app.route('/start-assessment', methods=['POST'])
def start_assessment():
    try:
        data = request.get_json()
        access_code = data.get("access_code")
        assessment_id = data.get("assessment_id")

        if not all([access_code, assessment_id]):
            return jsonify({"error": "Missing access code or assessment ID."}), 400

        assessment = Assessment.query.filter_by(id=assessment_id, code=access_code).first()
        if not assessment:
            return jsonify({"error": "Assessment not found or invalid access code."}), 404

        return jsonify({
            "message": "Assessment access granted.",
            "assessment_id": assessment.id,
            "assessment_name": assessment.name,
            "instructions": assessment.instructions,
            "duration": {
                "hour": assessment.duration_hour,
                "minute": assessment.duration_minute
            },
            "questions": assessment.assessment_questions or []
        }), 200

    except Exception as e:
        app.logger.error(f"Error starting assessment: {e}")
        return jsonify({"error": "Internal server error."}), 500