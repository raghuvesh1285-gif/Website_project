import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from datetime import datetime
import requests
import subprocess
import tempfil
from pathlib import Path

@app.route('/api/compile-java', methods=['POST'])
def compile_java():
    try:
        data = request.get_json()
        java_code = data.get('code', '')
        
        if not java_code.strip():
            return jsonify({'error': 'No code provided'})
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write Java code to file
            java_file = os.path.join(temp_dir, 'Main.java')
            with open(java_file, 'w') as f:
                f.write(java_code)
            
            # Compile Java code
            compile_process = subprocess.run(
                ['javac', java_file],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=temp_dir
            )
            
            if compile_process.returncode != 0:
                return jsonify({
                    'error': compile_process.stderr or 'Compilation failed'
                })
            
            # Run Java code
            run_process = subprocess.run(
                ['java', 'Main'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=temp_dir
            )
            
            if run_process.returncode != 0:
                return jsonify({
                    'error': f"Runtime Error:\n{run_process.stderr}"
                })
            
            return jsonify({
                'output': run_process.stdout,
                'success': True
            })
            
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Code execution timed out (10 seconds limit)'})
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'})


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
    """Simple web search using DuckDuckGo API (free)"""
    try:
        url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
        resp = requests.get(url, timeout=5)
        data = resp.json()
        
        results = []
        # Get abstract if available
        if data.get('Abstract'):
            results.append(f"Summary: {data['Abstract']}")
        
        # Get related topics
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
        # Check if browsing mode is enabled by looking for the specific system prompt
        is_browsing = False
        for msg in messages:
            if (msg.get('role') == 'system' and 
                'real-time web browsing' in msg.get('content', '').lower()):
                is_browsing = True
                break

        # If browsing is enabled, enhance ALL models with web search
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

        # Call Groq API - now ALL models get web search when browsing is enabled
        if is_browsing and model_id == "openai/gpt-oss-120b":
            # For GPT, use your existing method with tools if needed
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=model_id,
                temperature=0.7,
                max_tokens=1024,
                tools=[{"type": "browser_search"}] if is_browsing else None,
                tool_choice="auto" if is_browsing else None
            )
        else:
            # For Qwen and Llama4, use enhanced prompt method
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

