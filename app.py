import os
import logging

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from chatbot import ChatBot, DEFAULT_MODEL, DEFAULT_TEMPERATURE
from helpers import apology, login_required, lookup, usd, register_helper, login_helper, create_tables_if_not_exist, \
    index_helper

# Configure application
app = Flask(__name__)

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Initialize logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("chatbot")

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///chat.db")

# Call the function to create tables
create_tables_if_not_exist(db)

# ChatBot initialization (global scope)
bot = ChatBot(api_key=os.environ["MISTRAL_API_KEY"], model=DEFAULT_MODEL, system_message=None, temperature=DEFAULT_TEMPERATURE)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
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


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    global bot
    if request.method == 'GET':
        return render_template('chat.html')
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
