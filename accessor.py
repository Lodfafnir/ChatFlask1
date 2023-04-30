import random
from random import choice
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from data.chat import Base, User, Chat, Message


class ChatAccessor:
    def __init__(self, db_uri):
        self.engine = create_engine(db_uri)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def get_random_active_user(self, seld_id):
        time_s = datetime.utcnow() - timedelta(minutes=5)
        users = self.session.query(User).filter(
            User.last_activity >= time_s,
            User.id != seld_id
        ).all()
        random_user = random.choice(users)
        self.add_chat("Тюленчик", seld_id, random_user.id)

    def get_random_other_user(self, user_id):
        users = self.session.query(User).filter(User.id != user_id).all()
        return choice(users)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def add_user(self, username, password):
        user = self.session.query(User).filter_by(username=username).first()
        if user is not None:
            return None
        user = User(username=username, password=password)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_user_by_id(self, user_id):
        with self.Session() as session:
            user = session.query(User).filter_by(id=user_id).first()
            return user

    def get_user_by_username(self, username):
        with self.Session() as session:
            user = session.query(User).filter_by(username=username).first()
            return user

    def add_chat(self, name, user1_id, user2_id):
        with self.Session() as session:
            chat = Chat(name=name, user1_id=user1_id, user2_id=user2_id,
                        created_at=datetime.utcnow())
            session.add(chat)
            session.commit()
            session.refresh()

    def get_chat_by_id(self, chat_id):
        with self.Session() as session:
            chat = session.query(Chat).filter_by(id=chat_id).first()
            return chat

    def get_chats_by_user_id_with_user2_id(self, user_id, user2_id):
        with self.Session() as session:
            chat = session.query(Chat).filter(
                Chat.user1_id == user_id or Chat.user2_id == user_id,
                Chat.user1_id == user2_id or Chat.user2_id == user2_id).first()
            return chat

    def add_message(self, text, sent_by, sent_to):
            message = Message(text=text, sent_by=sent_by,
                              sent_to=sent_to, created_at=datetime.utcnow())
            self.session.add(message)
            self.session.commit()

    def get_messages_by_chat_id(self, chat_id):
        with self.Session() as session:
            messages = session.query(Message).filter_by(chat_id=chat_id).all()
            return messages

    def get_all_message_by_id_to_id(self, id1, id2):
        messages = self.session.query(Message).filter(
        or_(Message.sent_by == id1, Message.sent_to == id1),
        or_(Message.sent_by == id2, Message.sent_to == id2)).all()
        return messages
