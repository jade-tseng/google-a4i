#!/usr/bin/env python3
"""
Simple Agent Deployment Script
Discovers agents in agents/ directory and deploys them to Google Agent Engine.
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
            print("❌ Not authenticated. Run 'python setup_auth.py' first")
            return False
    except:
        print("❌ gcloud not found. Install Google Cloud SDK")
        return False


def discover_agents():
    """Discover agents in the agents/ directory."""
    print("🔍 Discovering agents...")
    
    agents_dir = Path("agents")
    if not agents_dir.exists():
        print("❌ agents/ directory not found")
        return {}
    
    # Add agents directory to path
    sys.path.insert(0, str(agents_dir.absolute()))
    
    # Find and load all agent files
    agent_files = list(agents_dir.glob("*.py"))
    agent_files = [f for f in agent_files if f.name not in ["__init__.py", "registry.py"]]
    
    print(f"Found {len(agent_files)} agent files:")
    for file in agent_files:
        print(f"  - {file.name}")
    
    agents = {}
    
    # Load each agent module and look for agent creation functions
    for agent_file in agent_files:
        module_name = agent_file.stem
        try:
            print(f"📦 Loading {module_name}...")
            spec = importlib.util.spec_from_file_location(module_name, agent_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                
                # Look for agent creation functions (functions that start with 'create_' and end with '_agent')
                for attr_name in dir(module):
                    if attr_name.startswith('create_') and attr_name.endswith('_agent'):
                        func = getattr(module, attr_name)
                        if callable(func):
                            agent_name = attr_name.replace('create_', '').replace('_agent', '')
                            agents[agent_name] = {
                                'name': agent_name,
                                'create_function': func,
                                'module': module_name,
                                'file': agent_file.name
                            }
                            print(f"  ✅ Found agent creator: {attr_name}")
                            
        except Exception as e:
            print(f"❌ Error loading {module_name}: {e}")
    
    print(f"\n✅ Discovered {len(agents)} agents:")
    for name, info in agents.items():
        print(f"  - {name} (from {info['file']})")
    
    return agents


def create_agent_instance(agent_info, project_id: str):
    """Create an agent instance."""
    print(f"🤖 Creating {agent_info['name']} agent...")
    
    try:
        # Create the agent with project info
        agent = agent_info['create_function'](
            project_id=project_id,
            dataset_name=f"{project_id}.B2AgentsForImpact"
        )
        print(f"✅ Created agent: {agent.name}")
        return agent
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        return None


def deploy_agent(agent: Agent, agent_info, project_id: str):
    """Deploy an agent to Google Agent Engine."""
    agent_name = agent_info['name']
    print(f"\n🚀 Deploying {agent_name} agent...")
    
    try:
        # Create AdkApp
        app = agent_engines.AdkApp(
            agent=agent,
            enable_tracing=True,
        )
        
        # Deploy
        deployment_name = agent_name.replace('_', '-')
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
        
        return remote_app
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        print("💡 Troubleshooting:")
        print("  - Ensure Vertex AI API is enabled: gcloud services enable aiplatform.googleapis.com")
        print("  - Check you have Vertex AI Administrator role")
        print("  - Verify billing is enabled")
        return None


def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description="Deploy agents to Google Agent Engine")
    parser.add_argument('--agent', '-a', help="Deploy specific agent by name")
    parser.add_argument('--list', '-l', action='store_true', help="List available agents")
    parser.add_argument('--check-auth', action='store_true', help="Check authentication")
    
    args = parser.parse_args()
    
    print("🚀 Agent Deployment System")
    print("=" * 40)
    
    # Check authentication
    if args.check_auth or not check_auth():
        return 1 if not check_auth() else 0
    
    # Get project
    project_id = get_project_info()
    if not project_id:
        print("❌ Could not determine project ID")
        print("💡 Run 'python setup_auth.py' to configure")
        return 1
    
    print(f"✅ Project: {project_id}")
    
    # Initialize Vertex AI
    try:
        staging_bucket = f"gs://agent-staging-{project_id[:8]}"
        vertexai.init(project=project_id, location="us-central1", staging_bucket=staging_bucket)
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
        os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
        print(f"✅ Vertex AI initialized (staging: {staging_bucket})")
    except Exception as e:
        print(f"❌ Error initializing Vertex AI: {e}")
        return 1
    
    # Discover agents
    agents = discover_agents()
    if not agents:
        print("❌ No agents found")
        return 1
    
    # List only
    if args.list:
        print(f"\n📋 Available agents ({len(agents)}):")
        for name, info in agents.items():
            print(f"  - {name} (from {info['file']})")
        return 0
    
    # Deploy specific agent
    if args.agent:
        if args.agent not in agents:
            print(f"❌ Agent '{args.agent}' not found")
            print(f"Available: {', '.join(agents.keys())}")
            return 1
        
        agent_info = agents[args.agent]
        agent = create_agent_instance(agent_info, project_id)
        if agent:
            result = deploy_agent(agent, agent_info, project_id)
            return 0 if result else 1
        return 1
    
    # Deploy all agents
    print(f"\n🚀 Deploying {len(agents)} agents...")
    deployed = 0
    
    for name, agent_info in agents.items():
        print(f"\n[{deployed + 1}/{len(agents)}] {agent_info.display_name}")
        agent = create_agent_instance(agent_info, project_id)
        if agent:
            result = deploy_agent(agent, agent_info, project_id)
            if result:
                deployed += 1
    
    print(f"\n🎉 Deployed {deployed}/{len(agents)} agents successfully!")
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
        sys.exit(1)
