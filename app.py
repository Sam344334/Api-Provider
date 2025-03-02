from flask import Flask, request, jsonify
import requests

app = Flask(__name__)  # This starts your website
API_KEY = 'sk-J9vDDHyPZfXCCf9CLNNMpnDdayVDnEDQ7AQ44siKoIu3PsaS'  # Your key
BASE_URL = 'https://fast.typegpt.net/v1/chat/completions'  # Guessing this endpoint

def call_fast_typegpt(prompt):
    headers = {
        'Authorization': f'Bearer {API_KEY}',  # This proves it’s you
        'Content-Type': 'application/json'    # Tells it we’re sending JSON
    }
    data = {
        'model': 'deepseek-r1',              # The AI model (might need adjusting)
        'messages': [{'role': 'user', 'content': prompt}],  # Your question
        'max_tokens': 50                     # Limits answer length
    }
    try:
        response = requests.post(BASE_URL, json=data, headers=headers)  # Send to API
        response.raise_for_status()  # Check for errors
        return response.json()  # Get the answer
    except requests.RequestException as e:
        return {'error': f'Oops, failed: {str(e)}'}  # If it breaks

@app.route('/api/answer', methods=['POST'])  # Your API address
def answer():
    data = request.get_json()  # Get the prompt from you
    prompt = data.get('prompt', '')
    if not prompt:
        return jsonify({'error': 'Give me a prompt!'}), 400  # No prompt, no go
    response = call_fast_typegpt(prompt)  # Ask the AI
    return jsonify(response)  # Send back the answer

if __name__ == '__main__':
    app.run(debug=True)  # Runs your website locally