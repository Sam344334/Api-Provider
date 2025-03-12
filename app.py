<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Models Demo</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .chat-container {
            border: 1px solid #ccc;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        .input-group {
            margin-bottom: 15px;
        }
        select, textarea, button {
            width: 100%;
            padding: 8px;
            margin: 5px 0;
            border-radius: 4px;
            border: 1px solid #ccc;
        }
        select {
            background-color: white;
        }
        select optgroup {
            font-weight: bold;
        }
        button {
            background-color: #4CAF50;
            color: white;
            border: none;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        #response {
            white-space: pre-wrap;
            background-color: #f9f9f9;
            padding: 15px;
            border-radius: 4px;
            margin-top: 15px;
        }
        .loading {
            display: none;
            color: #666;
            font-style: italic;
        }
    </style>
</head>
<body>
    <h1>AI Models Demo</h1>
    <div class="chat-container">
        <div class="input-group">
            <label for="model">Select Model:</label>
            <select id="model">
                <optgroup label="Fast TypeGPT Models">
                    <option value="deepseek-r1">DeepSeek-R1</option>
                    <option value="gpt-4o">GPT-4O</option>
                </optgroup>
                <optgroup label="Puter AI Models">
                    <option value="claude">Claude</option>
                </optgroup>
                <optgroup label="OpenRouter Models">
                    <option value="deepseek/deepseek-r1-zero:free">DeepSeek R1 Zero</option>
                    <option value="qwen/qwq-32b:free">Qwen 32B</option>
                    <option value="qwen/qwen2.5-vl-72b-instruct:free">Qwen 2.5 VL 72B</option>
                    <option value="deepseek/deepseek-r1-distill-qwen-32b:free">DeepSeek R1 Distill Qwen</option>
                    <option value="deepseek/deepseek-r1:free">DeepSeek R1</option>
                    <option value="deepseek/deepseek-chat:free">DeepSeek Chat</option>
                    <option value="google/gemini-2.0-flash-thinking-exp-1219:free">Gemini 2.0 Flash</option>
                    <option value="qwen/qwen-2.5-coder-32b-instruct:free">Qwen 2.5 Coder</option>
                </optgroup>
            </select>
        </div>
        <div class="input-group">
            <label for="prompt">Enter your prompt:</label>
            <textarea id="prompt" rows="4" placeholder="Type your message here..."></textarea>
        </div>
        <button onclick="sendMessage()">Send Message</button>
        <div id="loading" class="loading">Processing request...</div>
        <div id="response"></div>
    </div>

    <script>
        async function sendMessage() {
            const prompt = document.getElementById('prompt').value;
            const model = document.getElementById('model').value;
            const responseDiv = document.getElementById('response');
            const loadingDiv = document.getElementById('loading');

            if (!prompt.trim()) {
                alert('Please enter a prompt');
                return;
            }

            loadingDiv.style.display = 'block';
            responseDiv.textContent = '';

            try {
                const response = await fetch('https://api-provider-b5s7.onrender.com/api/answer', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        prompt: prompt,
                        model: model
                    })
                });

                const data = await response.json();
                
                if (data.error) {
                    responseDiv.textContent = `Error: ${data.error}`;
                } else {
                    responseDiv.textContent = data.answer;
                }
            } catch (error) {
                responseDiv.textContent = `Error: ${error.message}`;
            } finally {
                loadingDiv.style.display = 'none';
            }
        }
    </script>
</body>
</html>
