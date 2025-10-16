#!/usr/bin/env python3
"""
Emergency Navigator Agent for Google Agent Engine Deployment
Consolidated agent that can be deployed individually to Agent Engine.
"""

import os
import sys
from google.cloud import bigquery
from google.adk.agents import Agent
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.adk.tools import agent_tool
from google.genai import types
import google.auth

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.geocode_tool import geocode_tool


def create_emergency_navigator_agent(project_id: str, dataset_name: str = None, model: str = "gemini-2.5-flash") -> Agent:
    """
    Create a consolidated Emergency Resource Finder & Crisis Navigator Agent for deployment.
    
    Args:
        project_id: Google Cloud project ID
        dataset_name: BigQuery dataset name (defaults to {project_id}.emergency_resources)
        model: Gemini model to use
        
    Returns:
        Configured Agent for emergency resource navigation
    """
    if dataset_name is None:
        dataset_name = f"{project_id}.emergency_resources"
    
    # Setup BigQuery tools - simplified for deployment
    try:
        credentials, _ = google.auth.default()
        bq_credentials = BigQueryCredentialsConfig(credentials=credentials)
        bq_tool_cfg = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)  # Read-only
        
        bq_tools = BigQueryToolset(
            credentials_config=bq_credentials,
            bigquery_tool_config=bq_tool_cfg
        )
        tools = [bq_tools]
    except Exception as e:
        print(f"⚠️  BigQuery tools not available: {e}")
        tools = []  # Deploy without BigQuery tools for now
    
    # Consolidated instructions for emergency resource navigation
    instructions = f"""
    You are the Emergency Resource Finder & Crisis Navigator Agent.
    
    Your mission: Guide users to nearby emergency resources such as open shelters, hospitals with available emergency rooms,
    and food distribution centers using BigQuery data and provide safety-aware recommendations.
    
    Dataset: `{dataset_name}`
    
    ## Core Capabilities
    
    1. **Location Processing:**
       - Use the geocode tool to convert addresses to coordinates
       - Handle various location formats (city, state, coordinates, addresses)
       - Calculate distances from user location
    
    2. **Resource Querying:**
       - Query BigQuery for shelters, hospitals, food centers
       - Filter by constraints: pet_friendly, dietary_restrictions, capacity_needed, max_miles
       - Include current availability and status information
       - Use fully qualified table names: `{dataset_name}.shelters`, `{dataset_name}.hospitals`, etc.
    
    3. **Analysis & Ranking:**
       - Prioritize by distance (closer is better)
       - Consider current availability/capacity
       - Factor in user constraints and special needs
       - Prioritize resources that are currently open/available
    
    4. **Safety-First Responses:**
       - For immediate danger: "If you're in immediate danger, call 911. For mental health crises, call or text 988."
       - Provide clear, actionable recommendations
       - Include contact information and addresses
       - Mention any important constraints or safety considerations
    
    ## Response Format
    Always provide:
    - Brief summary of findings
    - Top 3-5 ranked resources with:
      * Name and type
      * Distance from user
      * Key features (pet-friendly, dietary options, etc.)
      * Contact information
      * Current status/availability
    - Practical next steps
    - Emergency contacts when relevant
    
    ## Example Queries You Handle
    - "Where is the nearest open and pet-friendly shelter with space for 3 people?"
    - "Which hospitals near me have open emergency rooms?"
    - "Food distribution centers with gluten-free options within 10 miles?"
    
    Be empathetic, concise, and always prioritize user safety.
    """
    
    # Add geocode tool if available
    try:
        tools.append(geocode_tool)
    except Exception as e:
        print(f"⚠️  Geocode tool not available: {e}")
    
    return Agent(
        model=model,
        name="emergency_resource_navigator",
        description="Finds and recommends emergency resources like shelters, hospitals, and food centers with safety guidance",
        instruction=instructions,
        tools=tools,
        generate_content_config=types.GenerateContentConfig(
            temperature=0.6,
            top_p=0.9,
            max_output_tokens=4096,
        ),
    )


# Deployment aliases
def create_emergency_navigator(project_id: str, dataset_name: str = None) -> Agent:
    """Create emergency navigator agent for deployment."""
    return create_emergency_navigator_agent(project_id, dataset_name)


def create_crisis_navigator_agent(project_id: str, dataset_name: str = None) -> Agent:
    """Alternative name for deployment discovery."""
    return create_emergency_navigator_agent(project_id, dataset_name)


if __name__ == "__main__":
    # Test the emergency navigator agent
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'test-project')
    dataset_name = f"{project_id}.emergency_resources"
    
    agent = create_emergency_navigator_agent(project_id, dataset_name)
    print(f"✅ Emergency Navigator Agent created: {agent.name}")
    print(f"📊 Project: {project_id}")
    print(f"🗄️  Dataset: {dataset_name}")
    print(f"🚨 Description: {agent.description}")
