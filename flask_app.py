#!/usr/bin/env python3
"""
Flask Web App for Emergency Navigator
Backend service that connects to your deployed Vertex AI reasoning engine.
"""

import os
import sys
from flask import Flask, render_template_string, request, jsonify
from flask_cors import CORS
import google.auth
import vertexai
from vertexai import agent_engines

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Configuration
PROJECT_ID = "qwiklabs-gcp-01-2a76b8f0c7a6"
ENGINE_ID = "3001143376293658624"
LOCATION = "us-central1"

# Initialize Vertex AI
vertexai.init(project=PROJECT_ID, location=LOCATION)

# Get the reasoning engine
engine_resource = f"projects/{PROJECT_ID}/locations/{LOCATION}/reasoningEngines/{ENGINE_ID}"
reasoning_engine = agent_engines.get(engine_resource)

print(f"✅ Connected to reasoning engine: {engine_resource}")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Emergency Navigator - Live App</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .emergency-banner {
            background: #ffebee;
            border: 3px solid #f44336;
            padding: 20px;
            margin: 20px;
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
        }
        
        .chat-section {
            padding: 30px;
        }
        
        .chat-container {
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            height: 500px;
            overflow-y: auto;
            padding: 20px;
            margin-bottom: 20px;
            background: #fafafa;
        }
        
        .message {
            margin: 15px 0;
            padding: 15px;
            border-radius: 10px;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .user-message {
            background: linear-gradient(135deg, #2196f3 0%, #21cbf3 100%);
            color: white;
            margin-left: auto;
            text-align: right;
        }
        
        .agent-message {
            background: linear-gradient(135deg, #4caf50 0%, #8bc34a 100%);
            color: white;
        }
        
        .input-section {
            display: flex;
            gap: 15px;
            align-items: center;
        }
        
        .input-field {
            flex: 1;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .input-field:focus {
            border-color: #2196f3;
        }
        
        .send-button {
            padding: 15px 30px;
            background: linear-gradient(135deg, #2196f3 0%, #21cbf3 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: transform 0.2s;
        }
        
        .send-button:hover {
            transform: translateY(-2px);
        }
        
        .send-button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 10px;
            color: #666;
        }
        
        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #2196f3;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .status {
            text-align: center;
            padding: 10px;
            background: #e8f5e8;
            border-radius: 5px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Emergency Navigator</h1>
            <p>Live Vertex AI Emergency Resource Finder</p>
        </div>
        
        <div class="emergency-banner">
            <div style="font-size: 1.2em; color: #d32f2f;">
                ⚠️ FOR IMMEDIATE EMERGENCIES: CALL 911 ⚠️
            </div>
            <div style="margin-top: 10px;">
                For mental health crises: Call or text <strong>988</strong>
            </div>
        </div>
        
        <div class="chat-section">
            <div class="status">
                ✅ Connected to Vertex AI Reasoning Engine: {{ engine_id }}
            </div>
            
            <div class="chat-container" id="chatContainer">
                <div class="message agent-message">
                    <strong>🚨 Emergency Navigator (Live AI):</strong><br>
                    Hello! I'm your live AI assistant powered by Vertex AI. I can help you find emergency resources like shelters, hospitals, and food assistance. 
                    <br><br>
                    <strong>I provide real-time guidance on:</strong>
                    <ul style="margin: 10px 0; padding-left: 20px;">
                        <li>Emergency shelters and housing</li>
                        <li>Hospital emergency rooms</li>
                        <li>Food banks and assistance programs</li>
                        <li>Safety protocols and emergency contacts</li>
                    </ul>
                    How can I help you today?
                </div>
            </div>
            
            <div class="loading" id="loadingIndicator">
                <div class="spinner"></div>
                <span style="margin-left: 10px;">Getting AI response...</span>
            </div>
            
            <div class="input-section">
                <input type="text" class="input-field" id="messageInput" 
                       placeholder="Ask about emergency resources..." 
                       onkeypress="handleKeyPress(event)">
                <button class="send-button" id="sendButton" onclick="sendMessage()">Send</button>
            </div>
        </div>
    </div>

    <script>
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const loadingIndicator = document.getElementById('loadingIndicator');
        
        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        function addMessage(message, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'agent-message'}`;
            
            const prefix = isUser ? '👤 You:' : '🚨 Emergency Navigator (Live AI):';
            messageDiv.innerHTML = `<strong>${prefix}</strong><br>${message.replace(/\\n/g, '<br>')}`;
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
        
        function showLoading(show) {
            loadingIndicator.style.display = show ? 'block' : 'none';
            sendButton.disabled = show;
            messageInput.disabled = show;
        }
        
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            addMessage(message, true);
            messageInput.value = '';
            showLoading(true);
            
            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ message: message })
                });
                
                const data = await response.json();
                
                showLoading(false);
                
                if (data.success) {
                    addMessage(data.response);
                } else {
                    addMessage(`I apologize, but I encountered an error: ${data.error}. Please try again or contact local emergency services at 911 for immediate assistance.`);
                }
                
            } catch (error) {
                showLoading(false);
                addMessage('I apologize, but I encountered a connection error. Please try again or contact local emergency services at 911 for immediate assistance.');
            }
        }
        
        // Focus on input field when page loads
        window.onload = function() {
            messageInput.focus();
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the main application page."""
    return render_template_string(HTML_TEMPLATE, engine_id=ENGINE_ID)

@app.route('/query', methods=['POST'])
def query_agent():
    """Query the Vertex AI reasoning engine."""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'No message provided'})
        
        # Query the reasoning engine
        response = reasoning_engine.query(input=message)
        
        # Extract the response text
        if hasattr(response, 'output'):
            response_text = response.output
        elif isinstance(response, dict) and 'output' in response:
            response_text = response['output']
        else:
            response_text = str(response)
        
        return jsonify({
            'success': True,
            'response': response_text,
            'engine_id': ENGINE_ID
        })
        
    except Exception as e:
        print(f"Error querying reasoning engine: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'engine_id': ENGINE_ID,
        'project_id': PROJECT_ID
    })

if __name__ == '__main__':
    print(f"🚀 Starting Emergency Navigator Flask App")
    print(f"📊 Project: {PROJECT_ID}")
    print(f"🧠 Engine ID: {ENGINE_ID}")
    print(f"🌐 Starting server on http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
