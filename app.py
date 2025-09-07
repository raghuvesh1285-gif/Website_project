import os
import requests
import json
import time
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from groq import Groq

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Groq client
api_key = os.environ.get("GROQ_API_KEY")
client = None

print(f"🔑 API Key present: {'Yes' if api_key else 'No'}")

if api_key:
    try:
        client = Groq(api_key=api_key)
        print("✅ Groq client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")

# ✅ FIXED: Function to serialize ExecutedTool objects
def serialize_executed_tools(executed_tools):
    """Convert ExecutedTool objects to JSON-serializable dictionaries"""
    if not executed_tools:
        return []
    
    serialized = []
    for tool in executed_tools:
        tool_dict = {}
        
        # Safely extract common attributes
        for attr in ['name', 'type', 'index', 'arguments', 'output', 'search_results']:
            if hasattr(tool, attr):
                val = getattr(tool, attr)
                
                # Handle different types of values
                if val is not None:
                    if isinstance(val, (str, int, float, bool, list, dict)):
                        tool_dict[attr] = val
                    else:
                        # Convert complex objects to string
                        try:
                            tool_dict[attr] = str(val)
                        except Exception:
                            tool_dict[attr] = repr(val)
        
        # Add additional tool information if available
        if hasattr(tool, '__dict__'):
            for key, value in tool.__dict__.items():
                if key not in tool_dict and not key.startswith('_'):
                    try:
                        if isinstance(value, (str, int, float, bool, list, dict)):
                            tool_dict[key] = value
                        else:
                            tool_dict[key] = str(value)
                    except Exception:
                        pass
        
        serialized.append(tool_dict)
    
    return serialized

@app.route('/api/chat', methods=['POST'])
def chat():
    print("\n" + "="*50)
    print("📨 NEW CHAT REQUEST RECEIVED")
    print("="*50)
    
    if not client:
        print("❌ No Groq client available")
        return jsonify({
            "error": "API client not initialized",
            "content": "Chat service is not available. Please check server logs."
        }), 500

    try:
        data = request.get_json()
        print(f"📋 Raw request data: {data}")
        
        if not data:
            return jsonify({
                "error": "No JSON data",
                "content": "Please provide valid JSON data."
            }), 400

        model_id = data.get('model', 'openai/gpt-oss-120b')
        messages = data.get('messages', [])
        
        print(f"🤖 Model ID: {model_id}")
        print(f"💬 Messages: {messages}")

        if not messages or not isinstance(messages, list):
            return jsonify({
                "error": "Messages must be a non-empty array",
                "content": "Please provide valid messages array."
            }), 400

        print(f"🚀 Calling Groq API with model: {model_id}")

        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=model_id,
                temperature=0.7,
                max_tokens=1024
            )

            print(f"✅ API call successful!")
            
            if hasattr(chat_completion, 'choices') and chat_completion.choices:
                message = chat_completion.choices[0].message
                if hasattr(message, 'content') and message.content:
                    return jsonify({
                        "content": message.content
                    })
            
            return jsonify({
                "content": "AI response received but content could not be extracted."
            })

        except Exception as groq_error:
            print(f"❌ Groq API Error: {groq_error}")
            return jsonify({
                "error": f"AI API Error: {str(groq_error)}",
                "content": f"The AI service returned an error: {str(groq_error)}"
            }), 500

    except Exception as e:
        print(f"❌ General error: {e}")
        return jsonify({
            "error": f"Server error: {str(e)}",
            "content": "An unexpected server error occurred."
        }), 500

@app.route('/api/chat-with-browsing', methods=['POST'])
def chat_with_browsing():
    """✅ FIXED: Real-time browsing with proper ExecutedTool serialization"""
    print("\n" + "="*50)
    print("🤖🌐 REAL-TIME BROWSING REQUEST")
    print("="*50)
    
    if not client:
        return jsonify({
            "error": "API client not initialized",
            "content": "Chat service is not available."
        }), 500

    try:
        data = request.get_json()
        messages = data.get('messages', [])
        
        print(f"🔗 Using COMPOUND model for real-time browsing")
        
        # Enhanced system message for better browsing
        enhanced_messages = [
            {
                "role": "system",
                "content": "You are StudyArea AI with real-time web search capabilities. When users ask about current events, recent information, stock prices, weather, news, or include URLs, use your web search tools to provide up-to-date, accurate information. Always cite your sources."
            }
        ] + messages
        
        # ✅ FIXED: Use Groq's Compound model for real web search
        chat_completion = client.chat.completions.create(
            model="groq/compound",  # ✅ This model has web search capability
            messages=enhanced_messages,
            temperature=0.7,
            max_tokens=2048
        )
        
        print(f"✅ Compound API call successful!")
        
        if hasattr(chat_completion, 'choices') and chat_completion.choices:
            message = chat_completion.choices[0].message
            content = message.content if hasattr(message, 'content') else "No content"
            
            response_data = {"content": content}
            
            # ✅ FIXED: Properly serialize reasoning if available
            if hasattr(message, 'reasoning') and message.reasoning:
                response_data["reasoning"] = str(message.reasoning)
                print(f"🧠 Reasoning available: {len(str(message.reasoning))} chars")
            
            # ✅ FIXED: Properly serialize executed tools
            if hasattr(message, 'executed_tools') and message.executed_tools:
                try:
                    serialized_tools = serialize_executed_tools(message.executed_tools)
                    response_data["search_results"] = serialized_tools
                    print(f"🔍 Search results serialized: {len(serialized_tools)} tools")
                except Exception as serialize_error:
                    print(f"⚠️ Tool serialization error: {serialize_error}")
                    response_data["search_results"] = [{"error": "Could not serialize search results"}]
            
            return jsonify(response_data)
        
        return jsonify({"content": "AI response received but content could not be extracted."})
            
    except Exception as e:
        print(f"❌ Real-time browsing error: {e}")
        return jsonify({
            "error": f"Browsing error: {str(e)}",
            "content": f"Real-time browsing failed: {str(e)}"
        }), 500

# Store active connections and browsing sessions
active_connections = []
browsing_sessions = {}

# WebSocket handlers
@socketio.on('connect')
def on_connect():
    active_connections.append(request.sid)
    print(f"🔌 Client {request.sid} connected")
    emit('connection_status', {'status': 'connected', 'message': 'Real-time browsing enabled'})

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in active_connections:
        active_connections.remove(request.sid)
    print(f"🔌 Client {request.sid} disconnected")

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "StudyArea API with FIXED Real-time Browsing",
        "status": "running",
        "groq_client": "initialized" if client else "not available",
        "features": ["chat", "FIXED real-time browsing via Compound", "websockets"],
        "browsing_model": "groq/compound",
        "regular_models": ["openai/gpt-oss-120b", "qwen/qwen3-32b", "meta-llama/llama-4-scout"],
        "fix_applied": "ExecutedTool serialization fixed"
    })

@app.route('/debug', methods=['GET'])
def debug():
    return jsonify({
        "groq_client_available": client is not None,
        "api_key_length": len(api_key) if api_key else 0,
        "active_connections": len(active_connections),
        "browsing_sessions": len(browsing_sessions),
        "serialization_fix": "Applied for ExecutedTool objects"
    })

if __name__ == '__main__':
    print("🚀 Starting StudyArea API with FIXED Real-time Browsing")
    print(f"🌐 Web Search Model: groq/compound")
    print(f"🔧 ExecutedTool Serialization: FIXED")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
