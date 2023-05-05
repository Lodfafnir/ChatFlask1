import requests

def test_token_api():
    # register_data = {
    #     'username': 'testuser',
    #     'password': 'testpassword',
    # }
    # register_response = requests.post('http://127.0.0.1:5000/api/v1/register', data=register_data)
    # assert register_response.status_code == 200

    # Логинимся и получаем токен
    login_data = {
        'username': 'Имя пользователя',
        'password': 'Имя пользователя',
    }
    login_response = requests.post('http://127.0.0.1:5000/api/v1/login', data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()['token']

    # Отправляем запрос на получение сообщений с токеном
    headers = {
        'Authorization': token,
    }
    messages_response = requests.post('http://127.0.0.1:5000/api/v1/get_messages', headers=headers)
    assert messages_response.status_code == 200
    messages = messages_response.json()
    print(messages)


test_token_api()