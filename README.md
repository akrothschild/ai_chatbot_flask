# CS50 AI Chatbot

#### Final Project for CS50x 2024 Course

#### [Github](https://github.com/akrothschild/ai_chatbot_flask)

#### Description: CS50 AI Chatbot built on Flask using Mistral AI

### Overview

The CS50 AI Chatbot is designed to provide an interactive chatting experience using artificial intelligence. Built on
the Flask framework and leveraging the power of Mistral AI, this project demonstrates the integration of AI with web
applications. Users can interact with the chatbot through a web interface, and the chatbot can respond intelligently
based on the inputs provided.

### Features

- **User Authentication**: Secure login and registration system.
- **Persistent Chat Sessions**: Users can start new chats, continue existing ones, and have their conversations stored.
- **AI-Powered Responses**: Utilizes Mistral AI for generating chatbot responses.
- **Responsive Design**: User interface built with Bootstrap for seamless experience across devices.
- **Logging and Error Handling**: Integrated logging for debugging and tracking errors.

### Before You Start

#### Requirements

Ensure you have the following installed:

- Python 3.7+
- Flask
- Flask-Session
- cs50
- Mistral AI SDK

You will also need `MISTRAL_API_KEY` as an environmental variable. To get it, visit [mistral.ai](https://mistral.ai) and
generate an API token. Place it into your IDE configuration or use a .env file.

#### Setting Up the Environment

##### Using an IDE:

For example, in PyCharm:

1. Go to `Run` -> `Edit Configurations`.
2. Add a new environment variable: `MISTRAL_API_KEY` with the value of your API token.

##### Using Terminal:

Navigate to the folder where `app.py` is located and create a .env file:

```bash
echo "export MISTRAL_API_KEY=<YOUR_API_TOKEN>" >> .env
```

##### Updating the Code

Ensure your code loads the environment variables correctly. You can use the `python-dotenv` package to manage your
environment variables. Update your code as follows:

```PPython
from dotenv import load_dotenv
import os

# Load environment variables (if .env is in the same folder)
load_dotenv()

# Change ChatBot initialization (global scope)
bot = ChatBot(api_key=os.getenv("MISTRAL_API_KEY"), model=DEFAULT_MODEL, system_message="", temperature=DEFAULT_TEMPERATURE)
```

##### Running the Project
To start the project, open a terminal in the folder where `app.py` is located and run:

```BBash
flask run
```

This will start the Flask development server. You can then open your web browser and navigate to `http://127.0.0.1:5000` to interact with the chatbot.

### Project Structure
Here's a brief overview of the project's structure:

- **app.py**: The main Flask application file that initializes the app and routes.
- **templates/**: Contains the HTML templates for rendering the web pages.
- **static/**: Contains static files such as CSS and JavaScript.
- **helpers.py**: Includes helper functions for handling user authentication and other utilities.
- **chatbot.py**: Defines the ChatBot class and its methods.

### Key Components

#### User Authentication
The application provides secure login and registration functionality using Flask-Session to manage user sessions. Passwords are hashed for security.

#### Chat Functionality
Users can start new chats or continue previous ones. Each chat is associated with a user and stored in the database. The chat interface displays the conversation history and allows users to send new messages.

#### AI-Powered Responses
The chatbot uses Mistral AI to generate responses based on user inputs. The integration is handled by the `ChatBot` class, which sends user inputs to the Mistral API and processes the responses.

### Example Usage
After setting up the environment and starting the Flask server, follow these steps to use the chatbot:
1. **Register**: Create a new user account by providing a username, email, and password.
2. **Login**: Log in with your credentials.
3. **Start a New Chat**: Click on "Start a New Chat" to begin a new conversation.
4. **Interact with the Chatbot**: Type your messages and receive responses from the chatbot.

### Troubleshooting
If you encounter issues, check the following:
- Ensure your `MISTRAL_API_KEY` is correctly set.
- Verify that all required packages are installed (check `requirements.txt`) or run:
```BBash
pip install -r requirements.txt
```
- Check the terminal for error messages and stack traces to debug the issue.
- Ensure the Flask server is running and accessible at `http://127.0.0.1:5000`.

### Additional Features
To further enhance the chatbot, consider implementing the following features:
- **RAG Training**: Train the model on a new data, for example, from Harvard University, so that the Chatbot will be able to answer any questions about Harvard.
- **Add Workers through GitHub Actions**: Automatically start and deploy your Chatbot on the Internet when an update is pushed/merged to the `main` branch.
- **User Profiles**: Allow users to update their profiles with additional information.
- **Chat Export**: Provide an option to export chat history as a text file.
- **Advanced AI Integration**: Explore other AI models or APIs to improve the chatbot's responses.
- **Mobile Optimization**: Ensure the web interface is fully optimized for mobile devices.

### Contributions
Contributions to the project are welcome. If you have ideas for new features or improvements, feel free to fork the repository and submit a pull request.

### License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

### Acknowledgements
- **CS50x**: Thanks to the CS50x course for providing the foundational knowledge and inspiration for this project.
- **Flask**: A lightweight WSGI web application framework in Python.
- **Mistral AI**: For providing the AI model used in this project.

### Contact
For any questions or feedback, please reach out to me on [GitHub](https://github.com/akrothschild).

By following this guide and using the provided code, you should be able to set up and run the CS50 AI Chatbot successfully. Happy chatting!
