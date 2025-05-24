# question_app/app.py
from flask import Flask, render_template, jsonify, request, redirect, url_for
import json
import os
import stripe

app = Flask(__name__)
# Load secret key from config.py or environment for production
app.config.from_pyfile('config.py')

# Function to load questions from a JSON file
def load_questions(topic_filename):
    # Ensure the path is correct for where your data files are located
    data_path = os.path.join(app.root_path, 'data', topic_filename)
    print(data_path)
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return render_template('error.html', message=f"Oops, we couldn't find the file you uploaded. Try uploading it again"), 500
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {topic_filename}. Check file format.")
        return None

@app.route('/')
def index():
    # You could dynamically list topics here by scanning the 'data' directory
    # For now, let's just render the homepage
    # The 'Inquisitor from Stitch.html' content would primarily go into questions.html
    # so index.html can be a simpler landing page or a topic selection page.
    return render_template('index.html')

@app.route('/generate')
def generate():
    # Placeholder for a future "Generate Questions" page
    # This might involve AI model integration later.
    return render_template('generate.html') # You'll create this template later

@app.route('/questions')
@app.route('/questions/<topic>')
def show_questions(topic='science_questions.json'):
    print(f"Attempting to load topic: {topic}") 
    questions_data = load_questions(topic)

    if questions_data:
        print(f"Successfully loaded data for topic: {topic}") 
        print(f"Data keys: {questions_data.keys()}")
        # If 'topic_data' is None or doesn't have 'topic' or 'questions' keys,
        # this will cause issues in questions.html
        if 'topic' not in questions_data or 'questions' not in questions_data:
            print("WARNING: Loaded JSON data is missing 'topic' or 'questions' key!")
            return render_template('error.html', message=f"Invalid JSON structure for '{topic}'."), 500

        return render_template('questions.html', topic_data=questions_data)
    else:
        print(f"Failed to load data for topic: {topic}")
        return render_template('error.html', message=f"only God KNOWS"), 404

@app.route('/about')
def about():
    # Placeholder for an "About" page
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

        # Create a Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    'price': price_id,
                    'quantity': 1,
                },
            ],
            mode='subscription', # Or 'payment' if it's a one-time purchase
            success_url=url_for('payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('payment_cancel', _external=True),
        )
        return jsonify({'checkout_url': checkout_session.url})
    except stripe.error.StripeError as e:
        print(f"Stripe Error: {e}")
        return render_template('error.html', message=f"An Error Occurred, but we didn't cause this"), 404
    except Exception as e:
        print(f"Server Error: {e}")
        return render_template('error.html', message=f"An Internal Server Error occurred"), 500

@app.route('/payment-success')
def payment_success():
    session_id = request.args.get('session_id')
    if session_id:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            # You can now process the successful payment, e.g., update user's subscription status in your database
            print(f"Payment successful for session: {session.id}, Customer: {session.customer_details.email}")
            return render_template('payment_status.html', status='success', session=session)
        except stripe.error.StripeError as e:
            print(f"Error retrieving Stripe session: {e}")
            return render_template('payment_status.html', status='error', message='Failed to retrieve payment details.'), 400
    return redirect(url_for('index')) # Redirect to home if no session ID

@app.route('/payment-cancel')
def payment_cancel():
    return render_template('payment_status.html', status='cancelled', message='Payment was cancelled.')

@app.route('/suggest-feature')
def suggest_feature():
    return render_template('error.html', message=f"We haven't populated this page...Stay Tuned"), 404

@app.route('/report-bug')
def report_bug():
    return render_template('error.html', message=f"We haven't populated this page...stay Tuned"), 404

if __name__ == '__main__':
    # When running directly, ensure debug mode is on for development
    # In production, use a production-ready WSGI server like Gunicorn or uWSGI
    app.run(debug=True)