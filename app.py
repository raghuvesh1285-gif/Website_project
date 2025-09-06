import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*", "methods": ["GET", "POST", "OPTIONS"]}})

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

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "StudyHub API - Debug Version",
        "status": "running",
        "groq_client": "initialized" if client else "not available",
        "api_key_present": bool(api_key)
    })

@app.route('/debug', methods=['GET'])
def debug():
    return jsonify({
        "groq_client_available": client is not None,
        "api_key_length": len(api_key) if api_key else 0,
        "environment_variables": list(os.environ.keys())
    })

if __name__ == '__main__':
    print("🚀 Starting StudyHub API (Debug Version)")
    print(f"🔧 Debug mode: ON")
    app.run(host='0.0.0.0', port=5000, debug=True)
