import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# Securely load the API key from environment variables
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
        # --- ADD PARAMETERS HERE TO CONTROL THE RESPONSE ---
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_id,
            temperature=0.5,  # Lower temperature for more focused answers
            max_completion_tokens=150  # Limit the response to ~150 tokens
        )
        # -----------------------------------------------------

        # Return only the message content
        return jsonify({"content": chat_completion.choices.message.content})
    except Exception as e:
        return jsonify({"error": f"Groq API Error: {str(e)}"}), 500

# This part is only for local testing. Render will use Gunicorn.
if __name__ == '__main__':
    app.run(port=5000)
