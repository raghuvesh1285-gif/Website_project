import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Initialize Groq client
api_key = os.environ.get("GROQ_API_KEY")
client = None
if api_key:
    try:
        client = Groq(api_key=api_key)
        print("✅ Groq client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")

@app.route('/api/chat', methods=['POST'])
def chat():
    print("📨 Received chat request")
    
    if not client:
        return jsonify({"error": "Groq API client not available"}), 500

    try:
        # Get and validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data received"}), 400
            
        print(f"📋 Request data: {data}")
        
        # Validate messages field
        if 'messages' not in data or not isinstance(data['messages'], list):
            return jsonify({"error": "Messages must be an array"}), 400
            
        if len(data['messages']) == 0:
            return jsonify({"error": "Messages array cannot be empty"}), 400

        messages = data['messages']
        model_id = data.get('model', 'openai/gpt-oss-120b')
        
        print(f"🚀 Calling Groq API with model: {model_id}")
        print(f"📝 Messages: {messages}")
        
        # Call Groq API - FIXED response handling
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_id,
            temperature=0.3,
            max_tokens=1024
        )
        
        print(f"📥 Raw API response: {chat_completion}")
        
        # ✅ CORRECT way to access response content
        if hasattr(chat_completion, 'choices') and len(chat_completion.choices) > 0:
            # Use object attribute access for Groq SDK response
            content = chat_completion.choices.message.content
            print(f"✅ Extracted content: {content}")
            
            return jsonify({
                "content": content or "No response generated"
            })
        else:
            print("❌ No choices in response")
            return jsonify({
                "content": "No response generated from AI model"
            })

    except Exception as e:
        print(f"❌ Error in chat endpoint: {str(e)}")
        print(f"❌ Error type: {type(e)}")
        
        return jsonify({
            "error": f"Server error: {str(e)}",
            "content": "An error occurred. Please try again."
        }), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "StudyHub API is running! 🚀",
        "status": "healthy",
        "groq_client": "connected" if client else "disconnected"
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "groq_available": client is not None,
        "timestamp": "2025-09-06"
    })

if __name__ == '__main__':
    print("🚀 Starting StudyHub API...")
    app.run(host='0.0.0.0', port=5000, debug=True)
