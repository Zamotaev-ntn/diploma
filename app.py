from flask import Flask, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from config import Config
from forms import RegisterForm, LoginForm
from models import User, Test, Question, UserResult
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from decorators import admin_required
from sqlalchemy import func
import json

app = Flask(__name__)
app.config.from_object(Config)

@app.template_filter('fromjson')
def fromjson_filter(s):
    if s is None:
        return []
    return json.loads(s)

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


@app.route("/admin/stats")
@admin_required
def admin_stats():
    total_users = User.query.count()
    total_tests = Test.query.count()
    total_attempts = UserResult.query.count()
    average_scores = db.session.query(Test.id, Test.title, func.avg(UserResult.score)).join(UserResult, Test.id == UserResult.test_id).group_by(Test.id).all()
    daily_attempts = db.session.query(func.date(UserResult.completed_at), func.count()).group_by(func.date(UserResult.completed_at)).all()
    daily_data = [[date.isoformat(), count] for date, count in daily_attempts]
    
    return render_template("admin_stats.html", 
                          total_users=total_users, 
                          total_tests=total_tests, 
                          total_attempts=total_attempts,
                          average_scores=average_scores,
                          daily_data=daily_data)


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


@app.route("/admin/tests/<int:test_id>/questions/create", methods=["GET", "POST"])
@admin_required
def admin_question_create(test_id):
    test = Test.query.get_or_404(test_id)
    if request.method == "POST":
        question_text = request.form.get("question_text")
        question_type = request.form.get("question_type")
        options_text = request.form.get("options_text", "")
        
        if not question_text or not question_type:
            flash("Нехватает текста или типа вопроса", "danger")
            return render_template("admin_question_form.html", test=test, question=None, options_text='')
        
        options = None
        if question_type in [Question.TYPE_SINGLE, Question.TYPE_MULTIPLE]:
            if not options_text.strip():
                flash("Для этого типа ребуются варианты", "danger")
            else:
                options_list = [opt.strip() for opt in options_text.split("\n") if opt.strip()]
                options = json.dumps(options_list)
        
        question = Question(test_id=test.id, text=question_text, question_type=question_type, options=options)
        db.session.add(question)
        db.session.commit()
        flash("Вопрос создан", "success")
        return redirect(url_for("admin_test_questions", test_id=test.id))
    
    return render_template("admin_question_form.html", test=test, question=None, options_text='')


@app.route("/admin/questions/<int:question_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_question_edit(question_id):
    question = Question.query.get_or_404(question_id)
    test = Test.query.get_or_404(question.test_id)
    
    if request.method == "POST":
        question_text = request.form.get("question_text")
        question_type = request.form.get("question_type")
        options_text = request.form.get("options_text", "")
        
        if not question_text or not question_type:
            flash("Нехватает текста или типа вопроса", "danger")
            options_text = ''
            if question.options:
                try:
                    options_list = json.loads(question.options)
                    options_text = '\n'.join(options_list)
                except:
                    options_text = ''
            return render_template("admin_question_form.html", test=test, question=question, options_text=options_text)
        
        question.text = question_text
        question.question_type = question_type
        question.options = None
        
        if question_type in [Question.TYPE_SINGLE, Question.TYPE_MULTIPLE]:
            if not options_text.strip():
                flash("Для этого типа ребуются варианты", "danger")
            else:
                options_list = [opt.strip() for opt in options_text.split("\n") if opt.strip()]
                question.options = json.dumps(options_list)
        
        db.session.commit()
        flash("Вопрос отредактирован", "success")
        return redirect(url_for("admin_test_questions", test_id=test.id))
    
    options_text = ''
    if question.options:
        try:
            options_list = json.loads(question.options)
            options_text = '\n'.join(options_list)
        except:
            options_text = ''
    
    return render_template("admin_question_form.html", test=test, question=question, options_text=options_text)


@app.route("/admin/questions/<int:question_id>/delete", methods=["POST", "GET"])
@admin_required
def admin_question_delete(question_id):
    question = Question.query.get_or_404(question_id)
    test_id = question.test_id
    db.session.delete(question)
    db.session.commit()
    flash("Вопрос удален", "success")
    return redirect(url_for("admin_test_questions", test_id=test_id))


@app.route("/tests")
@login_required
def user_tests():
    tests = Test.query.all()
    return render_template("user_tests.html", tests=tests)


@app.route("/tests/<int:test_id>/take", methods=["GET", "POST"])
@login_required
def take_test(test_id):
    test = Test.query.get_or_404(test_id)
    questions = Question.query.filter_by(test_id=test.id).all()
    
    if request.method == "POST":
        answers = {}
        score = 0
        
        for question in questions:
            if question.question_type == Question.TYPE_SINGLE:
                answer = request.form.get(f"question_{question.id}")
                if answer:
                    answers[str(question.id)] = answer
                    score += 1
            elif question.question_type == Question.TYPE_MULTIPLE:
                answers_list = request.form.getlist(f"question_{question.id}")
                if answers_list:
                    answers[str(question.id)] = answers_list
                    score += len(answers_list)
            elif question.question_type == Question.TYPE_TEXT:
                answer = request.form.get(f"question_{question.id}")
                if answer:
                    answers[str(question.id)] = answer
            elif question.question_type == Question.TYPE_SCALE:
                answer = request.form.get(f"question_{question.id}")
                if answer:
                    answers[str(question.id)] = answer
                    score += int(answer)
        
        result = UserResult(
            user_id=current_user.id,
            test_id=test.id,
            answers_json=json.dumps(answers),
            score=score
        )
        db.session.add(result)
        db.session.commit()
        flash("Тест пройден", "success")
        return redirect(url_for("user_tests"))
    
    return render_template("take_test.html", test=test, questions=questions)


@app.route("/my_results")
@login_required
def my_results():
    results = UserResult.query.filter_by(user_id=current_user.id).all()
    return render_template("my_results.html", results=results)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True, host="127.0.0.1", port=5001)