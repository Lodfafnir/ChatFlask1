import random
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, redirect, url_for, request, flash, \
    jsonify
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from flask_wtf import FlaskForm
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from wtforms import StringField, PasswordField, validators

from accessor import ChatAccessor
from data.chat import Chat, Message

app = Flask(__name__)
app.secret_key = 'mysecretkey'
login_manager = LoginManager()
login_manager.init_app(app)

# db_uri = 'sqlite:///chat.db'
# engine = create_engine(db_uri)

accessor = ChatAccessor('sqlite:///db/chat.db')
Session = accessor.Session

accessor.create_tables()


@login_manager.user_loader
def load_user(user_id):
    return accessor.get_user_by_id(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for('login'))

class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[validators.DataRequired()])
    password = PasswordField('Пароль', validators=[
        validators.DataRequired(),
        validators.Length(min=8, message='Пароль должен быть не менее 8 символов')
    ])
    confirm_password = PasswordField('Подтвердите пароль', validators=[
        validators.DataRequired(),
        validators.EqualTo('password', message='Пароли должны совпадать')
    ])


@app.route("/dashboard")
@login_required
def dashboard():
    if not current_user.is_authenticaten:
        return redirect("login")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        # Check if the user already exists
        if accessor.get_user_by_username(username):
            flash('Пользователь с таким именем уже существует', 'error')
            return redirect(url_for('register'))
        # Create a new user
        user = accessor.add_user(username, password)
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html', user=current_user, form=form)


# создаем класс формы входа
class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[validators.DataRequired()])
    password = PasswordField('Пароль', validators=[validators.DataRequired()])


@login_required
@app.route('/chat/<int:user_id>/messages')
def chat_messages(user_id):
    msgs = accessor.get_all_message_by_id_to_id(current_user.id, user_id)
    messages = []
    for i in msgs:
        messages.append((i.text, i.sent_by, i.sent_to))
    return render_template('message_list.html', messages=messages)


# добавляем маршрут для отображения страницы входа
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if request.method == 'POST':
            username = form.username.data
            password = form.password.data
            user = accessor.get_user_by_username(username)
            if user.password == password:
                login_user(user)
                return redirect(url_for('index'))
    return render_template('login.html', user=current_user, form=form)


def update_last_act(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated:
            current_user.active = datetime.utcnow()
        return f(*args, **kwargs)

    return wrapper


@login_required
@app.route('/logout')
def logout():
    logout_user()
    return redirect("/")


@login_required
@app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
@update_last_act
def chat(user_id):
    if request.method == 'POST':
        text = request.form.get('message')
        accessor.add_message(text, current_user.id, user_id)
        return redirect("/chat/{}".format(user_id))
    msgs = accessor.get_all_message_by_id_to_id(current_user.id, user_id)
    messages = []
    for i in msgs:
        messages.append((i.text, i.sender.username, i.receiver.username))
    print(messages)
    return render_template('chat.html', user=current_user, messages=messages)


@app.route('/')
@app.route('/index')
@update_last_act
def index():
    return render_template('base.html', user=current_user)


@app.route('/check_updates')
@login_required
def check_updates():
    session = Session()
    self_chat = session.query(Chat).filter(Chat.user1_id == current_user.id).first()
    if self_chat and self_chat.user2_id:
        return jsonify({'redirect': f'/chat/{self_chat.user2_id}'})
    active_chats = session.query(Chat).filter(Chat.user1_id != current_user.id, Chat.user2_id == None).all()
    if active_chats:
        chat = random.choice(active_chats)
        chat.user2_id = current_user.id
        self_chat.user2_id = chat.user1_id
        session.commit()
        user2_id = chat.user1_id
        session.close()
        return jsonify({'redirect': f'/chat/{user2_id}'})
    return jsonify({})


@app.route('/get_message')
@login_required
def get_message():
    session = Session()
    messages = session.query(Message).filter(Message.sent_to == current_user.id, Message.ridden == False).all()
    newmes = render_template("new_messages.html", messages=messages)
    for i in messages:
        i.ridden = True
    session.commit()
    if messages:
        return jsonify({'messages': newmes})
    return jsonify({})

@app.route('/join_chat', methods=['GET'])
@login_required
def join_chat():
    session = Session()
    self_chat = session.query(Chat).filter(Chat.user1_id == current_user.id).first()
    if not self_chat:
        self_chat = Chat(user1_id=current_user.id)
        session.add(self_chat)
        session.commit()
    if self_chat.user2_id:
        user2_id = self_chat.user2_id
        session.close()
        return redirect(f'/chat/{user2_id}')
    return render_template('wait_form.html')


if __name__ == "__main__":
    app.run(port=5000)
