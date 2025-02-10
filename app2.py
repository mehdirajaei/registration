from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "super_secret_key"

# اطلاعات ایمیل برای ارسال لینک بازیابی
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_ADDRESS = "your_email@gmail.com"  # جایگزین کنید
EMAIL_PASSWORD = "your_email_password"  # جایگزین کنید

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY, 
                    first_name TEXT, 
                    last_name TEXT, 
                    username TEXT UNIQUE, 
                    password TEXT, 
                    reset_token TEXT)''')
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        username = request.form["username"]
        password = request.form["password"]
        hashed_password = generate_password_hash(password)

        try:
            conn = sqlite3.connect("users.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (first_name, last_name, username, password) VALUES (?, ?, ?, ?)", 
                      (first_name, last_name, username, hashed_password))
            conn.commit()
            conn.close()
            flash("ثبت‌نام موفقیت‌آمیز بود! لطفاً وارد شوید.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("این ایمیل قبلاً ثبت شده است.", "danger")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[0], password):
            session["username"] = username
            flash("ورود موفقیت‌آمیز!", "success")
            return redirect(url_for("dashboard"))

        flash("نام کاربری یا رمز عبور اشتباه است.", "danger")

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if "username" in session:
        return render_template("dashboard.html")
    flash("لطفاً ابتدا وارد شوید.", "warning")
    return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.pop("username", None)
    flash("خروج موفقیت‌آمیز!", "info")
    return redirect(url_for("login"))

@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if request.method == "POST":
        username = request.form["username"]
        token = secrets.token_hex(16)

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("UPDATE users SET reset_token = ? WHERE username = ?", (token, username))
        conn.commit()
        conn.close()

        reset_link = f"http://127.0.0.1:5000/change_password?token={token}"
        send_reset_email(username, reset_link)

        flash("لینک بازیابی رمز عبور به ایمیل شما ارسال شد.", "info")
        return redirect(url_for("login"))

    return render_template("reset_password.html")

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    token = request.args.get("token")

    if request.method == "POST":
        new_password = request.form["password"]
        hashed_password = generate_password_hash(new_password)

        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("UPDATE users SET password = ?, reset_token = NULL WHERE reset_token = ?", (hashed_password, token))
        conn.commit()
        conn.close()

        flash("رمز عبور با موفقیت تغییر کرد. لطفاً وارد شوید.", "success")
        return redirect(url_for("login"))

    return render_template("change_password.html", token=token)

def send_reset_email(to_email, reset_link):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email
    msg["Subject"] = "بازیابی رمز عبور"

    body = f"""
    <html>
    <body>
        <h2>درخواست تغییر رمز عبور</h2>
        <p>کاربر گرامی،</p>
        <p>برای تغییر رمز عبور خود روی لینک زیر کلیک کنید:</p>
        <a href="{reset_link}" style="background-color:blue;color:white;padding:10px 20px;text-decoration:none;">بازیابی رمز عبور</a>
        <p>اگر این درخواست از طرف شما نیست، این ایمیل را نادیده بگیرید.</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(body, "html"))

    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.sendmail(EMAIL_ADDRESS, to_email, msg.as_string())
        server.quit()
    except Exception as e:
        print("خطا در ارسال ایمیل:", e)

if __name__ == "__main__":
    from waitress import serve  # More stable in production
    serve(app2, host="0.0.0.0", port=8080)

