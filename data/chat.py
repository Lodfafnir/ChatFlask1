from datetime import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    password = Column(String(50), nullable=False)
    email = Column(String(50), nullable=True)
    active = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __str__(self):
        return '<User({})>'.format(self.username)

    def __init__(self, username, password):
        self.username = username
        self.password = password


class Chat(Base):
    __tablename__ = 'chat'
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=True)
    user1_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user2_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user1 = relationship('User', foreign_keys=[user1_id])
    user2 = relationship('User', foreign_keys=[user2_id])

    def __init__(self, user1_id, user2_id=None):
        self.user1_id = user1_id
        self.user2_id = user2_id


class UserStatus(Base):
    __tablename__ = 'user_status'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    user_id2 = Column(Integer, ForeignKey('user.id'), nullable=True)

    def __init__(self, user_id, single=True):
        self.user_id = user_id
        self.single = single

    def __str__(self):
        return self.text


class Message(Base):
    __tablename__ = 'message'
    id = Column(Integer, primary_key=True)
    text = Column(String(500), nullable=False)
    sent_by = Column(Integer, ForeignKey('user.id'), nullable=False)
    sent_to = Column(Integer, ForeignKey('user.id'), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    ridden = Column(Boolean, default=False)
    sender = relationship('User', foreign_keys=[sent_by])
    receiver = relationship('User', foreign_keys=[sent_to])
