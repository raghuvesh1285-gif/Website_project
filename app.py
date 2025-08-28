import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# Initialize Groq Client
# This will safely fail if the API key is not set on Render
try:
    client = Groq(api_key=os.environ.get("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"))
except Exception as e:
    client = None

# Define the API endpoint that your frontend will call
@app.route('/api/chat', methods=['POST'])
def chat():
    # Check if the Groq client was initialized correctly
    if not client:
        return jsonify({"error": "Server-side error: Groq API key is not configured."}), 500

    # Get data from the frontend request
    data = request.get_json()
    model_id = data.get('model')
    messages = data.get('messages')

    # Basic validation
    if not model_id or not messages:
        return jsonify({"error": "Request is missing 'model' or 'messages'."}), 400

    # Forward the request to the Groq API
    try:
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_id
        )
        # Return only the message content, as the frontend expects
        return jsonify(chat_completion.choices[0].message.content)
    except Exception as e:
        # Return a specific error if the API call fails
        return jsonify({"error": f"Groq API Error: {str(e)}"}), 500

# This part is only for local testing. Render will use Gunicorn.
if __name__ == '__main__':
    app.run(port=5000)

