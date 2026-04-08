import os

CLIENT_ID = os.getenv("AfE7Dk_XHIdYcgq7Sy2rwmzQa9mgrj33TmRPh2FOtsAOF5557OmRM7A_OaGbYHT7xMegjPmkPbLfQyO1")
SECRET = os.getenv("EAVPEctw_KDxzZb9UeVdTkZ1W1JsHWg3v3Bh9qURa8zw9A2aayJ7xUz7RzrrjYcja-qgBMvwL282gRTq")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")

    SQLALCHEMY_DATABASE_URI = 'sqlite:///payments.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # EMAIL
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv("EMAIL_USER")
    MAIL_PASSWORD = os.getenv("EMAIL_PASS")

    # PAYPAL
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
    PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")

    PAYPAL_MODE = "sandbox"  # change to "live"