from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)  # For your website
API_KEY = os.environ.get('API_KEY', 'sk-J9vDDHyPZfXCCf9CLNNMpnDdayVDnEDQ7AQ44siKoIu3PsaS')
BASE_URL = 'https://fast.typegpt.net/v1/chat/completions'
VALID_MODELS = ['deepseek-r1', 'gpt-4o']  # Available models

def call_fast_typegpt(prompt, model):
    if model not in VALID_MODELS:
        return {'error': f'Model {model} not supported. Use: {VALID_MODELS}'}
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': model,  # Use the selected model
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 50
    }
    try:
        response = requests.post(BASE_URL, json=data, headers=headers)
        response.raise_for_status()
        return {'answer': response.json()['choices'][0]['message']['content']}
    except requests.RequestException as e:
        return {'error': f'Failed: {str(e)}'}

@app.route('/api/answer', methods=['POST'])
def answer():
    data = request.get_json()
    prompt = data.get('prompt', '')
    model = data.get('model', 'deepseek-r1')  # Default to deepseek-r1 if not specified
    if not prompt:
        return jsonify({'error': 'Prompt required'}), 400
    response = call_fast_typegpt(prompt, model)
    return jsonify(response)

@app.route('/')
def home():
    return f"Welcome to My API! Use /api/answer with prompt and model ({VALID_MODELS})."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
