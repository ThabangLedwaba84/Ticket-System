from flask import Flask, render_template, request, redirect, url_for, session
import qrcode
import os
import uuid
import random
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask import send_file
import io

app = Flask(__name__)
app.secret_key = "secretkey"

users = {}
tickets = {}

@app.route('/download/<ticket_id>')
def download_ticket(ticket_id):
    if ticket_id not in tickets:
        return "Ticket not found", 404

    ticket = tickets[ticket_id]

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Ticket Details")

    # Details
    c.setFont("Helvetica", 12)
    y = height - 100

    c.drawString(50, y, f"Name: {ticket['name']} {ticket['surname']}")
    y -= 20
    c.drawString(50, y, f"Email: {ticket['email']}")
    y -= 20
    c.drawString(50, y, f"Ticket ID: {ticket_id}")
    y -= 20
    c.drawString(50, y, f"Code: {ticket['code']}")

    if 'date_generated' in ticket:
        y -= 20
        c.drawString(50, y, f"Date Generated: {ticket['date_generated']}")

    if 'date_purchased' in ticket:
        y -= 20
        c.drawString(50, y, f"Date Purchased: {ticket['date_purchased']}")

    # QR Code Image
    qr_path = ticket['qr']
    c.drawImage(qr_path, 400, height - 200, width=120, height=120)

    c.showPage()
    c.save()

    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f"ticket_{ticket_id}.pdf",
                     mimetype='application/pdf')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        users[email] = {
            'name': request.form['name'],
            'surname': request.form['surname'],
             'email': request.form['email'],
            'password': request.form['password']
        }
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Admin login
        if email == 'admin@gmail.com' and password == 'admin':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))

        # User login
        if email in users and users[email]['password'] == password:
            session['user'] = email
            return redirect(url_for('user_dashboard'))

    return render_template('login.html')

# =========================
# ADMIN DASHBOARD
# =========================
@app.route('/admin')
def admin_dashboard():
    if 'admin' not in session:
        return redirect(url_for('login'))

    generated_count = len([t for t in tickets.values() if t.get('type') == 'admin'])
    purchased_count = len([t for t in tickets.values() if t.get('type') == 'user'])

    
    max_generated = 100
    max_purchased = 100

    # ✅ Calculate percentages
    generated_percent = (generated_count / max_generated) * 100 if max_generated else 0
    purchased_percent = (purchased_count / max_purchased) * 100 if max_purchased else 0

    return render_template(
        'admin.html',
        tickets=tickets,
        generated_count=generated_count,
        purchased_count=purchased_count,
        generated_percent=generated_percent,
        purchased_percent=purchased_percent,
        max_generated=max_generated,
        max_purchased=max_purchased
    )

@app.route('/generate', methods=['POST'])
def generate_ticket():
    if 'admin' not in session:
        return redirect(url_for('login'))

    name = request.form['name']
    surname = request.form['surname']
    email = request.form['email']

    ticket_id = str(uuid.uuid4())[:8]
    code = random.randint(1000, 9999)
    date_generated = datetime.now().strftime("%Y-%m-%d %H:%M")

    data = f"""
ADMIN GENERATED TICKET
Name: {name} {surname}
Email: {email}
Ticket ID: {ticket_id}
Code: {code}
Date Generated: {date_generated}
"""

    img = qrcode.make(data)

    if not os.path.exists('static/qrcodes'):
        os.makedirs('static/qrcodes')

    filename = f"static/qrcodes/{ticket_id}.png"
    img.save(filename)

    tickets[ticket_id] = {
     'name': name,
    'surname': surname,
    'email': email,
    'qr': filename,
    'code': code,
    'date_generated': date_generated,
    'type': 'admin',
    'used': False
    }

    return redirect(url_for('admin_dashboard'))

# =========================
# USER DASHBOARD
# =========================
@app.route('/dashboard')
def user_dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    user_email = session['user']
    user_tickets = [t for t in tickets.values() if t['email'] == user_email]

    return render_template('dashboard.html', tickets=user_tickets)

@app.route('/buy')
def buy_ticket():
    if 'user' not in session:
        return redirect('/login')

    count = int(request.args.get('count', 1))

    user = session['user']

    for _ in range(count):
        ticket_id = str(uuid.uuid4())
        code = random.randint(1000, 9999)

        qr_path = f"static/{ticket_id}.png"
        qrcode.make(str(code)).save(qr_path)

        

        tickets[ticket_id] = {
            'name': users[user]['name'],
            'surname': users[user]['surname'],
            'email': users[user].get('email', 'N/A'),
            'code': code,
            'qr': qr_path,
            'date_purchased': datetime.now().strftime("%Y-%m-%d %H:%M"),
            'used': False,
            'quantity': count   
        }

    return redirect('/dashboard')

@app.route('/use/<ticket_id>')
def mark_ticket_used(ticket_id):
    if ticket_id not in tickets:
        return "Ticket not found", 404

    if tickets[ticket_id].get('used'):
        return "Ticket already used", 400

    tickets[ticket_id]['used'] = True
    return f"Ticket {ticket_id} marked as used"

# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# =========================
# RUN APP
# =========================
if __name__ == '__main__':
    app.run(debug=True)