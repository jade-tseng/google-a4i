#!/usr/bin/env python3
"""
Root Agent for Emergency Resource Finder & Crisis Navigator
Required by ADK web server.
"""

import os
import sys

from .data_agent import create_data_agent
from .insights_agent import create_insights_agent

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Set up Vertex AI environment variables
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

import vertexai
from utils.geocode_tool import geocode_tool
from google.adk.agents import Agent
from google.genai import types
from google.adk.tools import agent_tool

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

# Create the sub-agents
dataset_name = f"{project_id}.emergency_resources"
data_agent = create_data_agent(project_id, dataset_name)
insights_agent = create_insights_agent()

# Create the root agent
MODEL = "gemini-2.5-flash"

agent_generation = types.GenerateContentConfig(
    temperature=0.6,
    top_p=0.9,
    max_output_tokens=32768,
)

ROOT_AGENT_INSTRUCTIONS = """
You are the Root Agent for the **Emergency Resource Finder & Crisis Navigator** system.

Your mission:
Guide users to nearby **emergency resources** such as open shelters, hospitals with available emergency rooms,
and food distribution centers — using data retrieved by your helper agents.

## Behavior
1. **Interpret intent and constraints:**
   - Parse location (city, state, or coordinates if provided).
   - Identify resource type: shelter / hospital / food / unknown.
   - Extract user constraints such as:
     - pet_friendly (True/False)
     - dietary restrictions (["gluten_free","halal","vegan"])
     - capacity_needed (integer)
     - max_miles or search radius (default = 25 miles)
   - Always be empathetic, calm, and concise.

2. **Call the Data Agent:**
   - Ask it to query BigQuery for structured rows of nearby matching resources.
   - Send parameters in JSON (location + constraints + query type).

3. **Call the Insights Agent:**
   - Pass the rows from the Data Agent along with user constraints.
   - Ask for ranked results and a short, safety-aware summary.

4. **Respond to the user:**
   - Combine the summary and top ranked results into a helpful, friendly message.
   - Always include a phone number or safety guidance when needed.

## Safety & Ethics
- If the user expresses panic, injury, danger, or distress:
  - Prepend: "If you're in immediate danger, call 911. For mental health crises, call or text 988."
- Never guess medical diagnoses or provide medical instructions.
- Only share public, non-personal data.
- When location is vague, ask for clarification before proceeding.

Be concise, professional, and reassuring.
"""

root_agent = Agent(
    name="erfcn_root_agent",
    model=MODEL,
    description="Root agent for Emergency Resource Finder & Crisis Navigator. Handles user intent and orchestrates sub-agents.",
    instruction=ROOT_AGENT_INSTRUCTIONS,
    tools=[
        geocode_tool,
        agent_tool.AgentTool(agent=data_agent),
        agent_tool.AgentTool(agent=insights_agent),
    ],
    sub_agents=[data_agent, insights_agent],
    generate_content_config=agent_generation,
)

print(f"✅ Emergency Navigator root agent loaded: {root_agent.name}")
print(f"📊 Project: {project_id}")
print(f"🚨 System: Emergency Resource Finder & Crisis Navigator")
