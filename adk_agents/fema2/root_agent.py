#!/usr/bin/env python3
"""
Root Agent for USDA BigQuery Agent
Required by ADK web server.
"""

import os
import sys

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from agents.fema2_agent import create_emergency_crisis_bigquery_agent

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

dataset_name = f"{project_id}.B2AgentsForImpact"

# Create the root agent instance - this is what ADK web server expects
root_agent = create_emergency_crisis_bigquery_agent(
    project_id=project_id,
    dataset_name=dataset_name
)

print(f"✅ Root agent loaded: {root_agent.name}")
print(f"📊 Project: {project_id}")
print(f"🗄️  Dataset: {dataset_name}")
