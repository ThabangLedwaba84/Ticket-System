from flask import Flask, render_template, request, redirect, session, jsonify
from config import Config
from models import db, User, Payment, Ticket
import uuid, os, requests, base64, qrcode
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
mail = Mail(app)

with app.app_context():
    db.create_all()

# =========================
# AUTH
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        user = User(email=email, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form['email']).first()

        if user and check_password_hash(user.password, request.form['password']):
            session['user_id'] = user.id
            return redirect("/dashboard")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# =========================
# DASHBOARD
# =========================
@app.route("/dashboard")
def dashboard():
    if 'user_id' not in session:
        return redirect("/login")

    tickets = Ticket.query.filter_by(user_id=session['user_id']).all()
    return render_template("dashboard.html", tickets=tickets)

# =========================
# PAYPAL
# =========================
def get_base_url():
    if app.config["PAYPAL_MODE"] == "live":
        return "https://api-m.paypal.com"
    return "https://api-m.sandbox.paypal.com"

def get_token():
    auth = base64.b64encode(
        f"{app.config['PAYPAL_CLIENT_ID']}:{app.config['PAYPAL_SECRET']}".encode()
    ).decode()

    res = requests.post(
        f"{get_base_url()}/v1/oauth2/token",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Type": "application/x-www-form-urlencoded"
        },
        data={"grant_type": "client_credentials"}
    )

    return res.json().get("access_token")

@app.route("/create-order", methods=["POST"])
def create_order():
    token = get_token()

    res = requests.post(
        f"{get_base_url()}/v2/checkout/orders",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {"currency_code": "ZAR", "value": "10.00"}
            }]
        }
    )

    return jsonify(res.json())

@app.route("/capture-order", methods=["POST"])
def capture():
    token = get_token()
    order_id = request.json["orderID"]

    res = requests.post(
        f"{get_base_url()}/v2/checkout/orders/{order_id}/capture",
        headers={"Authorization": f"Bearer {token}"}
    )

    data = res.json()

    if data.get("status") == "COMPLETED":
        code = str(uuid.uuid4())

        path = f"static/qrcodes/{code}.png"
        os.makedirs("static/qrcodes", exist_ok=True)
        qrcode.make(code).save(path)

        ticket = Ticket(ticket_code=code, user_id=session['user_id'])
        db.session.add(ticket)
        db.session.commit()

        return jsonify({"ticket": code})

    return jsonify({"error": "failed"})

# =========================
# QR VALIDATION PAGE
# =========================
@app.route("/scan")
def scan():
    return render_template("scan.html")

@app.route("/validate/<code>")
def validate(code):
    ticket = Ticket.query.filter_by(ticket_code=code).first()

    if not ticket:
        return "Invalid"

    if ticket.used:
        return "Already used"

    ticket.used = True
    db.session.commit()
    return "Access Granted"

# =========================
# ADMIN DASHBOARD
# =========================
@app.route("/admin")
def admin():
    users = User.query.count()
    tickets = Ticket.query.count()
    used = Ticket.query.filter_by(used=True).count()

    return render_template("admin.html",
                           users=users,
                           tickets=tickets,
                           used=used)

# =========================
# RUN
# =========================
import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
