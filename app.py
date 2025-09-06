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

api_key = os.environ.get("GROQ_API_KEY")
client = None
if api_key:
    try:
        client = Groq(api_key=api_key)
        print("✅ Groq client initialized")
    except Exception as e:
        print(f"❌ Groq error: {e}")

@app.route('/api/chat', methods=['POST'])
def chat():
    print("📨 Chat request received")
    
    if not client:
        return jsonify({"error": "API not available"}), 500

    try:
        # Get JSON data
        data = request.get_json()
        print(f"📋 Request data: {data}")
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        # Validate required fields
        if 'messages' not in data:
            return jsonify({"error": "Missing 'messages' field"}), 400
            
        if not isinstance(data['messages'], list):
            return jsonify({"error": "'messages' must be an array"}), 400
            
        if len(data['messages']) == 0:
            return jsonify({"error": "'messages' array cannot be empty"}), 400

        messages = data['messages']
        model_id = data.get('model', 'openai/gpt-oss-120b')
        
        print(f"🚀 Using model: {model_id}")
        
        # Call Groq API
        response = client.chat.completions.create(
            messages=messages,
            model=model_id,
            temperature=0.3,
            max_tokens=1024
        )

        content = response.choices.message.content
        print(f"✅ Response generated: {content[:100]}...")
        
        return jsonify({
            "content": content or "Sorry, no response generated."
        })

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            "error": str(e),
            "content": "An error occurred. Please try again."
        }), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "StudyHub API is running! 🚀"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
