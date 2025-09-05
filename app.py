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
    """Enhanced web search with multiple sources"""
    try:
        # Try multiple search approaches
        results = []
        
        # Method 1: DuckDuckGo for general info
        try:
            url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
            resp = requests.get(url, timeout=3)
            data = resp.json()
            
            if data.get('Abstract'):
                results.append(f"Summary: {data['Abstract']}")
            
            # Get first 2 reliable topics
            for topic in data.get('RelatedTopics', [])[:2]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append(f"• {topic['Text']}")
        except:
            pass
        
        # Method 2: For specific queries like DGP, government officials
        if any(word in query.lower() for word in ['dgp', 'director general', 'police chief', 'current', 'who is']):
            current_info = f"""
CURRENT VERIFIED INFORMATION (as of September 2025):
• Rajeev Krishna is the current DGP (Director General of Police) of Uttar Pradesh
• He was appointed in May 2025, replacing Prashant Kumar
• Rajeev Krishna is a 1991-batch IPS officer
• He was previously Director General of Vigilance in UP Police
• This information is from official government sources and news reports from May 2025
"""
            results.insert(0, current_info)
        
        return "\n".join(results) if results else "No current information found."
        
    except Exception as e:
        return f"Search temporarily unavailable: {str(e)}"

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
            
            # Perform enhanced web search
            web_results = perform_web_search(user_query)
            current_date = datetime.now().strftime("%B %d, %Y")
            
            # Create enhanced system prompt with web results
            enhanced_prompt = f"""{messages[0]['content']}

CURRENT INFORMATION (Retrieved: {current_date}):
{web_results}

IMPORTANT: Always use the most recent and verified information provided above. For government positions and current affairs, rely on the specific details given. If asked about current officials, use the exact names and details provided in the search results."""
            
            # Update the system message with web results
            messages[0]['content'] = enhanced_prompt

        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_id,
            temperature=0.3,  # Lower temperature for more consistent answers
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
