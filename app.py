# flask_app/app.py (or your main Flask app file)
from flask import Flask, render_template, jsonify, request, redirect, url_for, abort
import json
import os
import stripe
from pydantic import BaseModel # Keep Pydantic for validation if you like, or use simple dictionary checks
from backend.log_helper.report import log_message
# Import your backend processing functions directly
# Adjust this import path based on where 'backend' folder is relative to this file
from backend.pipeline.pipe import process_article, process_document, process_yt
from flask_cors import CORS
from backend.pipeline.helper import get_content_between_curly_braces
from ast import literal_eval

app = Flask(__name__)
app.config.from_pyfile('config.py')
CORS(app)
# Optional: Set Stripe API key from config for direct use
#stripe.api_key = app.config.get('STRIPE_SECRET_KEY')

# --- Pydantic Models (Optional but good for explicit schema definition) ---
# If you don't want Pydantic, you can remove these and use manual request.json checks
class FileInput(BaseModel):
    file_path: str
    num_questions: int = 10

class URLInput(BaseModel):
    url: str
    num_questions: int = 10

# --- Helper to load questions (remains) ---
def load_questions(topic_filename):
    data_path = os.path.join(app.root_path, 'data', topic_filename)
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            log_message("File found, loading file for rendering")
            return json.load(f)
    except FileNotFoundError:
        # In a combined app, this might be handled by an API route returning 404
        log_message(f"Error: File '{topic_filename}' not found.", "error")
        return None
    except json.JSONDecodeError:
        log_message(f"Error decoding JSON from {topic_filename}. Check file format.", 'error')
        return None

# --- Existing Flask Routes (unchanged) ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate')
def generate():
    # This route will likely contain forms that post to the new /api/generate/file or /api/generate/url
    return render_template('generate.html')

@app.route('/questions')
@app.route('/questions/<topic>')
def show_questions(topic='science_questions.json'):
    questions_data = load_questions(topic)
    if questions_data:
        if 'topic' not in questions_data or 'questions' not in questions_data:
            return render_template('error.html', message=f"Invalid JSON structure for '{topic}'."), 500
        return render_template('questions.html', topic_data=questions_data)
    else:
        return render_template('error.html', message=f"No questions found for '{topic}' or file not accessible."), 404

@app.route('/about')
def about():
    return render_template('about.html')

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
        return render_template('error.html', message=f"An Error Occurred: {e.user_message}"), 500 # Use user_message for Stripe errors
    except Exception as e:
        log_message(f"Server Error: {e}", 'error')
        return render_template('error.html', message=f"An Internal Server Error occurred: {str(e)}"), 500


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

@app.route('/suggest-feature')
def suggest_feature():
    return render_template('error.html', message=f"We haven't populated this page...Stay Tuned"), 404

@app.route('/report-bug')
def report_bug():
    return render_template('error.html', message=f"We haven't populated this page...stay Tuned"), 404


# --- New API Routes for Question Generation (from FastAPI) ---

@app.route("/api/generate/file", methods=['POST'])
def generate_questions_from_file_api():
    """
    Generates questions from a local file path.
    Accepts JSON body.
    """
    try:
        # Use Pydantic for validation, or manually parse request.json
        # If using Pydantic, ensure Flask handles validation errors gracefully
        try:
            input_data = FileInput(**request.json)
        except Exception as e:
            abort(400, description=f"Invalid request body: {e}")

        file_path = input_data.file_path
        num_questions = input_data.num_questions

        # Call the backend logic directly
        # Ensure process_document is compatible (synchronous or properly awaited)
        try:
            questions = process_document(file_path, num_questions)
            response_data = {"file_path": file_path, "questions": questions[:num_questions]}
        except Exception as e:
            log_message(f"An error occurred while processing the document: {e}", "error")

        # Save the JSON response to a file (optional, as Flask will return it)
        with open("data/questions.json", "w") as f:
            json.dump(response_data, f, indent=4)

        return jsonify(response_data)

    except Exception as e:
        # Catch and handle errors, similar to FastAPI HTTPException
        log_message(f"Error in /api/generate/file: {e}", 'error')
        abort(500, description=f"An unexpected error occurred: {str(e)}")


@app.route("/api/generate/url", methods=['POST'])
def generate_questions_from_url_api():
    """
    Generates questions from a given URL.
    Accepts JSON body.
    """
    try:
        try:
            input_data = URLInput(**request.json)
            log_message("Input data fetched")
        except Exception as e:
            abort(400, description=f"Invalid request body: {e}")
            log_message(f"An error occurred while fetching input data: {e}", 'error')

        
        url = input_data.url
        num_questions = input_data.num_questions

        if not url.startswith(("http://", "https://")):
            abort(400, description="Invalid URL format. URL must start with http:// or https://")

        # Call the backend logic directly
        # Ensure process_yt/process_article are compatible (synchronous or properly awaited)
        if "youtu" in url:
            try:
                response = process_yt(url=url, num_questions=num_questions)

                try:
                    log_message(f"Youtube response: {response}")
                    questions, title = response
                except Exception as e:
                    log_message(f"An error occurred while trying to unpackL {e}", "error")
            except Exception as e:
                log_message(f"Could not process Youtube link: {e}" , 'error')
        else:
            try:
                questions, title = process_article(url=url, num_questions=num_questions)
            except Exception as e:
                log_message(f"Could not process article: {e}", 'error')

        response_data = {"topic": title, "questions": questions}

        # Save the JSON response to a file (optional)
        with open("data/questions.json", "w") as f:
            try:
                json.dump(response_data, f, indent=2)
                log_message("Successfully dumped data")
            except Exception as e:
                log_message(f"Error while processing JSON: {json.dump(response_data)}, {e}", "error")

        return jsonify(response_data)

    except Exception as e:
        log_message(f"Error in /api/generate/url: {e}", 'error')
        abort(500, description=f"An unexpected error occurred: {str(e)}")


if __name__ == '__main__':
    # When running directly for development
    app.run(debug=True)