from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager
from config import Config
from forms import RegisterForm
from models import User
from extensions import db
from werkzeug.security import generate_password_hash

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


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True, host="127.0.0.1", port=5001)