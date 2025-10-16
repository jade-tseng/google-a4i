#!/usr/bin/env python3
"""
Complete Deployment Workflow
Orchestrates the full deployment pipeline from local testing to production Vertex AI app.
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_command(cmd, description, cwd=None):
    """Run a command and return success status."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ {description} failed")
            if result.stderr.strip():
                print(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False


def check_prerequisites():
    """Check if all prerequisites are met."""
    print("🔍 Checking prerequisites...")
    
    checks = [
        ("gcloud --version", "Google Cloud SDK"),
        ("python --version", "Python"),
        ("pip show google-cloud-aiplatform", "Google Cloud AI Platform"),
    ]
    
    all_good = True
    for cmd, desc in checks:
        if not run_command(cmd, f"Checking {desc}"):
            all_good = False
    
    return all_good


def test_local_adk():
    """Test the local ADK web server."""
    print("\n🧪 Testing Local ADK Web Server...")
    
    # Check if ADK agents directory exists
    if not Path("adk_agents/emergency_navigator").exists():
        print("❌ ADK agents directory not found")
        return False
    
    print("✅ ADK agents directory found")
    print("💡 To test locally, run: adk web adk_agents --port 8080")
    return True


def deploy_to_agent_engine():
    """Deploy individual agents to Google Agent Engine."""
    print("\n🚀 Deploying to Google Agent Engine...")
    
    # List available agents
    if not run_command("python deploy.py --list", "Listing available agents"):
        return False
    
    # Deploy emergency navigator agent
    if not run_command("python deploy.py --agent emergency_navigator", "Deploying emergency navigator agent"):
        return False
    
    return True


def deploy_to_vertex_ai():
    """Deploy as Vertex AI application."""
    print("\n🚀 Deploying to Vertex AI...")
    
    if not run_command("python deploy_vertex_app.py --app-name emergency-navigator", "Creating Vertex AI application"):
        return False
    
    return True


def create_vertex_endpoint():
    """Create Vertex AI endpoint for serving."""
    print("\n🌐 Creating Vertex AI Endpoint...")
    
    if not run_command("python deploy_vertex_app.py --create-endpoint", "Creating Vertex AI endpoint"):
        return False
    
    return True


def main():
    """Main workflow orchestrator."""
    parser = argparse.ArgumentParser(description="Complete Emergency Navigator Deployment Workflow")
    parser.add_argument('--step', choices=['check', 'local', 'agent-engine', 'vertex-ai', 'endpoint', 'all'], 
                       default='all', help="Which deployment step to run")
    parser.add_argument('--skip-checks', action='store_true', help="Skip prerequisite checks")
    
    args = parser.parse_args()
    
    print("🚀 Emergency Navigator Deployment Workflow")
    print("=" * 60)
    
    # Step 1: Check prerequisites
    if args.step in ['check', 'all'] and not args.skip_checks:
        if not check_prerequisites():
            print("\n❌ Prerequisites check failed. Please install missing components.")
            return 1
    
    # Step 2: Test local ADK
    if args.step in ['local', 'all']:
        if not test_local_adk():
            print("\n❌ Local ADK test failed.")
            return 1
    
    # Step 3: Deploy to Agent Engine
    if args.step in ['agent-engine', 'all']:
        if not deploy_to_agent_engine():
            print("\n❌ Agent Engine deployment failed.")
            return 1
    
    # Step 4: Deploy to Vertex AI
    if args.step in ['vertex-ai', 'all']:
        if not deploy_to_vertex_ai():
            print("\n❌ Vertex AI deployment failed.")
            return 1
    
    # Step 5: Create Vertex AI endpoint
    if args.step in ['endpoint', 'all']:
        if not create_vertex_endpoint():
            print("\n❌ Vertex AI endpoint creation failed.")
            return 1
    
    # Success summary
    print("\n🎉 Deployment Workflow Completed Successfully!")
    print("\n📋 What was deployed:")
    
    if args.step in ['local', 'all']:
        print("  ✅ Local ADK web server ready (run: adk web adk_agents --port 8080)")
    
    if args.step in ['agent-engine', 'all']:
        print("  ✅ Google Agent Engine deployment")
    
    if args.step in ['vertex-ai', 'all']:
        print("  ✅ Vertex AI application")
    
    if args.step in ['endpoint', 'all']:
        print("  ✅ Vertex AI serving endpoint")
    
    print("\n🔗 Next steps:")
    print("  - Test your deployed agents in Google Cloud Console")
    print("  - Monitor performance and usage")
    print("  - Set up CI/CD for automated deployments")
    
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
