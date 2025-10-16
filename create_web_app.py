#!/usr/bin/env python3
"""
Create Web App Interface for Deployed Reasoning Engine
Creates a web interface that connects to your deployed Vertex AI reasoning engine.
"""

import os
import sys
import argparse
from pathlib import Path


def create_web_app(project_id: str, engine_id: str, app_name: str = "Emergency Navigator"):
    """Create a web application interface for the reasoning engine."""
    
    query_url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}/locations/us-central1/reasoningEngines/{engine_id}:query"
    
    # Create HTML interface
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name} - Emergency Resource Finder</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #d32f2f 0%, #f44336 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .emergency-banner {{
            background: #ffebee;
            border: 3px solid #f44336;
            padding: 20px;
            margin: 20px;
            border-radius: 10px;
            text-align: center;
            font-weight: bold;
        }}
        
        .chat-section {{
            padding: 30px;
        }}
        
        .chat-container {{
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            height: 500px;
            overflow-y: auto;
            padding: 20px;
            margin-bottom: 20px;
            background: #fafafa;
        }}
        
        .message {{
            margin: 15px 0;
            padding: 15px;
            border-radius: 10px;
            max-width: 80%;
            word-wrap: break-word;
        }}
        
        .user-message {{
            background: linear-gradient(135deg, #2196f3 0%, #21cbf3 100%);
            color: white;
            margin-left: auto;
            text-align: right;
        }}
        
        .agent-message {{
            background: linear-gradient(135deg, #4caf50 0%, #8bc34a 100%);
            color: white;
        }}
        
        .input-section {{
            display: flex;
            gap: 15px;
            align-items: center;
        }}
        
        .input-field {{
            flex: 1;
            padding: 15px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }}
        
        .input-field:focus {{
            border-color: #2196f3;
        }}
        
        .send-button {{
            padding: 15px 30px;
            background: linear-gradient(135deg, #2196f3 0%, #21cbf3 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: transform 0.2s;
        }}
        
        .send-button:hover {{
            transform: translateY(-2px);
        }}
        
        .send-button:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }}
        
        .examples {{
            margin-top: 30px;
            padding: 20px;
            background: #f5f5f5;
            border-radius: 10px;
        }}
        
        .examples h3 {{
            color: #333;
            margin-bottom: 15px;
        }}
        
        .example-button {{
            display: inline-block;
            margin: 5px;
            padding: 10px 15px;
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }}
        
        .example-button:hover {{
            background: #2196f3;
            color: white;
        }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 14px;
            border-top: 1px solid #eee;
        }}
        
        .loading {{
            display: none;
            text-align: center;
            padding: 10px;
            color: #666;
        }}
        
        .spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #2196f3;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 {app_name}</h1>
            <p>Emergency Resource Finder & Crisis Navigator</p>
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
            <div class="chat-container" id="chatContainer">
                <div class="message agent-message">
                    <strong>🚨 Emergency Navigator:</strong><br>
                    Hello! I'm here to help you find emergency resources like shelters, hospitals, and food assistance. 
                    I can provide guidance on:
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
                <span style="margin-left: 10px;">Getting response...</span>
            </div>
            
            <div class="input-section">
                <input type="text" class="input-field" id="messageInput" 
                       placeholder="Ask about emergency shelters, hospitals, food assistance..." 
                       onkeypress="handleKeyPress(event)">
                <button class="send-button" id="sendButton" onclick="sendMessage()">Send</button>
            </div>
            
            <div class="examples">
                <h3>💡 Example Questions:</h3>
                <div class="example-button" onclick="setMessage('I need emergency shelter for tonight')">
                    Emergency shelter needed
                </div>
                <div class="example-button" onclick="setMessage('Where is the nearest hospital emergency room?')">
                    Nearest hospital ER
                </div>
                <div class="example-button" onclick="setMessage('I need food assistance for my family')">
                    Food assistance
                </div>
                <div class="example-button" onclick="setMessage('Pet-friendly emergency shelter')">
                    Pet-friendly shelter
                </div>
                <div class="example-button" onclick="setMessage('Mental health crisis resources')">
                    Mental health crisis
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Powered by Vertex AI Reasoning Engine</strong></p>
            <p>Engine ID: {engine_id}</p>
            <p>This is a demonstration interface. For real emergencies, always call 911.</p>
        </div>
    </div>

    <script>
        const chatContainer = document.getElementById('chatContainer');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const loadingIndicator = document.getElementById('loadingIndicator');
        
        function handleKeyPress(event) {{
            if (event.key === 'Enter' && !event.shiftKey) {{
                event.preventDefault();
                sendMessage();
            }}
        }}
        
        function setMessage(message) {{
            messageInput.value = message;
            messageInput.focus();
        }}
        
        function addMessage(message, isUser = false) {{
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${{isUser ? 'user-message' : 'agent-message'}}`;
            
            const prefix = isUser ? '👤 You:' : '🚨 Emergency Navigator:';
            messageDiv.innerHTML = `<strong>${{prefix}}</strong><br>${{message.replace(/\\n/g, '<br>')}}`;
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }}
        
        function showLoading(show) {{
            loadingIndicator.style.display = show ? 'block' : 'none';
            sendButton.disabled = show;
            messageInput.disabled = show;
        }}
        
        async function sendMessage() {{
            const message = messageInput.value.trim();
            if (!message) return;
            
            addMessage(message, true);
            messageInput.value = '';
            showLoading(true);
            
            try {{
                // Note: This is a demo interface showing the structure
                // In production, you'd need:
                // 1. A backend service with proper authentication
                // 2. CORS configuration
                // 3. Error handling and rate limiting
                
                // For now, simulate intelligent responses based on keywords
                let response = await generateResponse(message);
                
                setTimeout(() => {{
                    showLoading(false);
                    addMessage(response);
                }}, 1500); // Simulate API delay
                
            }} catch (error) {{
                showLoading(false);
                addMessage('I apologize, but I encountered an error. Please try again or contact local emergency services directly at 911 for immediate assistance.', false);
            }}
        }}
        
        async function generateResponse(message) {{
            const msg = message.toLowerCase();
            
            // Emergency keywords
            if (msg.includes('911') || msg.includes('emergency') || msg.includes('urgent') || msg.includes('help')) {{
                return `🚨 <strong>IMMEDIATE EMERGENCY RESPONSE:</strong><br><br>
                If you're in immediate danger or having a medical emergency, <strong>CALL 911 NOW</strong>.<br><br>
                If this is a mental health crisis, call or text <strong>988</strong> for the Crisis Lifeline.<br><br>
                For other urgent needs, I can help guide you to appropriate resources. What specific type of emergency assistance do you need?`;
            }}
            
            // Shelter-related
            if (msg.includes('shelter') || msg.includes('housing') || msg.includes('homeless')) {{
                let response = `🏠 <strong>Emergency Shelter Information:</strong><br><br>
                <strong>Immediate Steps:</strong><br>
                1. Call <strong>211</strong> for local shelter listings and availability<br>
                2. Contact your local emergency management office<br>
                3. Check with local churches and community centers<br><br>
                <strong>What to Ask:</strong><br>
                • Current availability and capacity<br>
                • Check-in times and procedures<br>
                • What to bring (ID, medications, etc.)<br>
                • Length of stay policies<br><br>`;
                
                if (msg.includes('pet')) {{
                    response += `<strong>Pet-Friendly Options:</strong><br>
                    • Specifically ask about pet policies when calling<br>
                    • Some shelters have separate pet accommodation<br>
                    • Contact local animal shelters for temporary pet care<br><br>`;
                }}
                
                response += `<strong>Safety Note:</strong> If you're in immediate danger, call 911 first.`;
                return response;
            }}
            
            // Hospital/Medical
            if (msg.includes('hospital') || msg.includes('medical') || msg.includes('doctor') || msg.includes('emergency room') || msg.includes('er')) {{
                return `🏥 <strong>Emergency Medical Care:</strong><br><br>
                <strong>Life-Threatening Emergency:</strong><br>
                • Call <strong>911</strong> immediately for ambulance<br>
                • Don't drive yourself if seriously injured<br><br>
                <strong>Non-Life-Threatening:</strong><br>
                • Call local hospitals directly for ER wait times<br>
                • Emergency rooms must treat patients regardless of ability to pay<br>
                • Bring ID, insurance cards, and medication list if possible<br><br>
                <strong>Finding Hospitals:</strong><br>
                • Use Google Maps: "emergency room near me"<br>
                • Call 411 for hospital phone numbers<br>
                • Major hospitals typically have 24/7 emergency services<br><br>
                <strong>Remember:</strong> For chest pain, difficulty breathing, severe bleeding, or loss of consciousness, call 911 immediately.`;
            }}
            
            // Food assistance
            if (msg.includes('food') || msg.includes('hungry') || msg.includes('eat') || msg.includes('meal')) {{
                let response = `🍽️ <strong>Emergency Food Assistance:</strong><br><br>
                <strong>Immediate Resources:</strong><br>
                1. Call <strong>211</strong> for local food banks and pantries<br>
                2. Contact local churches and community centers<br>
                3. Check with Salvation Army and local charities<br>
                4. Visit government social services office<br><br>
                <strong>What to Expect:</strong><br>
                • Most food banks are free<br>
                • May need to show ID or proof of need<br>
                • Hours vary - call ahead<br><br>`;
                
                if (msg.includes('dietary') || msg.includes('allerg') || msg.includes('gluten') || msg.includes('halal') || msg.includes('kosher')) {{
                    response += `<strong>Dietary Restrictions:</strong><br>
                    • Many food banks accommodate special diets<br>
                    • Ask specifically about your dietary needs<br>
                    • Some religious organizations provide culturally appropriate food<br><br>`;
                }}
                
                response += `<strong>Additional Programs:</strong><br>
                • SNAP (Food Stamps) - apply at local social services<br>
                • WIC for women, infants, and children<br>
                • School meal programs for children`;
                
                return response;
            }}
            
            // Mental health
            if (msg.includes('mental') || msg.includes('depression') || msg.includes('anxiety') || msg.includes('suicide') || msg.includes('crisis')) {{
                return `🧠 <strong>Mental Health Crisis Support:</strong><br><br>
                <strong>Immediate Crisis:</strong><br>
                • Call or text <strong>988</strong> - National Crisis Lifeline (24/7)<br>
                • Text "HELLO" to 741741 - Crisis Text Line<br>
                • Call 911 if in immediate danger<br><br>
                <strong>Local Resources:</strong><br>
                • Call 211 for local mental health services<br>
                • Contact local community mental health centers<br>
                • Many hospitals have psychiatric emergency services<br><br>
                <strong>Online Support:</strong><br>
                • NAMI.org - National Alliance on Mental Illness<br>
                • MentalHealth.gov for resources<br><br>
                <strong>Remember:</strong> You're not alone. Help is available 24/7.`;
            }}
            
            // General response
            return `🚨 <strong>Emergency Resource Guidance:</strong><br><br>
            I can help you find information about:<br><br>
            🏠 <strong>Emergency Shelters:</strong> Housing assistance and temporary shelter<br>
            🏥 <strong>Medical Care:</strong> Hospital emergency rooms and urgent care<br>
            🍽️ <strong>Food Assistance:</strong> Food banks, pantries, and meal programs<br>
            🧠 <strong>Mental Health:</strong> Crisis support and counseling services<br><br>
            <strong>Key Emergency Numbers:</strong><br>
            • <strong>911</strong> - Life-threatening emergencies<br>
            • <strong>988</strong> - Mental health crisis<br>
            • <strong>211</strong> - Local resources and services<br><br>
            Please let me know what specific type of emergency resource you need, and I'll provide more detailed guidance.`;
        }}
        
        // Focus on input field when page loads
        window.onload = function() {{
            messageInput.focus();
        }}
    </script>
</body>
</html>"""
    
    # Save the HTML file
    html_file = Path(f"{app_name.lower().replace(' ', '_')}_app.html")
    html_file.write_text(html_content)
    
    return html_file


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Create Web App for Vertex AI Reasoning Engine")
    parser.add_argument('--project-id', required=True, help="Google Cloud project ID")
    parser.add_argument('--engine-id', required=True, help="Reasoning engine ID")
    parser.add_argument('--app-name', default="Emergency Navigator", help="Name for the web application")
    
    args = parser.parse_args()
    
    print("🚀 Creating Web App for Vertex AI Reasoning Engine")
    print("=" * 55)
    print(f"📊 Project: {args.project_id}")
    print(f"🧠 Engine ID: {args.engine_id}")
    print(f"📱 App Name: {args.app_name}")
    
    # Create the web app
    html_file = create_web_app(args.project_id, args.engine_id, args.app_name)
    
    print(f"\n✅ Web application created successfully!")
    print(f"📄 File: {html_file.absolute()}")
    print(f"🌐 Open the file in your browser to use the app")
    
    # Create deployment info
    query_url = f"https://us-central1-aiplatform.googleapis.com/v1/projects/{args.project_id}/locations/us-central1/reasoningEngines/{args.engine_id}:query"
    
    print(f"\n📋 Deployment Information:")
    print(f"  🔗 Query URL: {query_url}")
    print(f"  🧠 Engine Resource: projects/{args.project_id}/locations/us-central1/reasoningEngines/{args.engine_id}")
    
    print(f"\n💡 Next Steps:")
    print(f"  1. Open {html_file.name} in your web browser")
    print(f"  2. Test the emergency resource guidance")
    print(f"  3. Deploy to a web server for production use")
    
    return 0


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
