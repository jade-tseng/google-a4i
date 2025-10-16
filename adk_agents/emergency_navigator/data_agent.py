#!/usr/bin/env python3
"""
Data Agent for Emergency Resource Finder & Crisis Navigator
Queries BigQuery for emergency resources like shelters, hospitals, and food centers.
"""

from google.cloud import bigquery
from google.adk.agents import Agent
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.genai import types
import google.auth
import json


def create_data_agent(project_id: str, dataset_name: str, model: str = "gemini-2.5-flash") -> Agent:
    """
    Create a Data Agent for querying emergency resource data from BigQuery.
    
    Args:
        project_id: Google Cloud project ID
        dataset_name: BigQuery dataset name containing emergency resource data
        model: Gemini model to use
        
    Returns:
        Configured Agent for BigQuery data queries
    """
    # Setup BigQuery tools
    credentials, _ = google.auth.default()
    bq_credentials = BigQueryCredentialsConfig(credentials=credentials)
    bq_tool_cfg = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)  # Read-only
    
    bq_tools = BigQueryToolset(
        credentials_config=bq_credentials,
        bigquery_tool_config=bq_tool_cfg
    )
    
    # Agent instructions for emergency resource data queries
    instructions = f"""
    You are the Data Agent for the Emergency Resource Finder & Crisis Navigator system.
    
    Your role is to query BigQuery datasets containing emergency resource information and return structured data.
    
    Dataset: `{dataset_name}`
    
    Key tables you work with:
    - shelters: Emergency shelters with capacity, pet policies, accessibility info
    - hospitals: Hospitals with emergency room status, bed availability
    - food_centers: Food distribution centers with dietary options, hours
    - locations: Geographic data for all resources
    
    When queried:
    1. Parse the JSON parameters for location, resource type, and constraints
    2. Build appropriate SQL queries to find matching resources
    3. Include distance calculations from user location when coordinates provided
    4. Filter by constraints like pet_friendly, dietary_restrictions, capacity_needed
    5. Return structured rows with all relevant resource details
    6. Always include contact information and current status when available
    
    Query the dataset `{dataset_name}` only. Use fully qualified table names.
    Return results as structured data that can be processed by the Insights Agent.
    
    Be precise with SQL queries and handle location-based searches efficiently.
    """
    
    return Agent(
        model=model,
        name="emergency_data_agent",
        description="Queries BigQuery for emergency resource data including shelters, hospitals, and food centers",
        instruction=instructions,
        tools=[bq_tools],
        generate_content_config=types.GenerateContentConfig(
            temperature=0.3,  # Lower temperature for precise data queries
            top_p=0.8,
            max_output_tokens=4096,
        ),
    )


# Register this agent for deployment
def create_emergency_data_agent(project_id: str, dataset_name: str) -> Agent:
    """Alias for create_data_agent for consistency."""
    return create_data_agent(project_id, dataset_name)


if __name__ == "__main__":
    # Test the data agent
    import os
    project_id = os.environ.get('GOOGLE_CLOUD_PROJECT', 'test-project')
    dataset_name = f"{project_id}.emergency_resources"
    
    agent = create_data_agent(project_id, dataset_name)
    print(f"✅ Data Agent created: {agent.name}")
    print(f"📊 Project: {project_id}")
    print(f"🗄️  Dataset: {dataset_name}")
