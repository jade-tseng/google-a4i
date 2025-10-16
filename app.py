#!/usr/bin/env python3
"""
ADK Web App Configuration
Configures agents for local web server using 'adk web'.
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import agents
from agents.fema2_agent import create_emergency_crisis_bigquery_agent

# Get project info from environment
project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'qwiklabs-gcp-01-2a76b8f0c7a6')
dataset_name = f"{project_id}.B2AgentsForImpact"

# Create the agent instance
agent = create_emergency_crisis_bigquery_agent(
    project_id=project_id,
    dataset_name=dataset_name
)

print(f"✅ Agent configured for ADK web server: {agent.name}")
print(f"📊 Project: {project_id}")
print(f"🗄️  Dataset: {dataset_name}")
