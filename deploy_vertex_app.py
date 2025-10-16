#!/usr/bin/env python3
"""
Vertex AI App Deployment Script
Creates a Vertex AI application from the Emergency Navigator agent.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import google.auth
import vertexai
from vertexai import agent_engines
from google.cloud import aiplatform
from agents.emergency_navigator_agent import create_emergency_navigator_agent


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


def create_vertex_ai_app(project_id: str, app_name: str = "emergency-navigator"):
    """
    Create a Vertex AI application with the Emergency Navigator agent.
    
    Args:
        project_id: Google Cloud project ID
        app_name: Name for the Vertex AI application
        
    Returns:
        Deployed application resource or None if failed
    """
    print(f"🚀 Creating Vertex AI App: {app_name}")
    
    try:
        # Initialize Vertex AI
        location = "us-central1"
        staging_bucket = f"gs://vertex-app-{project_id[:8]}"
        
        vertexai.init(project=project_id, location=location, staging_bucket=staging_bucket)
        aiplatform.init(project=project_id, location=location, staging_bucket=staging_bucket)
        
        print(f"✅ Vertex AI initialized")
        print(f"📍 Location: {location}")
        print(f"🗄️  Staging bucket: {staging_bucket}")
        
        # Create the emergency navigator agent
        dataset_name = f"{project_id}.emergency_resources"
        agent = create_emergency_navigator_agent(project_id, dataset_name)
        
        print(f"✅ Agent created: {agent.name}")
        
        # Create AdkApp for Vertex AI
        app = agent_engines.AdkApp(
            agent=agent,
            enable_tracing=True,
        )
        
        # Deploy to Vertex AI Agent Engine
        print(f"🚀 Deploying to Vertex AI Agent Engine...")
        
        remote_app = agent_engines.create(
            display_name=app_name,
            agent_engine=app,
            requirements=[
                "google-cloud-aiplatform[adk,agent_engines]>=1.70.0",
                "google-auth>=2.0.0",
                "google-genai>=0.8.0",
                "google-cloud-bigquery>=3.0.0",
                "pandas>=1.5.0"
            ]
        )
        
        print(f"✅ Vertex AI App deployed successfully!")
        print(f"📍 Resource: {remote_app.resource_name}")
        
        # Extract engine ID for console URLs
        parts = remote_app.resource_name.split('/')
        if len(parts) >= 6:
            engine_id = parts[5]
            
            # Console URLs
            agent_console_url = (
                f"https://console.cloud.google.com/vertex-ai/agent-builder/"
                f"engines/{engine_id}/overview?project={project_id}"
            )
            
            vertex_console_url = (
                f"https://console.cloud.google.com/vertex-ai/reasoning-engines/"
                f"{engine_id}?project={project_id}"
            )
            
            print(f"\n🔗 Console URLs:")
            print(f"  Agent Builder: {agent_console_url}")
            print(f"  Vertex AI: {vertex_console_url}")
        
        return remote_app
        
    except Exception as e:
        print(f"❌ Vertex AI App deployment failed: {e}")
        print("\n💡 Troubleshooting:")
        print("  - Ensure Vertex AI API is enabled: gcloud services enable aiplatform.googleapis.com")
        print("  - Check you have Vertex AI Administrator role")
        print("  - Verify billing is enabled")
        print("  - Ensure staging bucket exists or can be created")
        return None


def create_vertex_ai_endpoint(project_id: str, engine_resource_name: str):
    """
    Create a Vertex AI endpoint for the deployed agent engine.
    
    Args:
        project_id: Google Cloud project ID
        engine_resource_name: Resource name of the deployed agent engine
        
    Returns:
        Endpoint resource or None if failed
    """
    print(f"🌐 Creating Vertex AI Endpoint...")
    
    try:
        # Initialize Vertex AI
        aiplatform.init(project=project_id, location="us-central1")
        
        # Create endpoint
        endpoint = aiplatform.Endpoint.create(
            display_name="emergency-navigator-endpoint",
            description="Endpoint for Emergency Resource Finder & Crisis Navigator",
        )
        
        print(f"✅ Endpoint created: {endpoint.resource_name}")
        print(f"🔗 Endpoint URL: {endpoint.gca_resource.name}")
        
        return endpoint
        
    except Exception as e:
        print(f"❌ Endpoint creation failed: {e}")
        return None


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy Emergency Navigator to Vertex AI")
    parser.add_argument('--app-name', default="emergency-navigator", help="Name for the Vertex AI application")
    parser.add_argument('--create-endpoint', action='store_true', help="Also create a Vertex AI endpoint")
    parser.add_argument('--check-auth', action='store_true', help="Check authentication")
    
    args = parser.parse_args()
    
    print("🚀 Vertex AI App Deployment System")
    print("=" * 50)
    
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
    
    # Deploy Vertex AI App
    remote_app = create_vertex_ai_app(project_id, args.app_name)
    if not remote_app:
        return 1
    
    # Optionally create endpoint
    if args.create_endpoint:
        endpoint = create_vertex_ai_endpoint(project_id, remote_app.resource_name)
        if endpoint:
            print(f"\n🎉 Complete deployment successful!")
            print(f"📱 App: {remote_app.resource_name}")
            print(f"🌐 Endpoint: {endpoint.resource_name}")
        else:
            print(f"\n⚠️  App deployed but endpoint creation failed")
            return 1
    else:
        print(f"\n🎉 Vertex AI App deployment successful!")
        print(f"💡 Use --create-endpoint to also create a serving endpoint")
    
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
