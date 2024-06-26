import os
import logging
import json

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from mistralai.models.chat_completion import ChatMessage

from flask_session import Session

from chatbot import ChatBot, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from helpers import apology, login_required, lookup, usd, register_helper, login_helper, create_tables_if_not_exist, \
    index_helper
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///chat.db'  # Replace with your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
Session(app)

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("chatbot")

db1 = SQL("sqlite:///chat.db")

# Call the function to create tables
create_tables_if_not_exist(db1)


class User(db.Model):
    __tablename__ = 'Users'
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    email = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String(100))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)


class Chat(db.Model):
    __tablename__ = 'Chats'
    chat_id = db.Column(db.Integer, primary_key=True)
    chat_name = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('chats', lazy=True))


class Message(db.Model):
    __tablename__ = 'Messages'
    message_id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('Chats.chat_id'))
    user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'))
    message_text = db.Column(db.Text)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    chat = db.relationship('Chat', backref=db.backref('messages', lazy=True))
    user = db.relationship('User', backref=db.backref('messages', lazy=True))


# ChatBot initialization (global scope)
bot = ChatBot(api_key=os.environ["MISTRAL_API_KEY"], model=DEFAULT_MODEL, system_message="",
              temperature=DEFAULT_TEMPERATURE)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    """Show portfolio of stocks"""
    return index_helper(db)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        return login_helper(SQL("sqlite:///chat.db"), request)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    session.clear()
    if request.method == "POST":
        return register_helper(SQL("sqlite:///chat.db"), request)
    else:
        return render_template("register.html")


@app.route('/chats')
@login_required
def chats():
    if 'user_id' in session:
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user:
            if request.method == 'POST':
                chat_name = "New chat"
                new_chat = Chat(chat_name=chat_name, user_id=user_id)
                db.session.add(new_chat)
                db.session.commit()
                flash('New chat created successfully!', 'success')
                return redirect(url_for('/chat'))
            else:
                chats = user.chats
                return render_template('chats.html', chats=chats)
        else:
            return "User not found", 404
    else:
        return "Unauthorized access", 401


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    global bot

    if request.method == 'GET':
        if 'user_id' in session:
            user_id = session['user_id']
            user = db1.execute("SELECT username FROM Users WHERE user_id = ?", user_id)
            if user:
                last_chat = db1.execute("SELECT * FROM Chats ORDER BY created_at DESC LIMIT 1")
                last_chat_id = db1.execute("SELECT chat_id FROM Chats ORDER BY created_at DESC LIMIT 1")
                if last_chat:
                    # Retrieve messages for the last created chat
                    db_messages = []
                    db_messages = db1.execute("SELECT message_text, role FROM Messages WHERE chat_id = ?",
                                              last_chat_id[0]["chat_id"])
                    for message in bot.messages:
                        l = {"message_text": message.content, "role": message.role}
                        if l not in db_messages:
                            db_messages.append(l)
                            db1.execute(
                                "INSERT INTO messages (chat_id, user_id, message_text, role) VALUES (?, ?, ?, ?)",
                                last_chat_id[0]["chat_id"], user_id, message.content, message.role)
                    for message in db_messages:
                        if message["message_text"] not in [msg.content for msg in bot.messages]:
                            bot.messages.append(ChatMessage(role=message["role"], content=message["message_text"]))
                        # messages = bot.messages
                        # # db1.execute(
                        # #     "INSERT INTO messages (chat_id, user_id, message_text, role) VALUES (?, ?, ?, ?)",
                        # #     last_chat_id[0]["chat_id"], user_id, bot.messages[-2].content, bot.messages[-2].role)
                        # # db1.execute(
                        # #     "INSERT INTO messages (chat_id, user_id, message_text, role) VALUES (?, ?, ?, ?)",
                        # #     last_chat_id[0]["chat_id"], user_id, bot.messages[-1].content, bot.messages[-1].role)
                        # str1 = ""
                        # str1 = str(bot.messages[-2].model_dump_json())
                        # print(str1)
                        # str2 = ""
                        # str2 = str(bot.messages[-1].model_dump_json())
                        # print(str2)
                        # db1.execute(
                        #     "INSERT INTO messages (chat_id, user_id, message_text, role) VALUES (?, ?, ?, ?)",
                        #     last_chat_id[0]["chat_id"], user_id, bot.messages[-2].content,
                        #     bot.messages[-2].role)
                        # db1.execute(
                        #     "INSERT INTO messages (chat_id, user_id, message_text, role) VALUES (?, ?, ?, ?)",
                        #     last_chat_id[0]["chat_id"], user_id, bot.messages[-1].content,
                        #     bot.messages[-1].role)
                    # else:
                    #     db1.execute(
                    #         "INSERT INTO messages (chat_id, user_id, message_text, role) VALUES (?, ?, ?, ?)",
                    #         last_chat_id[0]["chat_id"], user_id, "", "user")

        return render_template('chat.html', messages=bot.messages)
    elif request.method == 'POST':
        if 'user_input' in request.form:
            user_input = request.form['user_input']
            if bot is None:
                return redirect(url_for('index'))
            if bot.is_command(user_input):
                bot.execute_command(user_input)
                return redirect(url_for('chat'))
            else:
                bot.run_inference(user_input)
                return redirect(url_for('chat'))
    bot.exit()
