from flask import Flask, render_template, request, redirect, url_for, flash
from forms import RegisterForm
from models import User
from extensions import db
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = "secret"


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
                password_hash=generate_password_hash(form.password.data),
            )
            db.session.add(user)
            db.session.commit()
            flash("Регистрация успешна")
        return redirect(url_for("register"))
    return render_template("register.html", form=form)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)
