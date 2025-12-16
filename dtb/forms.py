from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, TextAreaField, SelectField, FloatField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=2, max=80)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Полное имя', validators=[DataRequired(), Length(min=2, max=100)])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password')])
    is_admin = BooleanField('Администратор')
    submit = SubmitField('Зарегистрировать')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Пользователь с таким логином уже существует.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Пользователь с таким email уже существует.')

class TaskForm(FlaskForm):
    title = StringField('Заголовок задания', validators=[DataRequired(), Length(min=5, max=200)])
    description = TextAreaField('Описание', validators=[DataRequired(), Length(min=10, max=1000)])
    task_type = SelectField('Тип задания', choices=[('personal', 'Личное'), ('general', 'Общее')], validators=[DataRequired()])
    assigned_to = SelectField('Назначить работнику', coerce=int)
    payment_amount = FloatField('Сумма оплаты (только для админа)')
    submit = SubmitField('Создать задание')

class CommentForm(FlaskForm):
    content = TextAreaField('Комментарий', validators=[DataRequired(), Length(min=1, max=1000)])
    submit = SubmitField('Добавить комментарий')