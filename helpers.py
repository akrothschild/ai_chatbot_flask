import csv
import datetime
import sqlite3

import pytz
import requests
import urllib
import uuid

from flask import redirect, render_template, request, session
from functools import wraps

from werkzeug.security import generate_password_hash

from google.auth.transport import requests as google_requests
from pyapplesignin import AppleSignIn


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [
            ("-", "--"),
            (" ", "-"),
            ("_", "__"),
            ("?", "~q"),
            ("%", "~p"),
            ("#", "~h"),
            ("/", "~s"),
            ('"', "''"),
        ]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Prepare API request
    symbol = symbol.upper()
    end = datetime.datetime.now(pytz.timezone("US/Eastern"))
    start = end - datetime.timedelta(days=7)

    # Yahoo Finance API
    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{urllib.parse.quote_plus(symbol)}"
        f"?period1={int(start.timestamp())}"
        f"&period2={int(end.timestamp())}"
        f"&interval=1d&events=history&includeAdjustedClose=true"
    )

    # Query API
    try:
        response = requests.get(
            url,
            cookies={"session": str(uuid.uuid4())},
            headers={"Accept": "*/*", "User-Agent": request.headers.get("User-Agent")},
        )
        response.raise_for_status()

        # CSV header: Date,Open,High,Low,Close,Adj Close,Volume
        quotes = list(csv.DictReader(response.content.decode("utf-8").splitlines()))
        price = round(float(quotes[-1]["Adj Close"]), 2)
        return {"price": price, "symbol": symbol}
    except (KeyError, IndexError, requests.RequestException, ValueError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


'''
========================
GENERATE REGISTRATION
A function to register a user to use our system
========================
'''


def register_helper(db, request, method="form"):
    if method == "form":
        return register_via_form(db, request)
    elif method == "apple":
        return register_via_apple(db, request)
    elif method == "google":
        return register_via_google(db, request)
    else:
        return apology("Unsupported registration method", 400)


def register_via_form(db, request):
    # Handle form registration as per existing logic
    username = request.form.get("username")
    username = username.strip()
    password = request.form.get("password")
    confirm_password = request.form.get("confirmation")
    if confirm_password != password:
        return apology("Invalid Password, password must be same", 400)
    elif not username:
        return apology("must provide username", 400)
    elif not password:
        return apology("must provide password", 400)
    elif not confirm_password:
        return apology("Must Confirm Password!", 400)
    special_characters = '!@#$%^&*()-+?_=,<>/"'
    if not any(c in special_characters for c in password):
        return apology("Password Must Contain a special Character", 400)
    elif not any(c.isalnum() for c in password):
        return apology("Password must contain letters and numbers", 400)
    hash = generate_password_hash(password)
    try:
        # Add username to the database
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
    except sqlite3.IntegrityError:
        return apology("Username or account already exists", 400)
    except Exception as e:
        return apology("Failed to register user: " + str(e), 400)
    redirect_message = 'Successfully registered! Login now'
    return render_template("login.html", register_message=redirect_message)


def register_via_apple(db, request):
    # Handle registration via Apple OAuth

    # Example: Retrieve Apple ID token from the request (ensure security, validate token)
    apple_token = request.form.get("apple_token")

    # Initialize AppleSignIn with your client ID and client secret
    apple_signin = AppleSignIn(client_id='your_client_id', team_id='your_team_id', redirect_uri='your_redirect_uri',
                               key_id='your_key_id', key_file_path='path_to_your_private_key_file.pem')

    # Validate and decode the ID token
    try:
        decoded_token = apple_signin.validate_id_token(apple_token)
        # Extract user details
        email = decoded_token.get('email')
        apple_user_id = decoded_token.get('sub')

        # Check if the user already exists in your database
        existing_user = db.execute("SELECT * FROM users WHERE apple_user_id = ?", apple_user_id).fetchone()
        if existing_user:
            return apology("Apple account already linked to another user", 400)

        # Create a new user record in your database
        try:
            db.execute("INSERT INTO users (username, apple_user_id) VALUES (?, ?)", email, apple_user_id)
        except sqlite3.IntegrityError:
            return apology("Username or Apple account already exists", 400)
        except Exception as e:
            return apology("Failed to register user: " + str(e), 400)

        redirect_message = 'Successfully registered via Apple! Login now'
        return render_template("login.html", register_message=redirect_message)

    except Exception as e:
        return apology("Apple token validation failed: " + str(e), 400)


def register_via_google(db, request):
    # Handle registration via Google OAuth

    # Example: Retrieve Google ID token from the request (ensure security, validate token)
    google_token = request.form.get("google_token")

    try:
        # Verify the Google ID token
        id_info = google_token.verify_oauth2_token(google_token, google_requests.Request())

        # Extract user details
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Invalid issuer.')

        google_user_id = id_info['sub']
        email = id_info['email']

        # Check if the user already exists in your database
        existing_user = db.execute("SELECT * FROM users WHERE google_user_id = ?", google_user_id).fetchone()
        if existing_user:
            return apology("Google account already linked to another user", 400)

        # Create a new user record in your database
        try:
            db.execute("INSERT INTO users (username, google_user_id) VALUES (?, ?)", email, google_user_id)
        except sqlite3.IntegrityError:
            return apology("Username or Google account already exists", 400)
        except Exception as e:
            return apology("Failed to register user: " + str(e), 400)

        redirect_message = 'Successfully registered via Google! Login now'
        return render_template("login.html", register_message=redirect_message)

    except ValueError as e:
        return apology("Google token validation failed: " + str(e), 400)
