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
        # Check if deep research mode is enabled in the system prompt
        is_deep_research = any("deep research agent" in message.get("content", "").lower() for message in messages if message.get("role") == "system")
        
        # --- DEFINITIVE FIX FOR REAL-TIME BROWSING ---
        if is_deep_research:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model="openai/gpt-oss-120b",
                temperature=0.7,
                max_tokens=2048,
                tools=[{"type": "browser_search"}],
                tool_choice="auto"  # Change from "required" to "auto"
            )
        else:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=model_id,
                temperature=0.7,
                max_tokens=1024
            )
        # ---------------------------------------------
        
        response_content = chat_completion.choices[0].message.content
        return jsonify({"content": response_content})
    except Exception as e:
        return jsonify({"error": f"Groq API Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=5000)
