from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo


class RegisterForm(FlaskForm):
    """Форма регистрации пользователя"""

    email = StringField(
        "Email",
        validators=[
            DataRequired(message="Email обязателен"),
            Email(message="Некорректный email"),
        ],
    )

    password = PasswordField(
        "Пароль",
        validators=[
            DataRequired(message="Пароль обязателен"),
            Length(min=6, message="Минимум 6 символов"),
        ],
    )

    confirm_password = PasswordField(
        "Подтверждение пароля",
        validators=[
            DataRequired(message="Подтвердите пароль"),
            EqualTo("password", message="Пароли не совпадают"),
        ],
    )

    submit = SubmitField("Зарегистрироваться")
