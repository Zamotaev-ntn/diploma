from flask import Flask, render_template, request, redirect, url_for, flash
from forms import RegisterForm

app = Flask(__name__)
app.secret_key = "secret"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        flash("Форма прошла проверку")
        return redirect(url_for("register"))
    return render_template("register.html", form=form)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5001)
