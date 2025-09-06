import os
import requests
import json
import time

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
    """✅ REAL-TIME BROWSING with Groq Compound Models"""
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
        
        # ✅ FIXED: Use Groq's Compound model for real web search
        chat_completion = client.chat.completions.create(
            model="groq/compound",  # ✅ This model has web search capability
            messages=messages,
            temperature=0.7,
            max_tokens=2048
        )
        
        print(f"✅ Compound API call successful!")
        
        if hasattr(chat_completion, 'choices') and chat_completion.choices:
            message = chat_completion.choices[0].message
            content = message.content if hasattr(message, 'content') else "No content"
            
            # ✅ Also get reasoning and search results if available
            reasoning = message.reasoning if hasattr(message, 'reasoning') else None
            executed_tools = message.executed_tools if hasattr(message, 'executed_tools') else None
            
            response_data = {"content": content}
            
            if reasoning:
                response_data["reasoning"] = reasoning
                print(f"🧠 Reasoning available: {len(reasoning) if reasoning else 0} chars")
            
            if executed_tools:
                response_data["search_results"] = executed_tools
                print(f"🔍 Search results available: {len(executed_tools)} tools")
            
            return jsonify(response_data)
        
        return jsonify({"content": "AI response received but content could not be extracted."})
            
    except Exception as e:
        print(f"❌ Real-time browsing error: {e}")
        return jsonify({
            "error": f"Browsing error: {str(e)}",
            "content": f"Real-time browsing failed: {str(e)}"
        }), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "StudyArea API with REAL Real-time Browsing",
        "status": "running",
        "groq_client": "initialized" if client else "not available",
        "features": ["chat", "REAL real-time browsing via Compound", "websockets"],
        "browsing_model": "groq/compound",
        "regular_models": ["openai/gpt-oss-120b", "qwen/qwen3-32b", "meta-llama/llama-4-scout"]
    })

if __name__ == '__main__':
    print("🚀 Starting StudyArea API with REAL Real-time Browsing")
    print(f"🌐 Web Search Model: groq/compound")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
