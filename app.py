from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from flask_cors import CORS
import requests
import os
import uuid
import datetime
import json

app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

FAST_API_KEY = os.environ.get('API_KEY', 'sk-J9vDDHyPZfXCCf9CLNNMpnDdayVDnEDQ7AQ44siKoIu3PsaS')
FAST_BASE_URL = 'https://fast.typegpt.net/v1/chat/completions'
PUTER_BASE_URL = 'https://api.puter.com/chat'
VALID_MODELS = ['deepseek-r1', 'gpt-4o', 'claude']

# File to store API keys and their metadata
API_KEYS_FILE = 'api_keys.json'

# Load existing API keys from file or initialize if file doesn't exist
def load_api_keys():
    try:
        with open(API_KEYS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save API keys to file
def save_api_keys(api_keys):
    with open(API_KEYS_FILE, 'w') as f:
        json.dump(api_keys, f, indent=4)

# Initialize API keys
VALID_API_KEYS = load_api_keys()

def call_fast_typegpt(prompt, model):
    headers = {
        'Authorization': f'Bearer {FAST_API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 50
    }
    try:
        response = requests.post(FAST_BASE_URL, json=data, headers=headers)
        response.raise_for_status()
        return {'answer': response.json()['choices'][0]['message']['content']}
    except requests.RequestException as e:
        return {'error': f'Fast API Failed: {str(e)}'}

def call_puter_ai(prompt, model):
    headers = {
        'Content-Type': 'application/json'
    }
    data = {
        'model': model,
        'prompt': prompt,
        'stream': False
    }
    try:
        response = requests.post(PUTER_BASE_URL, json=data, headers=headers)
        response.raise_for_status()
        return {'answer': response.json().get('text', 'No response')}
    except requests.RequestException as e:
        return {'error': f'Puter API Failed: {str(e)}'}

@app.route('/api/answer', methods=['POST'])
def answer():
    user_api_key = request.headers.get('X-API-Key')
    
    # Check if API key exists and is valid
    if not user_api_key or user_api_key not in VALID_API_KEYS:
        return jsonify({'error': 'Invalid or missing API key'}), 401
    
    # Check if API key is expired
    if VALID_API_KEYS[user_api_key].get('expires_at') and \
       datetime.datetime.fromisoformat(VALID_API_KEYS[user_api_key]['expires_at']) < datetime.datetime.now():
        return jsonify({'error': 'API key has expired'}), 403
    
    # Check if API key has reached its rate limit
    if VALID_API_KEYS[user_api_key].get('daily_limit'):
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        if VALID_API_KEYS[user_api_key].get('usage', {}).get(today, 0) >= VALID_API_KEYS[user_api_key]['daily_limit']:
            return jsonify({'error': 'Daily usage limit reached'}), 429
    
    data = request.get_json()
    prompt = data.get('prompt', '')
    model = data.get('model', 'deepseek-r1')
    
    if not prompt:
        return jsonify({'error': 'Prompt required'}), 400
    
    if model not in VALID_MODELS:
        return jsonify({'error': f'Model {model} not supported. Use: {VALID_MODELS}'}), 400
    
    # Call the appropriate API based on the model
    if model == 'claude':
        response = call_puter_ai(prompt, model)
    else:
        response = call_fast_typegpt(prompt, model)
    
    # Update usage statistics
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    if 'usage' not in VALID_API_KEYS[user_api_key]:
        VALID_API_KEYS[user_api_key]['usage'] = {}
    if today not in VALID_API_KEYS[user_api_key]['usage']:
        VALID_API_KEYS[user_api_key]['usage'][today] = 0
    VALID_API_KEYS[user_api_key]['usage'][today] += 1
    
    # Save updated API keys
    save_api_keys(VALID_API_KEYS)
    
    return jsonify(response)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/api-dashboard', methods=['GET'])
def api_dashboard():
    return render_template('api_dashboard.html', api_keys=VALID_API_KEYS)

@app.route('/generate-key', methods=['GET', 'POST'])
def generate_key():
    if request.method == 'POST':
        # Get form data
        email = request.form.get('email', '')
        name = request.form.get('name', '')
        tier = request.form.get('tier', 'free')
        
        # Set limits based on tier
        if tier == 'free':
            daily_limit = 10
            expiry_days = 30
        elif tier == 'basic':
            daily_limit = 50
            expiry_days = 90
        elif tier == 'premium':
            daily_limit = 200
            expiry_days = 365
        else:  # unlimited
            daily_limit = None
            expiry_days = None
        
        # Generate expiry date if applicable
        if expiry_days:
            expires_at = (datetime.datetime.now() + datetime.timedelta(days=expiry_days)).isoformat()
        else:
            expires_at = None
        
        # Generate a new API key
        new_key = str(uuid.uuid4())
        
        # Store the key with metadata
        VALID_API_KEYS[new_key] = {
            'created_at': datetime.datetime.now().isoformat(),
            'expires_at': expires_at,
            'email': email,
            'name': name,
            'tier': tier,
            'daily_limit': daily_limit,
            'usage': {}
        }
        
        # Save updated API keys
        save_api_keys(VALID_API_KEYS)
        
        # Flash a success message
        flash('API key generated successfully!', 'success')
        
        return render_template('generate_key.html', api_key=new_key, key_data=VALID_API_KEYS[new_key])
    
    return render_template('generate_key.html', api_key=None)

@app.route('/revoke-key/<api_key>', methods=['POST'])
def revoke_key(api_key):
    if api_key in VALID_API_KEYS:
        del VALID_API_KEYS[api_key]
        save_api_keys(VALID_API_KEYS)
        flash('API key revoked successfully!', 'success')
    else:
        flash('API key not found!', 'error')
    
    return redirect(url_for('api_dashboard'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
