from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-this-secret-key-before-production"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{BASE_DIR / 'instance' / 'family_hub.db'}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "יש להתחבר כדי להמשיך"


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="user")
    must_change_password = db.Column(db.Boolean, default=True)
    is_active_flag = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def is_active(self):
        return self.is_active_flag

    @property
    def is_admin(self):
        return self.role == "admin"

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Medication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    time_of_day = db.Column(db.String(40), nullable=False, default="בוקר")
    notes = db.Column(db.String(255), default="")
    taken_today = db.Column(db.Boolean, default=False)
    user = db.relationship("User", backref="medications")


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    appointment_time = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(160), default="")
    notes = db.Column(db.String(255), default="")
    user = db.relationship("User", backref="appointments")


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_default_data():
    db.create_all()
    if not User.query.filter_by(username="ronen").first():
        admin = User(username="ronen", full_name="רונן גולדנברג", role="admin", must_change_password=True)
        admin.set_password("123456")
        db.session.add(admin)
        db.session.commit()


def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)


@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username, is_active_flag=True).first()
        if user and user.check_password(password):
            login_user(user)
            if user.must_change_password:
                flash("זוהי סיסמה ראשונית. נא להחליף סיסמה.", "warning")
                return redirect(url_for("change_password"))
            return redirect(url_for("dashboard"))
        flash("שם משתמש או סיסמה שגויים", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        if len(new_password) < 6:
            flash("הסיסמה חייבת להכיל לפחות 6 תווים", "danger")
        elif new_password != confirm_password:
            flash("הסיסמאות אינן תואמות", "danger")
        else:
            current_user.set_password(new_password)
            current_user.must_change_password = False
            db.session.commit()
            flash("הסיסמה עודכנה בהצלחה", "success")
            return redirect(url_for("dashboard"))
    return render_template("change_password.html")


@app.route("/dashboard")
@login_required
def dashboard():
    users = User.query.filter_by(is_active_flag=True).order_by(User.full_name).all() if current_user.is_admin else [current_user]
    return render_template("dashboard.html", users=users)


@app.route("/users", methods=["GET", "POST"])
@login_required
def users():
    admin_required()
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        role = request.form.get("role", "user")
        if not username or not full_name:
            flash("חובה להזין שם משתמש ושם מלא", "danger")
        elif User.query.filter_by(username=username).first():
            flash("שם המשתמש כבר קיים", "danger")
        else:
            user = User(username=username, full_name=full_name, role=role, must_change_password=True)
            user.set_password("123456")
            db.session.add(user)
            db.session.commit()
            flash("המשתמש נוסף. הסיסמה הראשונית היא 123456", "success")
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("users.html", users=all_users)


@app.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def delete_user(user_id):
    admin_required()
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("לא ניתן למחוק את המשתמש המחובר", "danger")
    else:
        user.is_active_flag = False
        db.session.commit()
        flash("המשתמש הושבת", "success")
    return redirect(url_for("users"))


@app.route("/medications/reset", methods=["POST"])
@login_required
def reset_medications():
    query = Medication.query if current_user.is_admin else Medication.query.filter_by(user_id=current_user.id)
    query.update({Medication.taken_today: False})
    db.session.commit()
    flash("כל סימוני התרופות אופסו", "success")
    return redirect(url_for("dashboard"))


if __name__ == "__main__":
    with app.app_context():
        create_default_data()
    app.run(host="127.0.0.1", port=5000, debug=True)
