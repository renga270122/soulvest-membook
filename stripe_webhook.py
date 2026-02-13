import os
import sqlite3
from flask import Flask, request, jsonify
import stripe

app = Flask(__name__)

# Set your Stripe secret key
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]  # Must be set in your environment for production

# Helper to update user to premium (by email)
def upgrade_user_to_premium(email):
    conn = sqlite3.connect("lovebook.db", check_same_thread=False)
    conn.execute("UPDATE users SET role='premium' WHERE email=?", (email,))
    conn.commit()
    conn.close()

@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    endpoint_secret = os.environ["STRIPE_WEBHOOK_SECRET"]  # Must be set in your environment for production
    event = None
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 400

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session.get('customer_email')
        if customer_email:
            upgrade_user_to_premium(customer_email)
            print(f"Upgraded {customer_email} to premium!")
    return '', 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4242)
