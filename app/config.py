# question_app/config.py
import os
# Flask secret key for security (e.g., sessions, flash messages)
# IMPORTANT: In a real application, retrieve this from an environment variable
# export SECRET_KEY='your_very_secret_key_here' in your shell or .env file
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_insecure_default_key_replace_me'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # DEBUG is True only if FLASK_ENV is 'development'
    DEBUG = (FLASK_ENV == 'development')
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY') or 'sk_test_YOUR_STRIPE_SECRET_KEY'
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY') or 'pk_test_YOUR_STRIPE_PUBLISHABLE_KEY'
    FLASK_APP="app/app.py"
    TESTING = False
    STRIPE_PRICE_ID_PRO = os.environ.get('STRIPE_PRICE_ID_PRO') or 'price_12345' # Example Price ID for Pro plan
    STRIPE_PRICE_ID_ENTERPRISE_CONTACT = os.environ.get('STRIPE_PRICE_ID_ENTERPRISE_CONTACT') or 'price_67890' # Example Price ID for Enterprise (if you want a specific price for contact)
    # For local development, this default is fine, but NEVER use it in production!