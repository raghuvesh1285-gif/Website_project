import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from datetime import datetime
import requests

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

def perform_web_search(query):
    """Simple web search using DuckDuckGo API"""
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        
        results = []
        if data.get('Abstract'):
            results.append(f"Summary: {data['Abstract']}")
        
        for topic in data.get('RelatedTopics', [])[:3]:
            if isinstance(topic, dict) and 'Text' in topic:
                results.append(f"• {topic['Text']}")
        
        return "\n".join(results) if results else "No current information found."
    except:
        return "Web search temporarily unavailable."

@app.route('/api/chat', methods=['POST'])
def chat():
    if not client:
        return jsonify({"error": "Groq API key not configured or invalid on server."}), 500

    data = request.get_json()
    model_id = data.get('model')
    messages = data.get('messages')

    if not model_id or not messages:
        return jsonify({"error": "Request missing model or messages."}), 400

    try:
        # Check if browsing mode is enabled
        is_browsing = False
        for msg in messages:
            if (msg.get('role') == 'system' and 
                'real-time web browsing' in msg.get('content', '').lower()):
                is_browsing = True
                break

        # If browsing is enabled, enhance with web search
        if is_browsing:
            # Extract user query
            user_query = ""
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_query = msg.get('content', '')
                    break
            
            # Perform web search
            web_results = perform_web_search(user_query)
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Create enhanced system prompt with web results
            enhanced_prompt = f"""{messages[0]['content']}

CURRENT INFORMATION (Date: {current_date}):
{web_results}

Use this current information to provide accurate, up-to-date responses. Cite sources when relevant."""
            
            # Update the system message with web results
            messages[0]['content'] = enhanced_prompt

        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_id,
            temperature=0.7,
            max_tokens=1024
        )

        response_content = chat_completion.choices[0].message.content
        return jsonify({"content": response_content})

    except Exception as e:
        return jsonify({"error": f"Groq API Error: {str(e)}"}), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "StudyHub API is running! 🚀"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
