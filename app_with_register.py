
from flask import Flask, render_template, request, redirect, url_for, session
import cohere
import smtplib
from email.message import EmailMessage
from datetime import datetime
import csv
import os

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallbacksecret")

# Load secrets from environment
co = cohere.Client(os.getenv("hcMMMoNhUG6TygWQf5kTOHeuEbOxtrCWE0pUw0kp"))
EMAIL_ADDRESS = os.getenv("blackvolk23@gmail.com")
EMAIL_PASSWORD = os.getenv("slws fcdi zyul rxwu")

LOG_FILE = "scam_log.csv"
USER_FILE = "users.csv"
family_emails = []

# Send alert email to saved family contacts
def send_alert_email(to_emails, scanned_text, ai_result):
    msg = EmailMessage()
    msg['Subject'] = "🚨 ZeroTrust Scam Alert"
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = ", ".join(to_emails)
    msg.set_content(f"""
Your family member scanned a suspicious message:

📩 Message:
{scanned_text}

🧠 AI says:
{ai_result}

🛡️ Stay safe,
ZeroTrust AI Shield
""")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
    except Exception as e:
        print(f"[!] Failed to send alert email: {str(e)}")

# Log scan results
def log_scan(message, result, risk_level):
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Timestamp", "Message", "AI_Result", "Risk_Level"])
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message, result, risk_level])

# Check login credentials
def check_user(username, password):
    if os.path.exists(USER_FILE):
        with open(USER_FILE, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0] == username and row[1] == password:
                    return True
    return False

# Register new user
def register_user(username, password):
    mode = 'a' if os.path.exists(USER_FILE) else 'w'
    with open(USER_FILE, mode=mode, newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([username, password])

# Routes

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        if check_user(user, pwd):
            session['user'] = user
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user = request.form['username']
        pwd = request.form['password']
        register_user(user, pwd)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    global family_emails
    if request.method == 'POST':
        email = request.form.get('email')
        if email and email not in family_emails:
            family_emails.append(email)
    return render_template('index.html', emails=family_emails)

@app.route('/remove_email/<email>')
def remove_email(email):
    if 'user' not in session:
        return redirect(url_for('login'))
    global family_emails
    email = email.strip()
    if email in family_emails:
        family_emails.remove(email)
    return redirect(url_for('index'))

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'user' not in session:
        return redirect(url_for('login'))
    user_input = request.form['user_input']
    risk_level = "Safe"
    try:
        response = co.generate(
            model='command',
            prompt=f"Is the following message or link a scam? Explain in detail:\n{user_input}",
            max_tokens=100,
            temperature=0.5
        )
        result = response.generations[0].text.strip()
        if any(word in result.lower() for word in ["scam", "suspicious", "phishing"]):
            risk_level = "Scam"
            if family_emails:
                send_alert_email(family_emails, user_input, result)
        log_scan(user_input, result, risk_level)
    except Exception as e:
        result = f"Error: {str(e)}"
        log_scan(user_input, result, "Error")
    return render_template('result.html', user_input=user_input, result=result)

@app.route('/history')
def history():
    if 'user' not in session:
        return redirect(url_for('login'))
    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            logs = list(reader)
    return render_template('history.html', logs=logs)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
