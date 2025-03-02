from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)
API_KEY = os.environ.get('API_KEY', 'sk-J9vDDHyPZfXCCf9CLNNMpnDdayVDnEDQ7AQ44siKoIu3PsaS')
BASE_URL = 'https://fast.typegpt.net/v1/chat/completions'

def call_fast_typegpt(prompt):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'deepseek-r1',
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
    if not prompt:
        return jsonify({'error': 'Prompt required'}), 400
    response = call_fast_typegpt(prompt)
    return jsonify(response)

# Add a root route to avoid "Not Found" on the base URL
@app.route('/')
def home():
    return "Welcome to My API! Use /api/answer to send a prompt."

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
