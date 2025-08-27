 import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app)

try:
    client = Groq(api_key=os.environ.get("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"))
except Exception as e:
    client = None

@app.route('/api/chat', methods=['POST'])
def chat():
    if not client:
        return jsonify({"error": "Groq client not initialized. Check API key on the server."}), 500

    data = request.get_json()
    model = data.get('model')
    messages = data.get('messages')

    if not model or not messages:
        return jsonify({"error": "Missing model or messages in request"}), 400

    try:
        chat_completion = client.chat.completions.create(messages=messages, model=model)
        return jsonify(chat_completion.choices[0].message)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000)