import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# Securely load the API key
api_key = os.environ.get("GROQ_API_KEY")

client = None
if api_key:
    try:
        client = Groq(api_key=api_key)
    except Exception as e:
        print(f"Failed to initialize Groq client: {e}")

@app.route('/api/chat', methods=['POST'])
def chat():
    if not client:
        return jsonify({"error": "Groq API key not configured or invalid on the server."}), 500

    data = request.get_json()
    model_id = data.get('model')
    messages = data.get('messages')

    if not model_id or not messages:
        return jsonify({"error": "Request is missing model or messages."}), 400

    try:
        # Call the API with parameters for more concise answers
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_id,
            temperature=0.7,  # A balance between creative and focused
            max_tokens=1024   # A reasonable limit to prevent overly long answers
        )
        
        response_content = chat_completion.choices[0].message.content
        return jsonify({"content": response_content})
    except Exception as e:
        return jsonify({"error": f"Groq API Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5000)
