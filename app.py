from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

FAST_API_KEY = os.environ.get('API_KEY', 'sk-J9vDDHyPZfXCCf9CLNNMpnDdayVDnEDQ7AQ44siKoIu3PsaS')
OPENROUTER_API_KEY = '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'
FAST_BASE_URL = 'https://fast.typegpt.net/v1/chat/completions'
PUTER_BASE_URL = 'https://api.puter.com/chat'
OPENROUTER_URL = 'https://openrouter.ai/api/v1/chat/completions'

VALID_MODELS = [
    'deepseek-r1', 
    'gpt-4o', 
    'claude',
    'deepseek/deepseek-r1-zero:free',
    'qwen/qwq-32b:free',
    'qwen/qwen2.5-vl-72b-instruct:free',
    'deepseek/deepseek-r1-distill-qwen-32b:free',
    'deepseek/deepseek-r1:free',
    'deepseek/deepseek-chat:free',
    'google/gemini-2.0-flash-thinking-exp-1219:free',
    'qwen/qwen-2.5-coder-32b-instruct:free'
]

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

def call_openrouter(prompt, model):
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://your-site.com',  # Replace with your actual site
        'X-Title': 'AI Models Demo'  # Replace with your actual app name
    }
    
    data = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 1000
    }
    
    try:
        response = requests.post(OPENROUTER_URL, json=data, headers=headers)
        response.raise_for_status()
        return {'answer': response.json()['choices'][0]['message']['content']}
    except requests.RequestException as e:
        return {'error': f'OpenRouter API Failed: {str(e)}'}

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
        elif model in ['deepseek-r1', 'gpt-4o']:
            response = call_fast_typegpt(prompt, model)
        else:
            # All other models are handled by OpenRouter
            response = call_openrouter(prompt, model)
            
        if 'error' in response:
            # Fallback to deepseek-r1 if the chosen model fails
            return call_fast_typegpt(prompt, 'deepseek-r1')
            
        return jsonify(response)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
