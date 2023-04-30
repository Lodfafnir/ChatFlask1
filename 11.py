from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)

# Sample data of users and messages
users = {
    'john': {
        'name': 'John',
        'status': 'online',
        'messages': []
    },
    'jane': {
        'name': 'Jane',
        'status': 'offline',
        'messages': []
    },
    'bob': {
        'name': 'Bob',
        'status': 'offline',
        'messages': []
    }
}
@app.route('/')
def home():
    current_user = session.get('username')
    contacts = []

    for username, user_data in users.items():
        # Exclude current user from the list of contacts
        if username != current_user:
            contacts.append(user_data)

    return render_template('home.html', contacts=contacts)

# Chat page with messages
@app.route('/chat/<username>')
def chat(username):
    # Get current user
    current_user = session.get('username')

    # Get messages between current user and selected contact
    messages = []

    if username in users:
        selected_user = users[username]
        messages = selected_user['messages']

    return render_template('chat.html', username=username, messages=messages)

# Send message from chat page
@app.route('/send_message/<username>', methods=['POST'])
def send_message(username):
    current_user = session.get('username')
    message = request.form['message']
    users[current_user]['messages'].append((message, username))
    users[username]['messages'].append((message, current_user))
    return redirect(url_for('chat', username=username))
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        session['username'] = username
        users[username]['status'] = 'online'
        return redirect(url_for('home'))
    return render_template('login.html')
# Logout function
@app.route('/logout')
def logout():
    # Get current user
    current_user = session.get('username')
    users[current_user]['status'] = 'offline'
    session.pop('username', None)

    return redirect(url_for('login'))

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.run(debug=True)
