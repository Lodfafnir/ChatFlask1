from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, validators

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[validators.DataRequired()])
    password = PasswordField('Пароль', validators=[validators.DataRequired()])
    confirm_password = PasswordField('Повторите пароль', validators=[
        validators.DataRequired(),
        validators.EqualTo('password', message='Пароли не совпадают')
    ])
