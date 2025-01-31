from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langchain_mistralai import ChatMistralAI
from datetime import datetime
import json
import os
import uuid
from apikey import apikey

app = Flask(__name__)
app.secret_key = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

API_KEY = apikey()
CHATS_FILE = "chats.json"

# Initialize the Mistral AI model
llm = ChatMistralAI(model_name="mistral-tiny", api_key=API_KEY)

class ChatManager:
    def __init__(self):
        self.chats = self._load_chats()
        self.user_sessions = {}

    def _load_chats(self):
        try:
            if os.path.exists(CHATS_FILE):
                with open(CHATS_FILE, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading chats: {e}")
            return {}

    def _save_chats(self):
        try:
            with open(CHATS_FILE, 'w') as f:
                json.dump(self.chats, f, indent=2)
        except Exception as e:
            print(f"Error saving chats: {e}")

    def create_chat(self, user_id):
        chat_id = str(uuid.uuid4())
        new_chat = {
            "title": "New Chat",
            "created_at": datetime.now().isoformat(),
            "messages": [],
            "user_id": user_id
        }
        self.chats[chat_id] = new_chat
        self.user_sessions[user_id] = chat_id
        self._save_chats()
        return chat_id

    def get_user_chats(self, user_id):
        return {k: v for k, v in self.chats.items() if v.get('user_id') == user_id}

    def add_message(self, chat_id, role, content):
        if chat_id in self.chats:
            self.chats[chat_id]['messages'].append({
                "role": role,
                "content": content,
                "timestamp": datetime.now().isoformat()
            })
            # Update title from first user message
            if len(self.chats[chat_id]['messages']) == 1:
                self.chats[chat_id]['title'] = content[:50]
            self._save_chats()

    def get_chat_history(self, chat_id):
        return self.chats.get(chat_id, {}).get('messages', [])

chat_manager = ChatManager()

@app.route('/')
def home():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    user_id = session.get('user_id')
    if not user_id:
        return
    
    # Initialize user session
    if user_id not in chat_manager.user_sessions:
        chat_id = chat_manager.create_chat(user_id)
    else:
        chat_id = chat_manager.user_sessions[user_id]
    
    emit('init', {
        'chats': chat_manager.get_user_chats(user_id),
        'active_chat': chat_id
    })

@socketio.on('new_chat')
def handle_new_chat():
    user_id = session.get('user_id')
    chat_id = chat_manager.create_chat(user_id)
    emit('chat_created', {
        'chat_id': chat_id,
        'title': chat_manager.chats[chat_id]['title'],
        'created_at': chat_manager.chats[chat_id]['created_at']
    }, broadcast=True)

@socketio.on('switch_chat')
def handle_switch_chat(data):
    user_id = session.get('user_id')
    chat_id = data['chat_id']
    
    if user_id in chat_manager.user_sessions:
        chat_manager.user_sessions[user_id] = chat_id
    
    history = chat_manager.get_chat_history(chat_id)
    emit('chat_switched', {
        'chat_id': chat_id,
        'history': history
    })

@socketio.on('chat')
def handle_chat(data):
    user_id = session.get('user_id')
    chat_id = chat_manager.user_sessions.get(user_id)
    user_input = data.get('message')
    
    if not user_input or not chat_id:
        return

    # Store user message
    chat_manager.add_message(chat_id, 'user', user_input)

    # Create conversation chain with history
    memory = ConversationBufferMemory()
    for msg in chat_manager.get_chat_history(chat_id):
        if msg['role'] == 'user':
            memory.chat_memory.add_user_message(msg['content'])
        else:
            memory.chat_memory.add_ai_message(msg['content'])

    # Generate response
    conversation = ConversationChain(llm=llm, memory=memory)
    response = conversation.invoke(input=user_input)
    response_text = response.get("response", "I'm having trouble understanding. Please try again.")

    # Store AI response
    chat_manager.add_message(chat_id, 'assistant', response_text)

    # Update frontend
    emit('message', {
        'type': 'assistant',
        'content': response_text,
        'chat_id': chat_id
    })

if __name__ == '__main__':
    if not os.path.exists(CHATS_FILE):
        with open(CHATS_FILE, 'w') as f:
            json.dump({}, f)
    socketio.run(app, debug=True)