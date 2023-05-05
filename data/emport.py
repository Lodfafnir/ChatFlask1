from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, validators
from accessor import ChatAccessor
import random
from random import choice
from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from data.chat import Base, User, Chat, Message
from sqlalchemy.orm import declarative_base, relationship
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, flash, jsonify
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, validators
from data.chat import Chat, Message
import requests
import os
from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
