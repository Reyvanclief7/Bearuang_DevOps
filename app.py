from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import os
from datetime import datetime

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config.from_object(Config)
db = SQLAlchemy(app)
app.secret_key = app.config['SECRET_KEY']


# ------------------------------
# Model User
# ------------------------------
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(200), unique=True, nullable=False)
    phone = db.Column(db.String(50))
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ------------------------------
# ROUTES
# ------------------------------

@app.route("/")
def index():
    # jika sudah login, langsung ke home
    if "user_id" in session:
        return redirect(url_for("home"))
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip().lower()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")

    if not username or not email or not password:
        flash("Lengkapi semua field yang wajib.", "error")
        return redirect(url_for("index"))

    # Cek apakah email sudah terdaftar
    existing = User.query.filter_by(email=email).first()
    if existing:
        flash("Email sudah terdaftar. Silakan login atau gunakan email lain.", "error")
        return redirect(url_for("index"))

    # Simpan user baru
    user = User(username=username, email=email, phone=phone)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    flash("Registrasi berhasil. Silakan login.", "success")
    return redirect(url_for("index"))


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("login_email", "").strip().lower()
    password = request.form.get("login_password", "")

    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        # Simpan session login
        session["user_id"] = user.id
        session["username"] = user.username

        flash(f"Selamat datang, {user.username}!", "success")
        return redirect(url_for("home"))
    else:
        flash("Email atau password salah.", "error")
        return redirect(url_for("index"))


@app.route("/home")
def home():
    if "user_id" not in session:
        flash("Silakan login terlebih dahulu.", "error")
        return redirect(url_for("index"))

    username = session.get("username")
    return render_template("home.html", username=username)


@app.route("/logout")
def logout():
    session.clear()
    flash("Anda telah logout.", "success")
    return redirect(url_for("index"))


# ------------------------------
# CLI Helper
# ------------------------------
@app.cli.command("create-db")
def create_db():
    db.create_all()
    print("Tables created.")


# ------------------------------
# Jalankan Aplikasi
# ------------------------------
if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    with app.app_context():
        db.create_all()
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", 5000)), debug=debug)
