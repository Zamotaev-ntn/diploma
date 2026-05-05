from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from config import Config
from forms import RegisterForm, LoginForm
from models import User, Test, Question, UserResult
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


@app.route("/admin/tests")
@admin_required
def admin_tests():
    tests = Test.query.order_by(Test.created_at.desc()).all()
    return render_template("admin_tests.html", tests=tests)


@app.route("/admin/tests/create", methods=["GET", "POST"])
@admin_required
def admin_tests_create():
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        if not title:
            flash("Название теста обязательно", "danger")
            return render_template("admin_test_form.html")

        test = Test(title=title, description=description, author_id=current_user.id)
        db.session.add(test)
        db.session.commit()
        flash("Тест создан", "success")
        return redirect(url_for("admin_tests"))
    return render_template("admin_test_form.html")


@app.route("/admin/tests/<int:test_id>/delete", methods=["POST", "GET"])
@admin_required
def admin_tests_delete(test_id):
    test = Test.query.get_or_404(test_id)
    Question.query.filter_by(test_id=test.id).delete()
    UserResult.query.filter_by(test_id=test.id).delete()
    db.session.delete(test)
    db.session.commit()
    flash("Тест и связанные данные удалены", "success")
    return redirect(url_for("admin_tests"))


@app.route("/admin/tests/<int:test_id>/questions")
@admin_required
def admin_test_questions(test_id):
    test = Test.query.get_or_404(test_id)
    questions = Question.query.filter_by(test_id=test.id).all()
    return render_template("admin_questions.html", test=test, questions=questions)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True, host="127.0.0.1", port=5001)