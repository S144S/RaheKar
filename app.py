from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# CONFIGS =====================================================================
app = Flask(__name__)
app.config["SECRET_KEY"] = "farzan"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///rehekar.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

db = SQLAlchemy(app)

# DATABASE TABLES ============================================================= 
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(120))
    lname = db.Column(db.String(120))
    phone = db.Column(db.String(120), unique=True)
    grade = db.Column(db.Integer, default=7)
    password = db.Column(db.String(200))


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# APP =========================================================================
# خانه
@app.route("/")
def home():
    return render_template('index.html', user=current_user)

# آشنایی با مشاغل مختلف
@app.route("/jobs")
def jobs():
    return render_template('jobs.html', user=current_user)

# درباره ما
@app.route("/about-us")
def about():
    return render_template('about.html', user=current_user)

# تماس با ما
@app.route("/contact")
def contact():
    return render_template('contact.html', user=current_user)

# ثبت نام
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        # گرفتن فرم
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        phone = request.form.get("phone")
        grade = request.form.get("grade")
        password = request.form.get("password")

        # چک کردن اینکه آیا کاربر قبلا ثبت نام کرده یا نه
        existing_user = Users.query.filter_by(phone=phone).first()
        if existing_user:
            flash("این شماره قبلا ثبت شده", "warning")
            redirect(url_for('register'))

        # هش کردن پسورد
        hashed_password = generate_password_hash(password)

        # ثبت در دیتابیس
        new_user = Users(
            fname=fname,
            lname=lname,
            phone=phone,
            grade=grade,
            password=hashed_password
        )
        db.session.add(new_user)
        db.session.commit()

        flash("ثبت نام با موفقیت انجام شد!", "success")
        return redirect(url_for('login'))
    return render_template("register.html")

# ورود
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        phone = request.form.get("phone")
        password = request.form.get("password")

        user = Users.query.filter_by(phone=phone).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("با موفقیت وارد شدید", "success")
            return redirect(url_for("home"))

        flash("شماره یا رمز اشتباه است", "danger")

    return render_template("login.html")

# خروج
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# صفحه بعد از وارد شدن
@app.route('/dashboard')
@login_required
def dashboard():
    context = {
        "user": current_user,
        "is_take_exam": False
    }
    return render_template("dashboard.html", context=context)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
