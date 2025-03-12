from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
import json
import uuid

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

FAST_API_KEY = os.environ.get('API_KEY', 'sk-J9vDDHyPZfXCCf9CLNNMpnDdayVDnEDQ7AQ44siKoIu3PsaS')
FAST_BASE_URL = 'https://fast.typegpt.net/v1/chat/completions'
PUTER_BASE_URL = 'https://api.puter.com/chat'
BLACKBOX_URL = 'https://www.blackbox.ai/api/chat'  # You'll need to verify this URL
VALID_MODELS = ['deepseek-r1', 'gpt-4o', 'claude', 'claude-sonnet']

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

def call_blackbox_ai(prompt, model="Claude-sonnet-3.7"):
    headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://www.blackbox.ai',
        'Referer': 'https://www.blackbox.ai/chat',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'en-US,en;q=0.9',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'Connection': 'keep-alive'
    }
    
    message_id = str(uuid.uuid4())
    conversation_id = str(uuid.uuid4())
    
    data = {
        "messages": [{"id": message_id, "content": prompt, "role": "user"}],
        "conversation_id": conversation_id,
        "stream": False,
        "model": model,
        "max_tokens": 1024,
        "temperature": 0.7
    }
    
    try:
        response = requests.post(BLACKBOX_URL, json=data, headers=headers)
        response.raise_for_status()
        
        return {'answer': response.json().get('response', 'No response')}
    except requests.RequestException as e:
        # Fallback to Claude via Puter if Blackbox fails
        return call_puter_ai(prompt, "claude")

@app.route('/')
def home():
    return render_template('home.html', models=VALID_MODELS)

@app.route('/api/answer', methods=['POST', 'GET'])
def answer():
    if request.method == 'GET':
        return jsonify({'message': 'Please use POST method with prompt and model in JSON body'})
    
    data = request.get_json()
    prompt = data.get('prompt', '')
    model = data.get('model', 'deepseek-r1')
    
    if not prompt:
        return jsonify({'error': 'Prompt required'}), 400
    if model not in VALID_MODELS:
        return jsonify({'error': f'Model {model} not supported. Use: {VALID_MODELS}'}), 400
    
    try:
        if model == 'claude':
            response = call_puter_ai(prompt, model)
        elif model == 'claude-sonnet':
            response = call_blackbox_ai(prompt)
        else:
            response = call_fast_typegpt(prompt, model)
        
        if 'error' in response:
            # If the primary model fails, fallback to deepseek-r1
            return call_fast_typegpt(prompt, 'deepseek-r1')
            
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
