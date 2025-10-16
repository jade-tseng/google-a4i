#!/usr/bin/env python3
"""
Root Agent for Emergency Resource Finder & Crisis Navigator
Required by ADK web server.
"""

import os
import sys

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Set up Vertex AI environment variables
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

import vertexai

# Get project info from environment
project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
if not project_id:
    # Try to get from gcloud
    import subprocess
    try:
        result = subprocess.run(
            ['gcloud', 'config', 'get-value', 'project'],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip() != "(unset)":
            project_id = result.stdout.strip()
    except:
        pass

if not project_id:
    project_id = "your-project-id"
    print("⚠️  Could not determine project ID. Using placeholder.")

# Initialize Vertex AI
try:
    vertexai.init(project=project_id, location="us-central1")
    print(f"✅ Vertex AI initialized for project: {project_id}")
except Exception as e:
    print(f"⚠️  Vertex AI initialization warning: {e}")

# Import and create the root agent
from root_agent import root_agent

print(f"✅ Emergency Navigator root agent loaded: {root_agent.name}")
print(f"📊 Project: {project_id}")
print(f"🚨 System: Emergency Resource Finder & Crisis Navigator")
