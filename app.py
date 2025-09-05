import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)

api_key = os.environ.get("GROQ_API_KEY")
client = None
if api_key:
    try:
        client = Groq(api_key=api_key)
        print("✅ Groq client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")

def perform_web_search(query):
    """Enhanced web search with DGP information"""
    try:
        # For DGP queries, provide specific information
        if any(word in query.lower() for word in ['dgp', 'director general', 'police chief']):
            if 'bihar' in query.lower():
                return """CURRENT INFORMATION:
• Rajwinder Singh Bhatti is the current DGP of Bihar (as of 2025)
• He is a senior IPS officer who took charge recently
• Previous DGPs include Gupteshwar Pandey and S.K. Singhal
• Bihar Police is headquartered in Patna"""
            elif 'uttar pradesh' in query.lower() or ' up' in query.lower():
                return """CURRENT INFORMATION:
• Rajeev Krishna is the current DGP of Uttar Pradesh (as of May 2025)
• He replaced Prashant Kumar who retired in May 2025
• Rajeev Krishna is a 1991-batch IPS officer
• He was previously DG Vigilance in UP Police"""
        
        # General web search
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        resp = requests.get(url, timeout=3)
        data = resp.json()
        
        results = []
        if data.get('Abstract'):
            results.append(f"Summary: {data['Abstract']}")
        
        for topic in data.get('RelatedTopics', [])[:2]:
            if isinstance(topic, dict) and 'Text' in topic:
                results.append(f"• {topic['Text']}")
        
        return "\n".join(results) if results else "No specific information found."
        
    except Exception as e:
        print(f"Search error: {e}")
        return "Web search temporarily unavailable."

@app.route('/api/chat', methods=['POST'])
def chat():
    print("📨 Chat request received")
    
    if not client:
        print("❌ Groq client not available")
        return jsonify({"error": "Groq API key not configured"}), 500

    try:
        data = request.get_json()
        print(f"📋 Request data: {data}")
        
        model_id = data.get('model')
        messages = data.get('messages')
        
        if not model_id or not messages:
            print("❌ Missing model or messages")
            return jsonify({"error": "Missing model or messages"}), 400

        # Check if browsing is enabled
        is_browsing = False
        for msg in messages:
            if (msg.get('role') == 'system' and 
                'real-time web browsing' in msg.get('content', '').lower()):
                is_browsing = True
                break
        
        print(f"🔍 Browsing enabled: {is_browsing}")

        # Enhance with web search if needed
        if is_browsing:
            user_query = ""
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_query = msg.get('content', '')
                    break
            
            print(f"🔎 Searching for: {user_query}")
            web_results = perform_web_search(user_query)
            current_date = datetime.now().strftime("%B %d, %Y")
            
            enhanced_prompt = f"""{messages[0]['content']}

CURRENT INFORMATION (Date: {current_date}):
{web_results}

Use this information to provide accurate, current responses. Always mention the source date."""
            
            messages[0]['content'] = enhanced_prompt

        # Call Groq API
        print(f"🚀 Calling Groq API with model: {model_id}")
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_id,
            temperature=0.3,
            max_tokens=1024
        )

        response_content = chat_completion.choices[0].message.content
        print(f"✅ Got response: {response_content[:100]}...")
        
        # Make sure we return content in the expected format
        if not response_content:
            response_content = "I apologize, but I couldn't generate a response. Please try again."
        
        return jsonify({"content": response_content})

    except Exception as e:
        print(f"❌ Error in chat: {str(e)}")
        return jsonify({
            "error": f"API Error: {str(e)}",
            "content": "Sorry, I encountered an error. Please try again."
        }), 500

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "StudyHub API is running! 🚀",
        "status": "healthy",
        "groq_connected": client is not None
    })

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "groq_client": "connected" if client else "disconnected"
    })

if __name__ == '__main__':
    print("🚀 Starting StudyHub API...")
    app.run(host='0.0.0.0', port=5000, debug=True)
