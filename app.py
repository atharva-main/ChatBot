from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain.schema import HumanMessage, AIMessage
from langchain_mistralai import ChatMistralAI

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

API_KEY = "rTZD2HoYGOZ14S80IQO1RIibXJgz6wYL"

# Initialize the Mistral AI model
llm = ChatMistralAI(model_name="mistral-tiny", api_key=API_KEY)

# Store conversation memory per session
user_sessions = {}

@app.route('/')
def home():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    """Handles new client connection."""
    session_id = request.sid
    user_sessions[session_id] = ConversationBufferMemory()
    emit('message', {'type': 'bot', 'content': 'Hello! How can I assist you today?'})

@socketio.on('chat')
def handle_chat(data):
    """Handles real-time chat messages via WebSocket."""
    session_id = request.sid
    user_input = data.get('message')

    if not user_input:
        emit('message', {'type': 'bot', 'content': 'Please enter a message.'})
        return

    # Retrieve or create memory for the session
    memory = user_sessions.get(session_id, ConversationBufferMemory())

    # Add user message to memory
    memory.chat_memory.add_user_message(user_input)

    # Generate AI response
    conversation = ConversationChain(llm=llm, memory=memory)
    response_dict = conversation.invoke(input=user_input)  # response is a dictionary

    # Extract response text
    response_text = response_dict.get("response") or response_dict.get("output") or str(response_dict)

    # Add AI response to memory
    memory.chat_memory.add_ai_message(response_text)

    # Emit messages back to the client
    emit('message', {'type': 'user', 'content': user_input})
    emit('message', {'type': 'bot', 'content': response_text})

@socketio.on('disconnect')
def handle_disconnect():
    """Handles client disconnection."""
    session_id = request.sid
    user_sessions.pop(session_id, None)
    print(f"User {session_id} disconnected.")

if __name__ == '__main__':
    socketio.run(app, debug=True)
