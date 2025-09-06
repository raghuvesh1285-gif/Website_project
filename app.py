import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

# Initialize Groq client
api_key = os.environ.get("GROQ_API_KEY")
client = None
if api_key:
    try:
        client = Groq(api_key=api_key)
        print("✅ Groq client initialized")
    except Exception as e:
        print(f"❌ Groq initialization failed: {e}")

@app.route('/api/chat', methods=['POST'])
def chat():
    print("📨 Chat request received")
    
    if not client:
        return jsonify({
            "error": "API client not available",
            "content": "Chat service is currently unavailable"
        }), 500

    try:
        # Get request data
        data = request.get_json()
        
        # Validate request
        if not data or 'messages' not in data:
            return jsonify({
                "error": "Invalid request format",
                "content": "Please provide messages array"
            }), 400

        messages = data['messages']
        model_id = data.get('model', 'openai/gpt-oss-120b')
        
        print(f"🚀 Processing with model: {model_id}")
        print(f"📝 Messages count: {len(messages)}")

        # Call Groq API with error handling
        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=model_id,
                temperature=0.3,
                max_tokens=1024
            )
            
            # Extract content safely
            if chat_completion and hasattr(chat_completion, 'choices') and chat_completion.choices:
                first_choice = chat_completion.choices
                if hasattr(first_choice, 'message') and hasattr(first_choice.message, 'content'):
                    content = first_choice.message.content
                    print(f"✅ Response generated successfully")
                    return jsonify({"content": content})
            
            # Fallback if structure is unexpected
            print("❌ Unexpected response structure")
            return jsonify({"content": "Sorry, I couldn't generate a response. Please try again."})
            
        except Exception as groq_error:
            print(f"❌ Groq API error: {groq_error}")
            return jsonify({
                "error": f"AI service error: {str(groq_error)}",
                "content": "The AI service encountered an error. Please try again."
            }), 500

    except Exception as e:
        print(f"❌ General error: {e}")
        return jsonify({
            "error": f"Server error: {str(e)}",
            "content": "An unexpected error occurred. Please try again."
        }), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "StudyHub API - Fixed Version",
        "status": "running",
        "groq_available": client is not None
    })

@app.route('/test', methods=['GET'])
def test():
    return jsonify({
        "message": "Test endpoint working",
        "timestamp": "2025-09-06",
        "version": "error-fixed"
    })

if __name__ == '__main__':
    print("🚀 Starting StudyHub API (Error-Fixed Version)...")
    app.run(host='0.0.0.0', port=5000)
