from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# API Keys and Base URLs
FAST_API_KEY = os.environ.get('API_KEY', 'sk-J9vDDHyPZfXCCf9CLNNMpnDdayVDnEDQ7AQ44siKoIu3PsaS')
FAST_BASE_URL = 'https://fast.typegpt.net/v1/chat/completions'

# Combine all models into FAST_MODELS
FAST_MODELS = [
    'deepseek-r1', 'gpt-4o', 'claude', 'evil', 'sur', 'sur-mistral', 'TirexAi',
    'unity', 'rtist', 'searchgpt', 'dify', 'HELVETE', 'HELVETE-X',
    'chatgpt-4o-latest', 'gpt-4o-mini', 'gpt-4o-2024-05-13', 'gpt-4o-2024-11-20',
    'gpt-4o-mini-2024-07-18', 'grok-2', 'gemini-pro', 'gemini-1.5-pro',
    'gemini-1.5-pro-latest', 'gemini-flash-2.0', 'gemini-1.5-flash',
    'claude-3-5-sonnet', 'claude-3-5-sonnet-20240620', 'claude-sonnet-3.5',
    'anthropic/claude-3.5-sonnet', 'deepseek-v3', 'deepseek-r1',
    'deepseek-ai/DeepSeek-R1', 'deepseek-ai/DeepSeek-V3',
    'deepseek-ai/DeepSeek-R1-Distill-Llama-70B', 'deepseek-ai/DeepSeek-R1-Distill-Qwen-32B',
    'deepseek-llm-67b-chat', 'mistral', 'mistral-large',
    'Mistral-Small-24B-Instruct-2501', 'Mistral-7B-Instruct-v0.2',
    'qwen-plus-latest', 'qwen-turbo-latest', 'qwen2.5-14b-instruct-1m',
    'qwen2.5-72b-instruct', 'qwen2.5-coder-32b-instruct', 'qwen2.5-vl-72b-instruct',
    'Qwen-QwQ-32B-Preview', 'qvq-72b-preview', 'qwq-32b-preview',
    'HelpingAI-15B', 'HelpingAI-flash', 'HelpingAI2-6B', 'HelpingAI2-9B',
    'HelpingAI2.5-10B', 'HelpingAI2.5-2B', 'HelpingAI2.5-5B',
    'c4ai-aya-23-35b', 'c4ai-aya-23-8b', 'dbrx-instruct',
    'llama-3.1-405b', 'llama-3.1-70b', 'llama-3.1-8b', 'llama3.1-8b',
    'Meta-Llama-3.1-405B-Instruct-Turbo', 'Meta-Llama-3.3-70B-Instruct-Turbo',
    'Niansuh', 'niansuh-t1', 'o3-mini', 'RepoMap',
    # Adding CF models
    '@cf/deepseek-ai/deepseek-math-7b-base', '@cf/deepseek-ai/deepseek-math-7b-instruct',
    '@cf/defog/sqlcoder-7b-2', '@cf/google/gemma-2b-it-lora', '@cf/google/gemma-7b-it-lora',
    '@cf/meta-llama/llama-2-7b-chat-hf-lora', '@cf/meta/llama-2-7b-chat-fp16',
    '@cf/meta/llama-2-7b-chat-int8', '@cf/meta/llama-3-8b-instruct',
    '@cf/meta/llama-3.1-8b-instruct', '@cf/microsoft/phi-2',
    '@cf/mistral/mistral-7b-instruct-v0.1', '@cf/mistral/mistral-7b-instruct-v0.2-lora',
    '@cf/openchat/openchat-3.5-0106', '@cf/qwen/qwen1.5-0.5b-chat',
    '@cf/qwen/qwen1.5-1.8b-chat', '@cf/qwen/qwen1.5-14b-chat-awq',
    '@cf/qwen/qwen1.5-7b-chat-awq', '@cf/thebloke/discolm-german-7b-v1-awq',
    '@cf/tiiuae/falcon-7b-instruct', '@cf/tinyllama/tinyllama-1.1b-chat-v1.0',
    # Adding HF models
    '@hf/google/gemma-7b-it', '@hf/mistralai/mistral-7b-instruct-v0.2',
    '@hf/nexusflow/starling-lm-7b-beta', '@hf/nousresearch/hermes-2-pro-mistral-7b',
    '@hf/thebloke/deepseek-coder-6.7b-base-awq', '@hf/thebloke/deepseek-coder-6.7b-instruct-awq',
    '@hf/thebloke/llama-2-13b-chat-awq', '@hf/thebloke/llamaguard-7b-awq',
    '@hf/thebloke/mistral-7b-instruct-v0.1-awq', '@hf/thebloke/neural-chat-7b-v3-1-awq',
    '@hf/thebloke/openhermes-2.5-mistral-7b-awq', '@hf/thebloke/zephyr-7b-beta-awq'
]

VALID_MODELS = FAST_MODELS

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
        return {'error': f'Fast TypeGPT API Failed: {str(e)}'}

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
        return jsonify(call_fast_typegpt(prompt, model))
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
