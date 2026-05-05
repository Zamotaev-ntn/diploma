from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from config import Config
from forms import RegisterForm, LoginForm
from models import User
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from decorators import admin_required

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(email=form.email.data).first()

        if existing_user:
            flash("Email уже зарегистрирован")
        else:
            user = User(
                email=form.email.data,
                password_hash=generate_password_hash(form.password.data)
            )

            db.session.add(user)
            db.session.commit()

            flash("Регистрация успешна")

        return redirect(url_for("register"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("Вы вошли", "success")
            next_page = request.args.get("next")
            return redirect(next_page) if next_page else redirect(url_for("dashboard"))
        else:
            flash("Неверный email или пароль", "danger")
    
    return render_template("login.html", form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user)


@app.route("/admin")
@admin_required
def admin():
    return render_template("admin.html", user=current_user)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True, host="127.0.0.1", port=5001)