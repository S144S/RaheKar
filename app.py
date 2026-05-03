from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import json

from ai_assitant import get_job_info, get_job_path, ask_job_ai, job_recommendation

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


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    job_title = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text)
    roadmap = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ChatUsage(db.Model):
    __tablename__ = "chat_usage"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    count = db.Column(db.Integer, default=0)


def check_and_increment_chat(user_id, limit=3):
    today = date.today()
    usage = ChatUsage.query.filter_by(user_id=user_id, date=today).first()

    if not usage:
        usage = ChatUsage(user_id=user_id, date=today, count=0)
        db.session.add(usage)

    if usage.count >= limit:
        return False  # اجازه پرسش ندارد

    usage.count += 1
    db.session.commit()
    return True

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

# صفحه آزمون
@app.route('/exam', methods=["GET", "POST"])
@login_required
def exam():
    questions = {
        "preferred_activity": {
            "q": "1. کدام فعالیت برای شما جذاب‌تر است؟",
            "choices": ["حل مسائل فکری", "همکاری با دیگران", "ساختن چیزهای جدید", "هدایت تیم"]
        },

        "favorite_subject": {
            "q": "2. به کدام درس علاقه بیشتری دارید؟",
            "choices": ["ریاضی و فیزیک", "علوم تجربی و زیست شناسی", "ادبیات و علوم انسانی", "ورزش و هنر"]
        },

        "least_favorite_subject": {
            "q": "3. از کدام درس اصلا خوشتان نمی‌آید؟",
            "choices": ["ریاضی و فیزیک", "علوم تجربی و زیست شناسی", "ادبیات و علوم انسانی", "ورزش و هنر"]
        },

        "problem_reaction": {
            "q": "4. در زمان بروز مشکل، اولین واکنش شما چیست؟",
            "choices": ["تحلیل منطقی موضوع", "کمک گرفتن از دیگران", "آزمایش راه‌حل‌های مختلف", "مدیریت و سازمان‌دهی شرایط"]
        },

        "preferred_work_environment": {
            "q": "5. کدام نوع محیط کاری را ترجیح می‌دهید؟",
            "choices": ["آرام و تحلیل‌محور", "تعامل‌محور و اجتماعی", "متغیر و خلاقانه", "ساختاریافته و مدیریتی"]
        },

        "easiest_skill": {
            "q": "6. کدام مهارت برای شما راحت‌تر است؟",
            "choices": ["تفکر منطقی", "مهارت‌های ارتباطی", "ایده‌پردازی", "برنامه‌ریزی و تصمیم‌گیری"]
        },

        "favorite_activity": {
            "q": "7. از انجام کدام فعالیت بیشتر لذت می‌برید؟",
            "choices": ["کار با اعداد و داده‌ها", "کمک به افراد", "خلق کارهای هنری", "هدایت پروژه‌ها"]
        },

        "new_skill_choice": {
            "q": "8. اگر فرصت یادگیری یک مهارت جدید داشته باشید، کدام را انتخاب می‌کنید؟",
            "choices": ["تحلیل داده", "آناتومی بدن", "طراحی و هنر", "رهبری و مدیریت"]
        },

        "self_description": {
            "q": "9. کدام جمله بیشتر شما را توصیف می‌کند؟",
            "choices": ["من منطقی و دقیق هستم", "من اجتماعی و همدل هستم", "من خلاق و نوآور هستم", "من منظم و مسئولیت‌پذیر هستم"]
        },

        "team_role": {
            "q": "10. در یک گروه، معمولاً چه نقشی را برعهده می‌گیرید؟",
            "choices": ["تحلیل‌گر", "هماهنگ‌کننده", "ایده‌پرداز", "رهبر"]
        },

        "favorite_project_type": {
            "q": "11. از کدام نوع پروژه‌ها بیشتر لذت می‌برید؟",
            "choices": ["پروژه‌های پژوهشی", "پروژه‌های اجتماعی", "پروژه‌های هنری", "پروژه‌های سازمانی"]
        },

        "motivation_source": {
            "q": "12. چه چیزی شما را بیشتر انگیزه می‌دهد؟",
            "choices": ["یادگیری و کشف", "اثرگذاری بر مردم", "خلق چیزهای جدید", "رسیدن به اهداف مشخص"]
        },

        "team_priority": {
            "q": "13. در کار گروهی، مهم‌ترین ویژگی برای شما چیست؟",
            "choices": ["منطق و دقت عملکرد", "هماهنگی و تعامل", "خلاقیت و تنوع", "سازمان‌دهی و رهبری"]
        },

        "strength_point": {
            "q": "14. کدام یک از این موارد نقطه قوت شماست؟",
            "choices": ["تفکر تحلیلی", "درک احساسات دیگران", "تصور و خلاقیت", "برنامه‌ریزی و اجرا"]
        },

        "job_priority": {
            "q": "15. هنگام انتخاب شغل، چه چیزی برای شما مهم‌تر است؟",
            "choices": ["ثبات و امنیت شغلی", "معنابخشی و کمک به دیگران", "تنوع و آزادی عمل", "پیشرفت و مدیریت"]
        },

        "work_style": {
            "q": "16. کدام سبک کاری به شما نزدیک‌تر است؟",
            "choices": ["تحقیق‌محور", "مردم‌محور", "خلاقانه", "نتیجه‌محور"]
        },

        "preferred_field": {
            "q": "17. کدام حوزه برای شما جذاب‌تر است؟",
            "choices": ["مهندسی و فناوری", "پزشکی و روان شناسی", "هنر و طراحی", "کسب‌وکار و مدیریت"]
        },

        "new_task_reaction": {
            "q": "18. در مواجهه با کارهای جدید، چه رفتاری دارید؟",
            "choices": ["اول فکر می‌کنم و تحلیل می‌کنم", "از دیگران راهنمایی می‌گیرم", "با آزمون و خطا پیش می‌روم", "برنامه‌ریزی می‌کنم و قدم‌به‌قدم جلو می‌روم"]
        },

        "success_preference": {
            "q": "19. کدام نوع موفقیت برای شما لذت‌بخش‌تر است؟",
            "choices": ["حل یک مسئله پیچیده", "کمک به رشد دیگران", "خلق یک کار ارزشمند", "رسیدن به یک هدف بزرگ"]
        },

        "final_choice": {
            "q": "20. اگر مجبور باشید بین این موارد یکی را انتخاب کنید، کدام را ترجیح می‌دهید؟",
            "choices": ["دقت", "همدلی", "نوآوری", "رهبری"]
        }
    }
    context = {
        "user": current_user,
        "questions": questions
    }
    if request.method == "POST":
        answers = {}
        for key in questions.keys():
            answers[key] = request.form.get(key)
        print(answers)
        print('-'*80)
        job = job_recommendation(answers)
        print(job)
        print('@'*80)
        try:
            new_job = UsersJob(
                user_id=current_user.id,
                job_title=job,
                deducted_from="exam"
            )

            db.session.add(new_job)
            db.session.commit()

            flash("شغل آینده شما با موفقیت ارزیابی شد.", "success")
            return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash("درحال حاضر سرویس ارزیابی شعل فعال نیست!", "danger")
    return render_template('exam.html', context=context)

# صفحه توضیح شغل
@app.route('/description')
@login_required
def description():
    user_jobs = current_user.user_job
    job_title = user_jobs[0].job_title if user_jobs else None
    if not job_title:
        flash("ابتدا باید شغل آینده شما مشخص شود!", "warning")
        return redirect(url_for("dashboard"))
    job = Job.query.filter_by(job_title=job_title).first()
    if not job or not job.description:
        info = get_job_info(job_title)
        if not job:
            job = Job(job_title=job_title, description=info)
            db.session.add(job)
        else:
            job.description = info
        db.session.commit()
    else:
        info = job.description
    context = {
        "user": current_user,
        "job_title": job_title,
        "job_info": info
    }
    return render_template("description.html", context=context)

# صفحه مسیر شغلی
@app.route('/roadmap')
@login_required
def roadmap():
    user_jobs = current_user.user_job
    job_title = user_jobs[0].job_title if user_jobs else None
    
    if not job_title:
        flash("ابتدا باید شغل آینده شما مشخص شود!", "warning")
        return redirect(url_for("dashboard"))

    job = Job.query.filter_by(job_title=job_title).first()

    # اگر هنوز roadmap وجود ندارد → از هوش مصنوعی بگیر
    if not job or not job.roadmap:
        info = get_job_path(job_title)   # احتمال زیاد dict برمی‌گرداند

        # اگر خروجی رشته بود → تبدیل کن
        if isinstance(info, str):
            info = json.loads(info)

        if not job:
            job = Job(job_title=job_title, roadmap=info)
            db.session.add(job)
        else:
            job.roadmap = info

        db.session.commit()

    else:
        info = job.roadmap   # اینجا dict داریم، درست است

    context = {
        "user": current_user,
        "job_title": job_title,
        "roadmap": info     # به نام صحیح بفرست
    }
    print(info)
    return render_template("roadmap.html", context=context)


@app.route("/chatbot", methods=["GET", "POST"])
@login_required
def chatbot():
    user_jobs = current_user.user_job
    job_title = user_jobs[0].job_title if user_jobs else None

    if not job_title:
        flash("ابتدا باید شغل آینده شما مشخص شود.", "warning")
        return redirect(url_for("dashboard"))

    answer = None

    if request.method == "POST":
        question = request.form.get("question")

        allowed = check_and_increment_chat(current_user.id)

        if not allowed:
            flash("شما امروز به سقف ۳ سؤال رسیدید!", "danger")
        else:
            answer = ask_job_ai(job_title, question)
    context = {
        "user": current_user,
        "job_title": job_title,
        "answer": answer  
    }
    return render_template("chatbot.html", context=context)

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
