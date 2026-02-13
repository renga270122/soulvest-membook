import os
import razorpay
from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# Set your Razorpay API keys (use environment variables for production)
RAZORPAY_KEY_ID = os.environ["RAZORPAY_KEY_ID"]
RAZORPAY_KEY_SECRET = os.environ["RAZORPAY_KEY_SECRET"]
razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

# Helper to update user to premium (by email)
def upgrade_user_to_premium(email):
    conn = sqlite3.connect("lovebook.db", check_same_thread=False)
    conn.execute("UPDATE users SET role='premium' WHERE email=?", (email,))
    conn.commit()
    conn.close()

@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():
    payload = request.json
    # Validate webhook signature (recommended)
    # signature = request.headers.get('X-Razorpay-Signature')
    # Use razorpay_client.utility.verify_webhook_signature() if needed
    if payload and payload.get('event') == 'payment.captured':
        # You should store mapping of order_id/payment_id to user email when creating the order
        # For demo, assume email is sent in notes
        email = payload['payload']['payment']['entity']['notes'].get('email')
        if email:
            upgrade_user_to_premium(email)
            print(f"Upgraded {email} to premium!")
    return '', 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4243)
