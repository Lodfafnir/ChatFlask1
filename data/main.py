from accessor import ChatAccessor
import random
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, validators
from data.chat import Chat, Message
import requests
from werkzeug.utils import secure_filename
import os
import jwt
from jwt.exceptions import DecodeError

app = Flask(__name__)
app.secret_key = 'mysecretkey'
app.config['SECRET_KEY'] = 'shgsvhnahr'
app.config['UPLOAD_FOLDER'] = 'static/images'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png', 'gif'}

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


def get_token(user_id, secret_key):
    token = jwt.encode({'user_id': user_id}, secret_key, algorithm='HS256')
    return token


def decode_token(token, secret_key):
    try:
        decoded_token = jwt.decode(token, secret_key, algorithms=['HS256'])
        return decoded_token
    except DecodeError:
        return None


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        if accessor.get_user_by_username(username):
            flash('Пользователь с таким именем уже существует', 'error')
            return redirect(url_for('register'))
        user = accessor.add_user(username, password)
        login_user(user)
        return redirect(url_for('index'))
    return render_template('register.html', user=current_user, form=form)


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


@login_required
@app.route("/exit_chat")
def exit_chat():
    accessor.clear_chat(current_user.id)
    return redirect("index")


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
def chat(user_id, recipient=None):
    if request.method == 'POST':
        text = request.form.get('message')
        accessor.add_message(text, current_user.id, user_id)
        return redirect("/chat/{}".format(user_id))
    msgs = accessor.get_all_message_by_id_to_id(current_user.id, user_id)
    messages = []
    for i in msgs:
        messages.append((i.text, i.sender.username, i.receiver.username))
    print(messages)
    print(current_user.id, user_id)
    return render_template('chat.html', user=current_user, messages=messages, recipient=user_id)
    print(recipient)



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


@app.route("/api/v1/get_messages", methods=["POST"])
def api_get_messages():
    token = request.headers.get('Authorization')
    print(token)
    if not token:
        return jsonify({
            'status': 401,
            'message': 'Токен отсутствует'
        })
    try:
        decoded_token = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = decoded_token['user_id']
        messages = accessor.get_all_message(user_id)
        messages = [message.to_dict() for message in messages]
        return jsonify(messages)
    except jwt.ExpiredSignatureError:
        return jsonify({
            'status': 401,
            'message': 'Истек срок действия токена'
        })
    except jwt.InvalidTokenError:
        return jsonify({
            'status': 401,
            'message': 'Неверный токен'
        })


@app.route('/api/v1/login', methods=['POST'])
def login_api():
    username = request.form.get('username')
    password = request.form.get('password')
    user = accessor.get_user_by_username(username)
    if user and user.password == password:
        token = get_token(user.id, app.config['SECRET_KEY'])
        return jsonify({
            'token': token
        })
    else:
        return jsonify({
            'status': 401,
            'message': 'Неверный логин или пароль'
        })


@app.route('/api/v1/register', methods=['POST'])
def register_api():
    username = request.form.get('username')
    password = request.form.get('password')
    if username and password:
        user = accessor.add_user(username, password)
        token = get_token(user.id, app.config['SECRET_KEY'])
        return jsonify({
            'token': token
        })
    else:
        return jsonify({
            'status': 400,
            'message': 'Не удалось зарегистрироваться'
        })


@login_required
@app.route('/upload_photo_form')
def upload_photo_form():
    return render_template('upload_photo_form.html')


@login_required
@app.route('/upload_photo', methods=['POST'])
def upload_photo():
    user_id = current_user.id
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo found'})
    photo = request.files['photo']
    if photo.filename == '':
        return jsonify({'error': 'No selected file'})
    if photo and allowed_file(photo.filename):
        filename = secure_filename(f'{user_id}.jpg')
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return redirect("index")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)
