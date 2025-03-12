from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os
from openai import OpenAI

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# API Keys and Base URLs
FAST_API_KEY = os.environ.get('API_KEY', 'sk-J9vDDHyPZfXCCf9CLNNMpnDdayVDnEDQ7AQ44siKoIu3PsaS')
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY', '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')
FAST_BASE_URL = 'https://fast.typegpt.net/v1/chat/completions'
PUTER_BASE_URL = 'https://api.puter.com/chat'

# Initialize OpenAI client for OpenRouter
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
    default_headers={
        "HTTP-Referer": "https://api-provider-b5s7.onrender.com",  # Required for OpenRouter
        "X-Title": "AI Models Demo"  # Optional
    }
)

# Group models by their API provider
FAST_MODELS = ['deepseek-r1', 'gpt-4o']
PUTER_MODELS = ['claude']
OPENROUTER_MODELS = [
    'deepseek/deepseek-r1-zero:free',
    'qwen/qwq-32b:free',
    'qwen/qwen2.5-vl-72b-instruct:free',
    'deepseek/deepseek-r1-distill-qwen-32b:free',
    'deepseek/deepseek-r1:free',
    'deepseek/deepseek-chat:free',
    'google/gemini-2.0-flash-thinking-exp-1219:free',
    'qwen/qwen-2.5-coder-32b-instruct:free'
]

VALID_MODELS = FAST_MODELS + PUTER_MODELS + OPENROUTER_MODELS

def call_fast_typegpt(prompt, model):
    if model not in FAST_MODELS:
        return {'error': 'Invalid model for Fast TypeGPT API'}
        
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
        return {'error': f'Fast TypeGPT API Failed: {str(e)}'}

def call_puter_ai(prompt, model):
    if model not in PUTER_MODELS:
        return {'error': 'Invalid model for Puter AI'}
        
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
    if model not in OPENROUTER_MODELS:
        return {'error': 'Invalid model for OpenRouter API'}
    
    try:
        completion = openrouter_client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=1000,
            temperature=0.7
        )
        return {'answer': completion.choices[0].message.content}
    except Exception as e:
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
        # Route to correct API based on model
        if model in OPENROUTER_MODELS:
            return jsonify(call_openrouter(prompt, model))
        elif model in PUTER_MODELS:
            return jsonify(call_puter_ai(prompt, model))
        elif model in FAST_MODELS:
            return jsonify(call_fast_typegpt(prompt, model))
        else:
            return jsonify({'error': 'Invalid model selection'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
