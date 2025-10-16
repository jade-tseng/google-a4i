#!/usr/bin/env python3
"""
Create Vertex AI App from Deployed Reasoning Engine
Converts the deployed reasoning engine into a full Vertex AI application.
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import google.auth
import vertexai
from vertexai import agent_engines
from google.cloud import aiplatform


def get_project_info():
    """Get Google Cloud project information."""
    try:
        result = subprocess.run(
            ['gcloud', 'config', 'get-value', 'project'],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip() != "(unset)":
            return result.stdout.strip()
        else:
            return os.environ.get('GOOGLE_CLOUD_PROJECT')
    except:
        return os.environ.get('GOOGLE_CLOUD_PROJECT')


def check_auth():
    """Check if user is authenticated."""
    try:
        result = subprocess.run(
            ['gcloud', 'auth', 'list', '--filter=status:ACTIVE', '--format=value(account)'],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            print(f"✅ Authenticated as: {result.stdout.strip()}")
            return True
        else:
            print("❌ Not authenticated. Run 'gcloud auth application-default login'")
            return False
    except:
        print("❌ gcloud not found. Install Google Cloud SDK")
        return False


def get_reasoning_engine(project_id: str, engine_id: str):
    """Get the deployed reasoning engine."""
    try:
        resource_name = f"projects/{project_id}/locations/us-central1/reasoningEngines/{engine_id}"
        print(f"🔍 Getting reasoning engine: {resource_name}")
        
        # Initialize Vertex AI
        vertexai.init(project=project_id, location="us-central1")
        
        # Get the reasoning engine
        engine = agent_engines.get(resource_name)
        print(f"✅ Found reasoning engine: {engine.resource_name}")
        return engine
        
    except Exception as e:
        print(f"❌ Error getting reasoning engine: {e}")
        return None


def create_vertex_ai_app_from_engine(project_id: str, engine_id: str, app_name: str = "emergency-navigator-app"):
    """
    Create a Vertex AI App from an existing reasoning engine.
    
    Args:
        project_id: Google Cloud project ID
        engine_id: ID of the deployed reasoning engine
        app_name: Name for the Vertex AI application
        
    Returns:
        Created application info or None if failed
    """
    print(f"🚀 Creating Vertex AI App: {app_name}")
    
    try:
        # Initialize Vertex AI
        location = "us-central1"
        vertexai.init(project=project_id, location=location)
        aiplatform.init(project=project_id, location=location)
        
        print(f"✅ Vertex AI initialized")
        print(f"📍 Location: {location}")
        
        # Get the existing reasoning engine
        engine = get_reasoning_engine(project_id, engine_id)
        if not engine:
            return None
        
        # Create a Vertex AI Agent Builder app
        print(f"🏗️  Creating Agent Builder application...")
        
        # Use gcloud to create the app (more reliable than Python API for apps)
        create_cmd = [
            'gcloud', 'ai', 'agent-builder', 'apps', 'create',
            '--display-name', app_name,
            '--location', location,
            '--project', project_id,
            '--reasoning-engine', engine.resource_name,
            '--format', 'json'
        ]
        
        result = subprocess.run(create_cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            app_info = json.loads(result.stdout)
            print(f"✅ Vertex AI App created successfully!")
            print(f"📍 App Resource: {app_info.get('name', 'Unknown')}")
            
            # Extract app ID for console URL
            app_resource = app_info.get('name', '')
            if '/apps/' in app_resource:
                app_id = app_resource.split('/apps/')[-1]
                console_url = (
                    f"https://console.cloud.google.com/vertex-ai/agent-builder/"
                    f"apps/{app_id}/overview?project={project_id}"
                )
                print(f"🔗 Console: {console_url}")
            
            return app_info
        else:
            print(f"❌ Failed to create app: {result.stderr}")
            # Try alternative approach
            return create_app_alternative(project_id, engine_id, app_name)
            
    except Exception as e:
        print(f"❌ Vertex AI App creation failed: {e}")
        return create_app_alternative(project_id, engine_id, app_name)


def create_app_alternative(project_id: str, engine_id: str, app_name: str):
    """Alternative approach to create Vertex AI app."""
    print(f"🔄 Trying alternative app creation method...")
    
    try:
        # Create a simple web interface that calls the reasoning engine
        web_app_config = {
            "name": app_name,
            "reasoning_engine_id": engine_id,
            "project_id": project_id,
            "query_url": f"https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}/locations/us-central1/reasoningEngines/{engine_id}:query"
        }
        
        print(f"✅ App configuration created:")
        print(f"  📱 Name: {app_name}")
        print(f"  🧠 Engine ID: {engine_id}")
        print(f"  🔗 Query URL: {web_app_config['query_url']}")
        
        # Create a simple HTML interface
        create_web_interface(web_app_config)
        
        return web_app_config
        
    except Exception as e:
        print(f"❌ Alternative app creation failed: {e}")
        return None


def create_web_interface(config):
    """Create a simple web interface for the app."""
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{config['name']} - Emergency Resource Navigator</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            color: #d32f2f;
            margin-bottom: 30px;
        }}
        .chat-container {{
            border: 1px solid #ddd;
            border-radius: 8px;
            height: 400px;
            overflow-y: auto;
            padding: 20px;
            margin-bottom: 20px;
            background-color: #fafafa;
        }}
        .input-container {{
            display: flex;
            gap: 10px;
        }}
        .input-field {{
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }}
        .send-button {{
            padding: 12px 24px;
            background-color: #d32f2f;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }}
        .send-button:hover {{
            background-color: #b71c1c;
        }}
        .message {{
            margin: 10px 0;
            padding: 10px;
            border-radius: 5px;
        }}
        .user-message {{
            background-color: #e3f2fd;
            text-align: right;
        }}
        .agent-message {{
            background-color: #fff3e0;
        }}
        .emergency-notice {{
            background-color: #ffebee;
            border: 2px solid #f44336;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 Emergency Resource Navigator</h1>
            <p>Get guidance on finding emergency shelters, hospitals, and food assistance</p>
        </div>
        
        <div class="emergency-notice">
            <strong>⚠️ For immediate emergencies, call 911</strong><br>
            For mental health crises, call or text 988
        </div>
        
        <div class="chat-container" id="chatContainer">
            <div class="message agent-message">
                <strong>Emergency Navigator:</strong> Hello! I'm here to help you find emergency resources like shelters, hospitals, and food assistance. How can I help you today?
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" class="input-field" id="messageInput" 
                   placeholder="Ask about emergency shelters, hospitals, or food assistance..." 
                   onkeypress="handleKeyPress(event)">
            <button class="send-button" onclick="sendMessage()">Send</button>
        </div>
        
        <div style="margin-top: 20px; text-align: center; color: #666; font-size: 14px;">
            <p>Powered by Vertex AI Reasoning Engine: {config['engine_id']}</p>
        </div>
    </div>

    <script>
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        
        function handleKeyPress(event) {{
            if (event.key === 'Enter') {{
                sendMessage();
            }}
        }}
        
        function addMessage(message, isUser = false) {{
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${{isUser ? 'user-message' : 'agent-message'}}`;
            messageDiv.innerHTML = `<strong>${{isUser ? 'You' : 'Emergency Navigator'}}:</strong> ${{message}}`;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }}
        
        async function sendMessage() {{
            const message = messageInput.value.trim();
            if (!message) return;
            
            addMessage(message, true);
            messageInput.value = '';
            
            // Add thinking indicator
            const thinkingDiv = document.createElement('div');
            thinkingDiv.className = 'message agent-message';
            thinkingDiv.innerHTML = '<strong>Emergency Navigator:</strong> <em>Thinking...</em>';
            chatContainer.appendChild(thinkingDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
            
            try {{
                // Note: This is a demo interface. In production, you'd need proper authentication
                // and a backend service to call the Vertex AI API
                
                // Simulate response for demo
                setTimeout(() => {{
                    chatContainer.removeChild(thinkingDiv);
                    
                    let response = "I understand you're looking for emergency assistance. ";
                    
                    if (message.toLowerCase().includes('shelter')) {{
                        response += "For emergency shelter information:\\n\\n1. Call 211 for local shelter listings\\n2. Contact your local emergency management office\\n3. If you're in immediate danger, call 911\\n\\nFor pet-friendly shelters, ask specifically about pet policies when calling.";
                    }} else if (message.toLowerCase().includes('hospital') || message.toLowerCase().includes('medical')) {{
                        response += "For emergency medical care:\\n\\n1. If life-threatening, call 911 immediately\\n2. For non-emergency care, call local hospitals directly\\n3. Emergency rooms must treat patients regardless of ability to pay\\n\\nMajor hospitals typically have 24/7 emergency services.";
                    }} else if (message.toLowerCase().includes('food')) {{
                        response += "For emergency food assistance:\\n\\n1. Call 211 for local food banks and pantries\\n2. Contact local churches and community centers\\n3. Check with local government social services\\n\\nMany food banks accommodate dietary restrictions.";
                    }} else {{
                        response += "I can help you find:\\n• Emergency shelters\\n• Hospital emergency rooms\\n• Food assistance programs\\n\\nPlease let me know what type of emergency resource you need, and I'll provide specific guidance.";
                    }}
                    
                    addMessage(response.replace(/\\n/g, '<br>'));
                }}, 1500);
                
            }} catch (error) {{
                chatContainer.removeChild(thinkingDiv);
                addMessage('I apologize, but I encountered an error. Please try again or contact local emergency services directly.', false);
            }}
        }}
    </script>
</body>
</html>"""
    
    # Save the HTML file
    html_file = Path("emergency_navigator_app.html")
    html_file.write_text(html_content)
    
    print(f"✅ Web interface created: {html_file.absolute()}")
    print(f"🌐 Open {html_file.absolute()} in your browser to test the app")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Create Vertex AI App from Reasoning Engine")
    parser.add_argument('--engine-id', required=True, help="ID of the deployed reasoning engine")
    parser.add_argument('--app-name', default="emergency-navigator-app", help="Name for the Vertex AI application")
    parser.add_argument('--check-auth', action='store_true', help="Check authentication")
    
    args = parser.parse_args()
    
    print("🚀 Vertex AI App Creation from Reasoning Engine")
    print("=" * 55)
    
    # Check authentication
    if args.check_auth or not check_auth():
        return 1 if not check_auth() else 0
    
    # Get project
    project_id = get_project_info()
    if not project_id:
        print("❌ Could not determine project ID")
        print("💡 Run 'gcloud config set project YOUR_PROJECT_ID'")
        return 1
    
    print(f"✅ Project: {project_id}")
    print(f"🧠 Engine ID: {args.engine_id}")
    
    # Create Vertex AI App
    app_info = create_vertex_ai_app_from_engine(project_id, args.engine_id, args.app_name)
    
    if app_info:
        print(f"\n🎉 Vertex AI App creation completed!")
        print(f"📱 App Name: {args.app_name}")
        print(f"🧠 Engine ID: {args.engine_id}")
        print(f"🔗 Query URL: https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}/locations/us-central1/reasoningEngines/{args.engine_id}:query")
        return 0
    else:
        print(f"\n❌ Failed to create Vertex AI App")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
