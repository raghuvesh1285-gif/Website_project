import os
import requests
import json
import time
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from groq import Groq

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}})
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Groq client with detailed error handling
api_key = os.environ.get("GROQ_API_KEY")
client = None

print(f"🔑 API Key present: {'Yes' if api_key else 'No'}")
print(f"🔑 API Key length: {len(api_key) if api_key else 0}")

if api_key:
    try:
        client = Groq(api_key=api_key)
        print("✅ Groq client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Groq client: {e}")
        print(f"❌ Error type: {type(e)}")

# Store active connections and browsing sessions
active_connections = []
browsing_sessions = {}

@app.route('/api/chat', methods=['POST'])
def chat():
    print("\n" + "="*50)
    print("📨 NEW CHAT REQUEST RECEIVED")
    print("="*50)
    
    if not client:
        print("❌ No Groq client available")
        return jsonify({
            "error": "API client not initialized",
            "content": "Chat service is not available. Please check server logs."
        }), 500

    try:
        # Get and log request data
        data = request.get_json()
        print(f"📋 Raw request data: {data}")
        
        if not data:
            print("❌ No JSON data received")
            return jsonify({
                "error": "No JSON data",
                "content": "Please provide valid JSON data."
            }), 400

        # Extract fields
        model_id = data.get('model', 'openai/gpt-oss-120b')
        messages = data.get('messages', [])
        
        print(f"🤖 Model ID: {model_id}")
        print(f"💬 Messages count: {len(messages)}")
        print(f"💬 Messages: {messages}")

        # Validate messages
        if not messages or not isinstance(messages, list):
            print("❌ Invalid messages format")
            return jsonify({
                "error": "Messages must be a non-empty array",
                "content": "Please provide valid messages array."
            }), 400

        # Call Groq API with detailed logging
        print(f"🚀 Calling Groq API...")
        print(f"🚀 Model: {model_id}")
        print(f"🚀 Messages: {len(messages)} items")

        try:
            chat_completion = client.chat.completions.create(
                messages=messages,
                model=model_id,
                temperature=0.7,
                max_tokens=1024
            )

            print(f"✅ API call successful!")
            print(f"📥 Response type: {type(chat_completion)}")
            print(f"📥 Response: {chat_completion}")

            # Extract content with detailed checks
            if hasattr(chat_completion, 'choices'):
                print(f"✅ Has choices attribute")
                print(f"📊 Choices count: {len(chat_completion.choices) if chat_completion.choices else 0}")
                
                if chat_completion.choices and len(chat_completion.choices) > 0:
                    first_choice = chat_completion.choices[0]
                    print(f"✅ First choice: {first_choice}")
                    
                    if hasattr(first_choice, 'message'):
                        message = first_choice.message
                        print(f"✅ Has message: {message}")
                        
                        if hasattr(message, 'content'):
                            content = message.content
                            print(f"✅ Content extracted: {content[:100]}...")
                            return jsonify({
                                "content": content or "Empty response from AI"
                            })
                        else:
                            print("❌ Message has no content attribute")
                    else:
                        print("❌ Choice has no message attribute")
                else:
                    print("❌ No choices in response")
            else:
                print("❌ Response has no choices attribute")

            print("❌ Could not extract content from response")
            return jsonify({
                "content": "AI response received but content could not be extracted."
            })

        except Exception as groq_error:
            print(f"❌ Groq API Error: {groq_error}")
            print(f"❌ Error type: {type(groq_error)}")
            print(f"❌ Error details: {str(groq_error)}")
            return jsonify({
                "error": f"AI API Error: {str(groq_error)}",
                "content": f"The AI service returned an error: {str(groq_error)}"
            }), 500

    except Exception as e:
        print(f"❌ General error: {e}")
        print(f"❌ Error type: {type(e)}")
        return jsonify({
            "error": f"Server error: {str(e)}",
            "content": "An unexpected server error occurred."
        }), 500

# NEW: Real-time browsing endpoints
@app.route('/api/browse', methods=['POST'])
def browse_url():
    """Browse a URL and return content with real-time updates"""
    print("\n" + "="*50)
    print("🌐 NEW BROWSE REQUEST RECEIVED")
    print("="*50)
    
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        session_id = data.get('session_id', str(time.time()))
        
        if not url:
            return jsonify({"error": "URL is required"}), 400
            
        print(f"🔗 URL: {url}")
        print(f"🆔 Session ID: {session_id}")
        
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme:
            url = 'https://' + url
            
        # Store browsing session
        browsing_sessions[session_id] = {
            'url': url,
            'start_time': time.time(),
            'status': 'browsing'
        }
        
        # Emit real-time status update
        socketio.emit('browse_status', {
            'session_id': session_id,
            'status': 'started',
            'url': url,
            'timestamp': time.time()
        })
        
        # Fetch webpage content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        # Parse content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract relevant content
        title = soup.find('title').get_text() if soup.find('title') else 'No Title'
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text content
        text_content = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit content size
        max_content_length = 5000
        if len(text_content) > max_content_length:
            text_content = text_content[:max_content_length] + "... [Content truncated]"
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True)[:10]:  # Limit to 10 links
            href = link['href']
            if href.startswith('http'):
                links.append({
                    'url': href,
                    'text': link.get_text().strip()[:100]
                })
            elif href.startswith('/'):
                full_url = urljoin(url, href)
                links.append({
                    'url': full_url,
                    'text': link.get_text().strip()[:100]
                })
        
        browse_result = {
            'url': url,
            'title': title,
            'status_code': response.status_code,
            'content': text_content,
            'links': links,
            'content_type': response.headers.get('content-type', ''),
            'timestamp': time.time(),
            'session_id': session_id
        }
        
        # Update session
        browsing_sessions[session_id].update({
            'status': 'completed',
            'result': browse_result
        })
        
        # Emit real-time completion update
        socketio.emit('browse_complete', {
            'session_id': session_id,
            'result': browse_result
        })
        
        print(f"✅ Browse completed successfully")
        print(f"📄 Title: {title}")
        print(f"📊 Content length: {len(text_content)} chars")
        
        return jsonify(browse_result)
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        print(f"❌ Network error: {e}")
        
        # Emit error update
        socketio.emit('browse_error', {
            'session_id': session_id if 'session_id' in locals() else 'unknown',
            'error': error_msg
        })
        
        return jsonify({"error": error_msg}), 500
        
    except Exception as e:
        error_msg = f"Browse error: {str(e)}"
        print(f"❌ Browse error: {e}")
        
        # Emit error update
        socketio.emit('browse_error', {
            'session_id': session_id if 'session_id' in locals() else 'unknown',
            'error': error_msg
        })
        
        return jsonify({"error": error_msg}), 500

@app.route('/api/chat-with-browsing', methods=['POST'])
def chat_with_browsing():
    """Enhanced chat endpoint that can browse URLs mentioned in messages"""
    print("\n" + "="*50)
    print("🤖🌐 CHAT WITH BROWSING REQUEST")
    print("="*50)
    
    if not client:
        return jsonify({
            "error": "API client not initialized",
            "content": "Chat service is not available."
        }), 500

    try:
        data = request.get_json()
        model_id = data.get('model', 'openai/gpt-oss-120b')
        messages = data.get('messages', [])
        auto_browse = data.get('auto_browse', False)
        
        # Check if last message contains URLs
        if auto_browse and messages:
            last_message = messages[-1].get('content', '')
            
            # Simple URL detection
            import re
            urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', last_message)
            
            if urls:
                print(f"🔗 Found URLs in message: {urls}")
                
                # Browse the first URL
                browse_data = {
                    'url': urls[0],
                    'session_id': f"chat_{time.time()}"
                }
                
                # Get browsing result
                browse_response = browse_url()
                if browse_response[1] == 200:  # Success
                    browse_result = json.loads(browse_response[0].data)
                    
                    # Add browsing context to messages
                    browsing_context = f"\n\n[BROWSING CONTEXT]\nURL: {browse_result['url']}\nTitle: {browse_result['title']}\nContent: {browse_result['content'][:1000]}...\n[END BROWSING CONTEXT]\n"
                    
                    messages[-1]['content'] += browsing_context
        
        # Call Groq API
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_id,
            temperature=0.7,
            max_tokens=1024
        )
        
        if hasattr(chat_completion, 'choices') and chat_completion.choices:
            content = chat_completion.choices[0].message.content
            return jsonify({"content": content or "Empty response from AI"})
        else:
            return jsonify({"content": "AI response received but content could not be extracted."})
            
    except Exception as e:
        print(f"❌ Chat with browsing error: {e}")
        return jsonify({
            "error": f"Server error: {str(e)}",
            "content": "An unexpected server error occurred."
        }), 500

# WebSocket handlers for real-time updates
@socketio.on('connect')
def on_connect():
    active_connections.append(request.sid)
    print(f"🔌 Client {request.sid} connected")
    emit('connection_status', {'status': 'connected', 'message': 'Real-time browsing enabled'})

@socketio.on('disconnect')
def on_disconnect():
    if request.sid in active_connections:
        active_connections.remove(request.sid)
    print(f"🔌 Client {request.sid} disconnected")

@socketio.on('browse_request')
def handle_browse_request(data):
    """Handle real-time browse requests via WebSocket"""
    try:
        url = data.get('url', '')
        session_id = f"ws_{request.sid}_{time.time()}"
        
        # Use the existing browse logic
        browse_data = {
            'url': url,
            'session_id': session_id
        }
        
        # Emit status update
        emit('browse_started', {'session_id': session_id, 'url': url})
        
        # Process browse request (simplified version)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title = soup.find('title').get_text() if soup.find('title') else 'No Title'
        
        # Clean content
        for script in soup(["script", "style"]):
            script.decompose()
        text_content = soup.get_text()[:2000]  # Limit for WebSocket
        
        result = {
            'session_id': session_id,
            'url': url,
            'title': title,
            'content': text_content,
            'status_code': response.status_code
        }
        
        emit('browse_result', result)
        
    except Exception as e:
        emit('browse_error', {'error': str(e), 'session_id': session_id})

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "StudyHub API with Real-time Browsing - Debug Version",
        "status": "running",
        "groq_client": "initialized" if client else "not available",
        "api_key_present": bool(api_key),
        "features": ["chat", "real-time browsing", "websockets"],
        "models": ["openai/gpt-oss-120b", "qwen", "llama4"]
    })

@app.route('/debug', methods=['GET'])
def debug():
    return jsonify({
        "groq_client_available": client is not None,
        "api_key_length": len(api_key) if api_key else 0,
        "environment_variables": list(os.environ.keys()),
        "active_connections": len(active_connections),
        "browsing_sessions": len(browsing_sessions)
    })

if __name__ == '__main__':
    print("🚀 Starting StudyHub API with Real-time Browsing (Debug Version)")
    print(f"🔧 Debug mode: ON")
    print(f"🌐 Real-time browsing: ENABLED")
    print(f"🔌 WebSocket support: ENABLED")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
