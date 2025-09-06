import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from datetime import datetime
import requests
import yfinance as yf
import re

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

def perform_comprehensive_search(query):
    """
    Comprehensive search function that handles multiple domains:
    - Current events & news
    - Technology updates  
    - Sports scores & results
    - Weather information
    - Stock prices
    - General information
    """
    try:
        # Detect query type
        query_lower = query.lower()
        
        # Stock/Finance queries
        if any(word in query_lower for word in ['stock', 'price', 'nvidia', 'apple', 'tesla', 'microsoft', 'google', 'share', 'market']):
            return get_stock_data(query)
        
        # News/Current events queries  
        elif any(word in query_lower for word in ['news', 'latest', 'current', 'recent', 'today', 'happened', 'breaking']):
            return get_news_data(query)
        
        # Sports queries
        elif any(word in query_lower for word in ['score', 'match', 'game', 'football', 'cricket', 'basketball', 'soccer']):
            return get_sports_data(query)
        
        # Weather queries
        elif any(word in query_lower for word in ['weather', 'temperature', 'rain', 'sunny', 'forecast']):
            return get_weather_data(query)
        
        # Technology/AI queries
        elif any(word in query_lower for word in ['ai', 'artificial intelligence', 'machine learning', 'technology', 'update', 'release']):
            return get_tech_news(query)
        
        # General web search
        else:
            return get_general_search(query)
            
    except Exception as e:
        return f"Search error: {str(e)}"

def get_stock_data(query):
    """Get real-time stock data"""
    try:
        symbols_map = {
            'nvidia': 'NVDA', 'nvda': 'NVDA',
            'apple': 'AAPL', 'aapl': 'AAPL', 
            'tesla': 'TSLA', 'tsla': 'TSLA',
            'microsoft': 'MSFT', 'msft': 'MSFT',
            'google': 'GOOGL', 'googl': 'GOOGL',
            'meta': 'META', 'facebook': 'META',
            'amazon': 'AMZN', 'amzn': 'AMZN'
        }
        
        stock_symbol = None
        for key, value in symbols_map.items():
            if key in query.lower():
                stock_symbol = value
                break
        
        if stock_symbol:
            stock = yf.Ticker(stock_symbol)
            info = stock.info
            hist = stock.history(period="1d")
            
            current_price = hist['Close'].iloc[-1] if not hist.empty else info.get('currentPrice', 'N/A')
            
            return f"""
REAL-TIME STOCK DATA for {stock_symbol}:
Current Price: ${current_price:.2f}
52-Week High: ${info.get('fiftyTwoWeekHigh', 'N/A')}
52-Week Low: ${info.get('fiftyTwoWeekLow', 'N/A')}  
Market Cap: ${info.get('marketCap', 'N/A'):,}
P/E Ratio: {info.get('trailingPE', 'N/A')}
Company: {info.get('longName', stock_symbol)}
Last Updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p EST')}
"""
        return get_general_search(query)
    except:
        return get_general_search(query)

def get_news_data(query):
    """Get current news using NewsAPI or similar"""
    try:
        # Using NewsAPI (free tier available)
        api_key = os.environ.get("NEWS_API_KEY")  # Add this to your environment
        if api_key:
            url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={api_key}"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            news_items = []
            for article in data.get('articles', [])[:5]:
                news_items.append(f"• {article['title']} - {article['source']['name']} ({article['publishedAt'][:10]})")
            
            return f"LATEST NEWS:\n" + "\n".join(news_items)
        else:
            return get_general_search(query)
    except:
        return get_general_search(query)

def get_sports_data(query):
    """Get sports scores and results"""
    try:
        # Using ESPN or similar sports API
        return get_general_search(f"latest {query} scores results")
    except:
        return get_general_search(query)

def get_weather_data(query):
    """Get weather information"""
    try:
        # Using OpenWeatherMap API
        api_key = os.environ.get("WEATHER_API_KEY")  # Add this to environment
        if api_key:
            # Extract city from query (basic implementation)
            city = "London"  # Default or extract from query
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=5)
            data = response.json()
            
            return f"""
CURRENT WEATHER for {city.title()}:
Temperature: {data['main']['temp']}°C
Feels like: {data['main']['feels_like']}°C  
Condition: {data['weather'][0]['description'].title()}
Humidity: {data['main']['humidity']}%
Wind Speed: {data['wind']['speed']} m/s
Updated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}
"""
        return get_general_search(query)
    except:
        return get_general_search(query)

def get_tech_news(query):
    """Get technology and AI news"""
    try:
        # Search for tech-specific sources
        search_query = f"{query} site:techcrunch.com OR site:theverge.com OR site:arstechnica.com"
        return get_general_search(search_query)
    except:
        return get_general_search(query)

def get_general_search(query):
    """Fallback general web search using multiple sources"""
    try:
        # Try SerpAPI if available (most comprehensive)
        serpapi_key = os.environ.get("SERPAPI_KEY")
        if serpapi_key:
            import serpapi
            search = serpapi.GoogleSearch({
                "q": query,
                "api_key": serpapi_key,
                "num": 5
            })
            results = search.get_dict()
            
            search_items = []
            for result in results.get("organic_results", [])[:5]:
                search_items.append(f"• {result.get('title')} - {result.get('snippet')} (Source: {result.get('link')})")
            
            return f"WEB SEARCH RESULTS:\n" + "\n".join(search_items)
        
        # Fallback to DuckDuckGo
        else:
            url = f"https://api.duckduckgo.com/?q={query}&format=json&no_html=1"
            resp = requests.get(url, timeout=5)
            data = resp.json()
            
            results = []
            if data.get('Abstract'):
                results.append(f"Summary: {data['Abstract']}")
            
            for topic in data.get('RelatedTopics', [])[:5]:
                if isinstance(topic, dict) and 'Text' in topic:
                    results.append(f"• {topic['Text']}")
            
            return f"SEARCH RESULTS:\n" + "\n".join(results) if results else "No current information found."
            
    except Exception as e:
        return f"Unable to fetch current information: {str(e)}"

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

        if is_browsing:
            # Extract user query
            user_query = ""
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_query = msg.get('content', '')
                    break
            
            # Perform comprehensive search across all domains
            web_results = perform_comprehensive_search(user_query)
            current_date = datetime.now().strftime("%B %d, %Y at %I:%M %p EST")
            
            # Create enhanced system prompt with search results
            enhanced_prompt = f"""{messages[0]['content']}

CURRENT INFORMATION (Retrieved: {current_date}):
{web_results}

Instructions:
- Use this current information to provide accurate, up-to-date responses
- Always cite sources and mention when information was last updated
- If the search results don't contain relevant information, clearly state that
- For financial data, include disclaimers about market volatility
- For news, mention the publication date and source reliability"""
            
            # Update the system message with enhanced context
            messages[0]['content'] = enhanced_prompt

        # Call Groq API with all models supporting enhanced search
        chat_completion = client.chat.completions.create(
            messages=messages,
            model=model_id,
            temperature=0.7,
            max_tokens=1500
        )

        response_content = chat_completion.choices[0].message.content
        return jsonify({"content": response_content})

    except Exception as e:
        return jsonify({"error": f"Groq API Error: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
