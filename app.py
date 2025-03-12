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
        'Referer': 'https://www.blackbox.ai/chat'
    }
    
    message_id = str(uuid.uuid4())[:7]
    
    data = {
        "messages": [{"id": message_id, "content": prompt, "role": "user"}],
        "agentMode": {
            "name": model,
            "id": model,
            "mode": True
        },
        "userId": None,
        "userSystemPrompt": None,
        "isChromeExt": False,
        "isPremium": True,
        "maxTokens": 1024,
        "validated": str(uuid.uuid4()),
        "codeModelMode": True
    }
    
    try:
        response = requests.post(BLACKBOX_URL, json=data, headers=headers)
        response.raise_for_status()
        
        # Parse the streaming response or regular response
        answer = response.json().get('content', 'No response')
        return {'answer': answer}
    except requests.RequestException as e:
        return {'error': f'BlackBox AI Failed: {str(e)}'}

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
    
    if model == 'claude':
        response = call_puter_ai(prompt, model)
    elif model == 'claude-sonnet':
        response = call_blackbox_ai(prompt)
    else:
        response = call_fast_typegpt(prompt, model)
    
    return jsonify(response)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
