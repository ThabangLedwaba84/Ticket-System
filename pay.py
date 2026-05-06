from flask import Flask, request, jsonify, render_template
import requests
import uuid
import random

app = Flask(__name__)

# 🔴 IMPORTANT: Replace with your LIVE credentials
PAYPAL_CLIENT_ID = "AfE7Dk_XHIdYcgq7Sy2rwmzQa9mgrj33TmRPh2FOtsAOF5557OmRM7A_OaGbYHT7xMegjPmkPbLfQyO1"
PAYPAL_SECRET = "EAVPEctw_KDxzZb9UeVdTkZ1W1JsHWg3v3Bh9qURa8zw9A2aayJ7xUz7RzrrjYcja-qgBMvwL282gRTq"

BASE_URL = "https://api-m.paypal.com"  # LIVE (real money)

tickets = {}

# ✅ Get PayPal Access Token
def get_paypal_token():
    url = f"{BASE_URL}/v1/oauth2/token"

    response = requests.post(
        url,
        headers={"Accept": "application/json"},
        data={"grant_type": "client_credentials"},
        auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET)
    )

    data = response.json()

    # 🔥 DEBUG PRINT (VERY IMPORTANT)
    print("PayPal Token Response:", data)

    if "access_token" not in data:
        raise Exception(f"PayPal Error: {data}")

    return data["access_token"]
# ✅ Create Order
@app.route('/create-order', methods=['POST'])
def create_order():
    data = request.json
    amount = data.get("amount", "150.00")

    token = get_paypal_token()

    url = f"{BASE_URL}/v2/checkout/orders"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    payload = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": "ZAR",
                "value": amount
            }
        }]
    }

    response = requests.post(url, json=payload, headers=headers)

    # 🔥 THIS IS THE FIX
    response_data = response.json()

    return jsonify({
        "id": response_data.get("id")
    })

# ✅ Capture Payment
@app.route('/capture-order', methods=['POST'])
def capture_order():
    data = request.json
    order_id = data.get("orderID")
    email = data.get("email")

    token = get_paypal_token()

    url = f"{BASE_URL}/v2/checkout/orders/{order_id}/capture"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }

    response = requests.post(url, headers=headers)
    result = response.json()

    # ✅ Check payment success
    if result.get("status") == "COMPLETED":

        ticket_code = "TICKET-" + str(random.randint(100000, 999999))

        tickets[ticket_code] = {
            "email": email,
            "order_id": order_id
        }

        return jsonify({
            "status": "success",
            "ticket_code": ticket_code
        })

    return jsonify({
        "status": "failed",
        "details": result
    })


# ✅ Page routes
@app.route('/')
def home():
    return render_template("pay.html")  # your HTML file


@app.route('/tickets')
def tickets_page():
    return f"<h2>Tickets:</h2>{tickets}"


# ✅ Run app
if __name__ == '__main__':
    app.run(debug=True)
