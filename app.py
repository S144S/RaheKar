from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(120))
    lname = db.Column(db.String(120))
    phone = db.Column(db.String(120), unique=True)
    grade = db.Column(db.Integer, default=7)
    password = db.Column(db.String(200))

class ConsultationRequest(db.Model):
    __tablename__ = "consultation_requests"

    id = db.Column(db.Integer, primary_key=True)

    # ✅ ارتباط با یوزر
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # ✅ اطلاعات درخواست
    phone = db.Column(db.String(120), nullable=False)
    requested_date = db.Column(db.Date, nullable=False)
    requested_time = db.Column(db.Time, nullable=False)
    description = db.Column(db.Text)

    # ✅ وضعیت درخواست
    status = db.Column(db.String(50), default="pending")  
    # pending | approved | rejected | done

    # ✅ تاریخ ثبت
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ رابطه برگشتی
    user = db.relationship("Users", backref="consult_requests")


class UsersJob(db.Model):
    __tablename__ = "users_job"

    id = db.Column(db.Integer, primary_key=True)

    # ✅ ارتباط با یوزر
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    job_title = db.Column(db.String(120), nullable=False)

    deducted_from = db.Column(db.String(50), default="user")  
    # user | exam

    # ✅ تاریخ ثبت
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ✅ رابطه برگشتی
    user = db.relationship("Users", backref="user_job")


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

# آشنایی با شغل علم داده
@app.route("/job-datascience")
def job_datascience():
    return render_template('job-Datascience.html', user=current_user)

# آشنایی با شغل طراحی UI/UX
@app.route("/job-uiux")
def job_uiux():
    return render_template('job-uiux.html', user=current_user)

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
            return redirect(url_for("dashboard"))

        flash("شماره یا رمز اشتباه است", "danger")

    return render_template("login.html")

# خروج
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# صفحه داشبورد
@app.route('/dashboard')
@login_required
def dashboard():
    user_jobs = current_user.user_job
    context = {
        "user": current_user,
        "job_title": user_jobs[0].job_title if user_jobs else None,
        "is_take_exam": False
    }
    print(context)
    return render_template("dashboard.html", context=context)

# صفحه درخواست مشاوره
@app.route('/consultant', methods=["GET", "POST"])
@login_required
def consultant():
    if request.method == "POST":
        try:
            new_request = ConsultationRequest(
                user_id=current_user.id,
                phone=request.form.get("phone"),
                requested_date=datetime.strptime(request.form.get("date"), "%Y-%m-%d").date(),
                requested_time=datetime.strptime(request.form.get("time"), "%H:%M").time(),
                description=request.form.get("description")
            )

            db.session.add(new_request)
            db.session.commit()

            flash("درخواست شما ثبت شد بزودی با شما تماس میگیریم.", "success")
        except Exception as e:
            print(e)
            flash("درحال حاضر سرویس درخواست مشاوره فعال نیست!", "danger")
        return redirect(url_for("dashboard"))

    existing_request = ConsultationRequest.query.filter(
        ConsultationRequest.user_id == current_user.id,
        ConsultationRequest.status.in_(["pending", "approved"])
    ).first()
    context = {
        "user": current_user,
        "form_disabled": existing_request is not None
    }

    return render_template("consultant.html", context=context)


@app.route('/chosen-job', methods=['POST'])
@login_required
def chosen_job():
    job = request.form.get('future_job')
    try:
        new_job = UsersJob(
            user_id=current_user.id,
            job_title=job,
            deducted_from="user"
        )

        db.session.add(new_job)
        db.session.commit()

        flash("شغل آینده شما با موفقیت دریافت شد.", "success")
    except Exception as e:
        print(e)
        flash("درحال حاضر سرویس انتخاب شعل فعال نیست!", "danger")

    return redirect(url_for('dashboard'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
