### app.py

from flask import Flask, render_template, request
import datetime
import openai
import re
import whois
import validators
import tldextract
import requests

app = Flask(__name__)
openai.api_key = "sk-xxxx"  # Replace with your actual OpenAI key

def analyze_text(text):
    prompt = f"Analyze this message for emotional manipulation, urgency, threats, or scam signs:\n{text}\nGive a risk score (0 to 10) and reasoning."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/scan', methods=['POST'])
def scan():
    message = request.form['message']
    result = analyze_text(message)

    # Extract score from response
    score_match = re.search(r'(\d+)/10', result)
    risk_score = int(score_match.group(1)) if score_match else 0

    with open("log.txt", "a") as f:
        f.write(f"[{datetime.datetime.now()}] Scan: {message}\nResult: {result}\n\n")

    return render_template("result.html", message=message, result=result, risk_score=risk_score)

@app.route('/scan-link', methods=['GET', 'POST'])
def scan_link():
    if request.method == 'POST':
        url = request.form['url']

        if not validators.url(url):
            return render_template('result.html', message=url, result="❌ Invalid URL", risk_score=0)

        try:
            response = requests.get(url, timeout=5, allow_redirects=True)
            final_url = response.url

            ext = tldextract.extract(final_url)
            domain = f"{ext.domain}.{ext.suffix}"

            w = whois.whois(domain)
            creation_date = w.creation_date

            # ✅ FIXED: closed string properly using parentheses
            result = (
                f"✅ Final URL: {final_url}\n"
                f"🔍 Domain: {domain}\n"
                f"🕒 Domain Created: {creation_date}"
            )

        except Exception as e:
            result = f"⚠️ Error scanning URL: {e}"

        return render_template("result.html", message=url, result=result, risk_score=0)

    return render_template("scan_link.html")


if __name__ == '__main__':
    app.run(debug=True)

