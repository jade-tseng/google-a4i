#!/usr/bin/env python3
"""
Simple BigQuery Agent Deployment to Vertex AI Agent Engine
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Core imports
import google.auth
from google.cloud import bigquery, storage
from google.adk.agents import Agent
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from vertexai import agent_engines
import vertexai


def get_project_info():
    """Get project information."""
    try:
        import subprocess
        result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                              capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip() != "(unset)":
            project_id = result.stdout.strip()
        else:
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    except:
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
    
    if not project_id:
        raise ValueError("Could not determine project ID. Set GOOGLE_CLOUD_PROJECT or run 'gcloud config set project PROJECT_ID'")
    
    return project_id


def create_bigquery_agent(project_id: str, dataset_name: str):
    """Create the BigQuery agent for USDA food data."""
    
    # Setup authentication
    credentials, _ = google.auth.default()
    
    # Setup BigQuery tools
    bq_credentials = BigQueryCredentialsConfig(credentials=credentials)
    bq_tool_cfg = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)  # Read-only
    
    bq_tools = BigQueryToolset(
        credentials_config=bq_credentials,
        bigquery_tool_config=bq_tool_cfg
    )
    
    # Agent instructions with database schema
    instructions = f"""
    You are a data analysis agent with access to BigQuery tools.
    The dataset you have access to contains information from the USDA about foods and nutrition information.
    Only query the dataset `{dataset_name}`.
    Fully qualify every table as `{dataset_name}.<table>`.
    Never perform DDL/DML; SELECT-only. Return the SQL you ran along with a concise answer.
    
    Key tables available:
    - food: Main food items (fdc_id, description, food_category_id)
    - food_nutrient: Nutritional values (fdc_id, nutrient_id, amount)
    - nutrient: Nutrient definitions (id, name, unit_name)
    - food_category: Food categories (id, description)
    - market_acquisition: Food sourcing info
    
    Always provide helpful analysis of the USDA food and nutrition data.
    """
    
    # Create the agent
    agent = Agent(
        model="gemini-2.5-flash",
        name="usda_food_bigquery_agent",
        description="Analyzes USDA food and nutrition data using BigQuery",
        instruction=instructions,
        tools=[bq_tools],
    )
    
    return agent


def deploy_agent():
    """Deploy the BigQuery agent to Vertex AI Agent Engine."""
    
    print("🚀 Deploying USDA BigQuery Agent to Vertex AI Agent Engine...")
    
    # Get project info
    project_id = get_project_info()
    print(f"✓ Project ID: {project_id}")
    
    # Initialize Vertex AI
    vertexai.init(project=project_id, location="us-central1", staging_bucket="gs://agent-engine-staging-ec50015b68224a39baab")
    print("✓ Vertex AI initialized")
    
    # Set environment variables
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
    
    # Create dataset name
    dataset_name = f"{project_id}.B2AgentsForImpact"
    print(f"✓ Dataset: {dataset_name}")
    
    # Create the agent
    print("📊 Creating BigQuery agent...")
    agent = create_bigquery_agent(project_id, dataset_name)
    print(f"✓ Agent created: {agent.name}")
    
    # Prepare for deployment
    requirements = [
        "google-cloud-aiplatform[adk,agent_engines]>=1.70.0",
        "google-auth>=2.0.0",
        "google-genai>=0.8.0",
        "google-cloud-bigquery>=3.0.0",
        "pandas>=1.5.0"
    ]
    
    print("📦 Deployment requirements:")
    for req in requirements:
        print(f"  - {req}")
    
    # Create AdkApp
    print("\n🔧 Creating AdkApp wrapper...")
    app = agent_engines.AdkApp(
        agent=agent,
        enable_tracing=True,
    )
    
    # Deploy to Agent Engine
    print("\n🚀 Deploying to Vertex AI Agent Engine...")
    try:
        remote_app = agent_engines.create(
            display_name="usda-bigquery-food-agent",
            agent_engine=app,
            requirements=requirements
        )
        
        print("\n✅ Deployment successful!")
        print(f"📍 Resource Name: {remote_app.resource_name}")
        
        # Parse resource name for useful info
        parts = remote_app.resource_name.split('/')
        if len(parts) >= 6:
            project_number = parts[1]
            location = parts[3] 
            engine_id = parts[5]
            
            print(f"\n📋 Deployment Details:")
            print(f"  Project: {project_id}")
            print(f"  Location: {location}")
            print(f"  Engine ID: {engine_id}")
            
            console_url = f"https://console.cloud.google.com/vertex-ai/agent-builder/engines/{engine_id}/overview?project={project_id}"
            print(f"\n🔗 Access your agent:")
            print(f"  {console_url}")
        
        print(f"\n💡 Test your agent with queries like:")
        print(f"  - 'List all tables in the dataset'")
        print(f"  - 'How many rows are in the food table?'")
        print(f"  - 'Show top 10 foods highest in protein'")
        
        return remote_app
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        print(f"\n🔍 Troubleshooting:")
        print(f"  1. Ensure Vertex AI API is enabled: gcloud services enable aiplatform.googleapis.com")
        print(f"  2. Check permissions: you need Vertex AI Administrator role")
        print(f"  3. Verify billing is enabled for the project")
        print(f"  4. Make sure the dataset {dataset_name} exists and is accessible")
        raise


if __name__ == "__main__":
    try:
        deploy_agent()
        print("\n🎉 Deployment completed successfully!")
    except Exception as e:
        print(f"\n💥 Deployment failed: {e}")
        sys.exit(1)
