#!/usr/bin/env python3
"""
ADK Agents Deployment Script
Deploys the multi-agent system from adk_agents/ directory to Google Cloud Agent Engine.
"""

import os
import sys
import subprocess
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Core imports
import google.auth
import vertexai
from vertexai import agent_engines
from google.adk.agents import Agent


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


def discover_adk_agents():
    """Discover ADK agent applications in adk_agents/ directory."""
    print("🔍 Discovering ADK agents...")
    
    adk_agents_dir = Path("adk_agents")
    if not adk_agents_dir.exists():
        print("❌ adk_agents/ directory not found")
        return {}
    
    # Find all subdirectories (each represents an ADK app)
    app_dirs = [d for d in adk_agents_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    
    print(f"Found {len(app_dirs)} ADK applications:")
    for app_dir in app_dirs:
        print(f"  - {app_dir.name}")
    
    agents = {}
    
    # Load each ADK application
    for app_dir in app_dirs:
        app_name = app_dir.name
        root_agent_file = app_dir / "root_agent.py"
        
        if not root_agent_file.exists():
            print(f"⚠️  {app_name}: No root_agent.py found, skipping")
            continue
            
        try:
            print(f"📦 Loading {app_name}...")
            
            # Add the app directory to Python path
            sys.path.insert(0, str(app_dir.absolute()))
            
            # Import the root_agent module
            spec = importlib.util.spec_from_file_location(f"{app_name}_root_agent", root_agent_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[f"{app_name}_root_agent"] = module
                spec.loader.exec_module(module)
                
                # Look for root_agent variable
                if hasattr(module, 'root_agent'):
                    root_agent = getattr(module, 'root_agent')
                    if hasattr(root_agent, 'name'):
                        agents[app_name] = {
                            'name': app_name,
                            'root_agent': root_agent,
                            'app_dir': app_dir,
                            'description': getattr(root_agent, 'description', f"ADK agent application: {app_name}")
                        }
                        print(f"  ✅ Found root agent: {root_agent.name}")
                    else:
                        print(f"  ❌ root_agent object has no name attribute")
                else:
                    print(f"  ❌ No root_agent variable found in {root_agent_file}")
                    
        except Exception as e:
            print(f"❌ Error loading {app_name}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n✅ Discovered {len(agents)} ADK agents:")
    for name, info in agents.items():
        print(f"  - {name}: {info['description']}")
    
    return agents


def deploy_adk_agent(agent_info, project_id: str):
    """Deploy an ADK agent application to Google Agent Engine."""
    app_name = agent_info['name']
    root_agent = agent_info['root_agent']
    
    print(f"\n🚀 Deploying ADK application: {app_name}")
    print(f"🤖 Root agent: {root_agent.name}")
    
    try:
        # Create AdkApp from the root agent
        app = agent_engines.AdkApp(
            agent=root_agent,
            enable_tracing=True,
        )
        
        # Deploy to Agent Engine
        deployment_name = app_name.replace('_', '-')
        print(f"📝 Deployment name: {deployment_name}")
        
        remote_app = agent_engines.create(
            display_name=deployment_name,
            agent_engine=app,
            requirements=[
                "google-cloud-aiplatform[adk,agent_engines]>=1.70.0",
                "google-auth>=2.0.0",
                "google-genai>=0.8.0",
                "google-cloud-bigquery>=3.0.0",
                "pandas>=1.5.0"
            ]
        )
        
        print(f"✅ Deployment successful!")
        print(f"📍 Resource: {remote_app.resource_name}")
        
        # Extract engine ID for console URL
        parts = remote_app.resource_name.split('/')
        if len(parts) >= 6:
            engine_id = parts[5]
            console_url = (
                f"https://console.cloud.google.com/vertex-ai/agent-builder/"
                f"engines/{engine_id}/overview?project={project_id}"
            )
            print(f"🔗 Console: {console_url}")
            
            # Also provide reasoning engines URL
            reasoning_url = (
                f"https://console.cloud.google.com/vertex-ai/reasoning-engines/"
                f"{engine_id}?project={project_id}"
            )
            print(f"🧠 Reasoning Engine: {reasoning_url}")
        
        return remote_app
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        print("💡 Troubleshooting:")
        print("  - Ensure Vertex AI API is enabled: gcloud services enable aiplatform.googleapis.com")
        print("  - Check you have Vertex AI Administrator role")
        print("  - Verify billing is enabled")
        print("  - Check agent dependencies and imports")
        return None


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy ADK agents to Google Agent Engine")
    parser.add_argument('--app', '-a', help="Deploy specific ADK application by name")
    parser.add_argument('--list', '-l', action='store_true', help="List available ADK applications")
    parser.add_argument('--check-auth', action='store_true', help="Check authentication")
    
    args = parser.parse_args()
    
    print("🚀 ADK Agents Deployment System")
    print("=" * 45)
    
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
    
    # Initialize Vertex AI
    try:
        staging_bucket = f"gs://adk-staging-{project_id[:8]}"
        vertexai.init(project=project_id, location="us-central1", staging_bucket=staging_bucket)
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
        os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
        print(f"✅ Vertex AI initialized (staging: {staging_bucket})")
    except Exception as e:
        print(f"❌ Error initializing Vertex AI: {e}")
        return 1
    
    # Discover ADK agents
    agents = discover_adk_agents()
    if not agents:
        print("❌ No ADK agents found")
        return 1
    
    # List only
    if args.list:
        print(f"\n📋 Available ADK applications ({len(agents)}):")
        for name, info in agents.items():
            print(f"  - {name}")
            print(f"    Root Agent: {info['root_agent'].name}")
            print(f"    Description: {info['description']}")
            print(f"    Directory: {info['app_dir']}")
        return 0
    
    # Deploy specific application
    if args.app:
        if args.app not in agents:
            print(f"❌ ADK application '{args.app}' not found")
            print(f"Available: {', '.join(agents.keys())}")
            return 1
        
        agent_info = agents[args.app]
        result = deploy_adk_agent(agent_info, project_id)
        return 0 if result else 1
    
    # Deploy all applications
    print(f"\n🚀 Deploying {len(agents)} ADK applications...")
    deployed = 0
    
    for name, agent_info in agents.items():
        print(f"\n[{deployed + 1}/{len(agents)}] {agent_info['name']}")
        result = deploy_adk_agent(agent_info, project_id)
        if result:
            deployed += 1
    
    print(f"\n🎉 Deployed {deployed}/{len(agents)} ADK applications successfully!")
    
    if deployed > 0:
        print(f"\n📍 Find your deployed agents at:")
        print(f"  🔗 Agent Builder: https://console.cloud.google.com/vertex-ai/agent-builder/engines?project={project_id}")
        print(f"  🧠 Reasoning Engines: https://console.cloud.google.com/vertex-ai/reasoning-engines?project={project_id}")
    
    return 0 if deployed > 0 else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
