#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deploy BigQuery Agent to Vertex AI Agent Engine
"""

import asyncio
import os
from vertexai import agent_engines

# Local imports
from google_utils import initialize_google_cloud
from bigquery_agent import create_usda_bigquery_agent


def deploy_bigquery_agent():
    """Deploy the BigQuery agent to Vertex AI Agent Engine."""
    
    print("🚀 Deploying BigQuery Agent to Vertex AI Agent Engine...")
    
    # Initialize Google Cloud
    print("☁️  Initializing Google Cloud services...")
    config, _ = initialize_google_cloud(create_staging_bucket=True)
    
    # Create the BigQuery agent
    print("📊 Creating USDA BigQuery agent...")
    bigquery_agent = create_usda_bigquery_agent(
        project_id=config.project_id,
        dataset_name=config.dataset_name,
        model="gemini-2.5-flash"
    )
    
    print(f"✓ Agent created: {bigquery_agent.name}")
    print(f"✓ Description: {bigquery_agent.description}")
    
    # Prepare requirements
    requirements = [
        "google-cloud-aiplatform[adk,agent_engines]>=1.70.0",
        "google-auth>=2.0.0",
        "google-genai>=0.8.0",
        "google-cloud-bigquery>=3.0.0",
        "google-cloud-storage>=2.0.0",
        "pandas>=1.5.0",
        "requests>=2.28.0"
    ]
    
    print("📦 Requirements:")
    for req in requirements:
        print(f"  - {req}")
    
    # Wrap the agent in an AdkApp
    print("\n🔧 Creating AdkApp wrapper...")
    app = agent_engines.AdkApp(
        agent=bigquery_agent,
        enable_tracing=True,
    )
    
    # Deploy to Agent Engine
    print("\n🚀 Deploying to Vertex AI Agent Engine...")
    try:
        remote_app = agent_engines.create(
            display_name="usda-bigquery-agent",
            agent_engine=app,
            requirements=requirements
        )
        
        print("\n✅ Deployment successful!")
        print(f"📍 Resource Name: {remote_app.resource_name}")
        print(f"🌐 Agent Engine ID: {remote_app.resource_name.split('/')[-1]}")
        
        # Extract useful information
        parts = remote_app.resource_name.split('/')
        project_number = parts[1]
        location = parts[3]
        engine_id = parts[5]
        
        print(f"\n📋 Deployment Details:")
        print(f"  Project: {config.project_id}")
        print(f"  Project Number: {project_number}")
        print(f"  Location: {location}")
        print(f"  Engine ID: {engine_id}")
        print(f"  Full Resource Name: {remote_app.resource_name}")
        
        print(f"\n🔗 You can access your agent at:")
        print(f"  https://console.cloud.google.com/vertex-ai/agent-builder/engines/{engine_id}/overview?project={config.project_id}")
        
        return remote_app
        
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        raise


async def test_deployed_agent(resource_name: str):
    """Test the deployed agent with sample queries."""
    print(f"\n🧪 Testing deployed agent: {resource_name}")
    
    # Note: This is a placeholder for testing deployed agents
    # The actual testing would require the Agent Engine client
    test_queries = [
        "List all tables in the dataset",
        "How many rows are in the food table?",
        "What are the top 5 foods highest in protein?"
    ]
    
    print("📝 Test queries prepared:")
    for i, query in enumerate(test_queries, 1):
        print(f"  {i}. {query}")
    
    print("\n💡 To test your deployed agent:")
    print("  1. Go to the Vertex AI console")
    print("  2. Navigate to Agent Builder > Engines")
    print("  3. Find your 'usda-bigquery-agent'")
    print("  4. Use the chat interface to test queries")


def main():
    """Main deployment function."""
    try:
        # Deploy the agent
        remote_app = deploy_bigquery_agent()
        
        # Test the deployment
        asyncio.run(test_deployed_agent(remote_app.resource_name))
        
        print("\n🎉 BigQuery agent deployment completed successfully!")
        
    except Exception as e:
        print(f"\n💥 Deployment failed with error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
