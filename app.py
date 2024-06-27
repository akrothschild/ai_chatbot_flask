import os
import logging

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from mistralai.models.chat_completion import ChatMessage

from flask_session import Session

from chatbot import ChatBot, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from helpers import apology, login_required, register_helper, login_helper, create_tables_if_not_exist

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("chatbot")

db = SQL("sqlite:///chat.db")

# Call the function to create tables
create_tables_if_not_exist(db)

# Initialize current chat control variable
current_chat_id = 0

# To use with SQLAlchemy
#
# class User(db.Model):
#     __tablename__ = 'Users'
#     user_id = db.Column(db.Integer, primary_key=True)
#     username = db.Column(db.String(50), unique=True)
#     email = db.Column(db.String(100), unique=True)
#     password_hash = db.Column(db.String(100))
#     created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
#
#
# class Chat(db.Model):
#     __tablename__ = 'Chats'
#     chat_id = db.Column(db.Integer, primary_key=True)
#     chat_name = db.Column(db.String(100))
#     user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'))
#     created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
#     user = db.relationship('User', backref=db.backref('chats', lazy=True))
#
#
# class Message(db.Model):
#     __tablename__ = 'Messages'
#     message_id = db.Column(db.Integer, primary_key=True)
#     chat_id = db.Column(db.Integer, db.ForeignKey('Chats.chat_id'))
#     user_id = db.Column(db.Integer, db.ForeignKey('Users.user_id'))
#     message_text = db.Column(db.Text)
#     role = db.Column(db.String(20), nullable=False)
#     created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
#     chat = db.relationship('Chat', backref=db.backref('messages', lazy=True))
#     user = db.relationship('User', backref=db.backref('messages', lazy=True))


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
    if 'user_id' in session:
        user_id = session['user_id']
        user = db.execute("SELECT username FROM Users WHERE user_id = ?", user_id)
        if user:
            return redirect(url_for("chats"))
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        return login_helper(db, request)

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
        return register_helper(db, request)
    else:
        return render_template("register.html")


@app.route('/chats', methods=['GET', 'POST'])
@login_required
def chats():
    if 'user_id' in session:
        user_id = session['user_id']
        user = db.execute("SELECT username FROM Users WHERE user_id = ?", user_id)
        if user:
            user_chats = db.execute("SELECT chat_id, chat_name FROM chats WHERE user_id = ? ORDER BY created_at DESC",
                                    user_id)
            return render_template('chats.html', chats=user_chats)
        else:
            logger.error(f"User {user_id} not found in the db")
            return apology("User not found", 404)
    else:
        logger.error(f"User not logged in")
        return apology("Unauthorized access", 401)


@app.route('/chat/<int:chat_id>', methods=['GET', 'POST'])
def do_chat(chat_id):
    global bot
    global current_chat_id
    if chat_id != current_chat_id:
        bot.new_chat()
    current_chat_id = chat_id
    if request.method == 'GET':
        if 'user_id' in session:
            user_id = session['user_id']
            user = db.execute("SELECT username FROM Users WHERE user_id = ?", user_id)
            if user:
                user_chats = db.execute(
                    "SELECT chat_id, chat_name FROM chats WHERE user_id = ? ORDER BY created_at DESC", user_id)
                selected_chat = db.execute("SELECT * FROM Chats WHERE Chats.chat_id = ? ORDER BY created_at DESC "
                                           "LIMIT 1", chat_id)
                if selected_chat:
                    # Retrieve messages for the last created chat
                    db_messages = db.execute(
                        "SELECT message_text, role FROM Messages WHERE chat_id = ? AND user_id = ?",
                        chat_id, user_id)
                    for message in bot.messages:
                        l = {"message_text": message.content, "role": message.role}
                        if l not in db_messages:
                            db_messages.append(l)
                            db.execute(
                                "INSERT INTO messages (chat_id, user_id, message_text, role) VALUES (?, ?, ?, ?)",
                                chat_id, user_id, message.content, message.role)
                            logger.info(
                                f'Inserted into messages: chat_id: {chat_id} for user: {user_id} message: {message.content} role: {message.role}')
                            new_chat_name = db.execute(
                                "SELECT message_text FROM messages WHERE chat_id = ? AND user_id = ? AND role = "
                                "'user' ORDER BY created_at DESC LIMIT 1",
                                chat_id, user_id)
                            db.execute("UPDATE chats SET chat_name = ? WHERE chat_id = ? AND user_id = ?",
                                       new_chat_name[0]["message_text"], chat_id, user_id)
                            logger.info(f'Updated chats: chat_id: {chat_id} for user: {user_id}')
                    for message in db_messages:
                        if message["message_text"] not in [msg.content for msg in bot.messages]:
                            bot.messages.append(ChatMessage(role=message["role"], content=message["message_text"]))
        else:
            user_chats = [{"chat_id": 0, "chat_name": "New Chat"}]
        return render_template('chat.html', chat_id=chat_id, messages=bot.messages, chats=user_chats)
    elif request.method == 'POST':
        if 'user_input' in request.form:
            user_input = request.form['user_input']
            if bot is None:
                return redirect(url_for('index'))
            if bot.is_command(user_input):
                bot.execute_command(user_input)
            else:
                bot.run_inference(user_input)
        return redirect(url_for('do_chat', chat_id=chat_id))
    bot.exit()


@app.route('/start_chat', methods=['GET'])
def start_chat():
    # Handle starting a new chat logic here
    # Redirect to a new chat page or handle form submission
    chat_id = 0
    chat_name = "New chat"
    bot.new_chat()
    if 'user_id' in session:
        user_id = session['user_id']
        user = db.execute("SELECT username FROM Users WHERE user_id = ?", user_id)
        if user:
            db.execute("INSERT INTO chats (chat_name, user_id) VALUES (?, ?)", chat_name, user_id)
            logger.info(logger.info(f'Inserted into db: chat_name: {chat_name} for user: {user_id}'))
            flash('New chat created successfully!', 'success')
            chat_id = db.execute(
                "SELECT chat_id FROM Chats WHERE chat_name = ? AND user_id = ? ORDER BY created_at DESC LIMIT 1",
                chat_name, user_id)
            return redirect(url_for('do_chat', chat_id=int(chat_id[0]['chat_id'])))
    return redirect(url_for('do_chat', chat_id=chat_id))


@app.route('/delete_chat', methods=['POST'])
def delete_chat():
    global current_chat_id
    if 'user_id' in session:
        user_id = session['user_id']
        user = db.execute("SELECT username FROM Users WHERE user_id = ?", user_id)
        if user:
            db.execute("DELETE FROM messages WHERE chat_id = ? AND user_id = ?", current_chat_id, user_id)
            db.execute("DELETE FROM chats WHERE chat_id = ? AND user_id = ?", current_chat_id, user_id)
            flash('Deleted successfully!', 'success')
            logger.info(f'Deleted chat and messages: chat_id: {current_chat_id} for user: {user_id}')
            chat_id = db.execute(
                "SELECT chat_id FROM Chats WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", user_id)
            bot.new_chat()
            if chat_id:
                current_chat_id = int(chat_id[0]['chat_id'])
            else:
                current_chat_id = 0
            return redirect(url_for('do_chat', chat_id=current_chat_id))
    chat_id = 0;
    bot.new_chat()
    return redirect(url_for('do_chat', chat_id=chat_id))


if __name__ == '__main__':
    app.run(debug=True)
