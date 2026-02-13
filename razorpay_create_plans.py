# Razorpay Subscription Automation Script
# This script helps you create subscription plans in Razorpay using their API.
# Fill in your Razorpay API key and secret below.

import razorpay

RAZORPAY_API_KEY = "YOUR_API_KEY"
RAZORPAY_API_SECRET = "YOUR_API_SECRET"

client = razorpay.Client(auth=(RAZORPAY_API_KEY, RAZORPAY_API_SECRET))

# Example: Create a monthly subscription plan
monthly_plan = client.plan.create({
    "period": "monthly",
    "interval": 1,
    "item": {
        "name": "LoveBook Premium Monthly",
        "amount": 9900,  # Amount in paise (₹99.00)
        "currency": "INR",
        "description": "Monthly subscription for LoveBook Premium"
    }
})
print("Monthly Plan Created:", monthly_plan)

# Example: Create a yearly subscription plan
yearly_plan = client.plan.create({
    "period": "yearly",
    "interval": 1,
    "item": {
        "name": "LoveBook Premium Yearly",
        "amount": 99900,  # Amount in paise (₹999.00)
        "currency": "INR",
        "description": "Yearly subscription for LoveBook Premium"
    }
})
print("Yearly Plan Created:", yearly_plan)

# Save the plan IDs for use in your Streamlit app.
