# -*- coding: utf-8 -*-
"""
Google Cloud Utilities and Authentication
Handles authentication, project setup, and common utilities for Google Cloud services.
"""

import os
import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional
from uuid import uuid4

# Google Cloud and Authentication
import google.auth
from google.cloud import storage, bigquery
from google.auth.credentials import Credentials

# Vertex AI
import vertexai

# Google GenAI
from google import genai
from google.genai import types

# ADK Imports
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
from google.adk.tools.bigquery.config import BigQueryToolConfig, WriteMode
from google.adk.tools import google_search, agent_tool

# Other utilities
import pandas as pd
import requests
from bs4 import BeautifulSoup


class GoogleCloudConfig:
    """Configuration class for Google Cloud services."""
    
    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1"):
        self.project_id = project_id or self._get_project_id()
        self.location = location
        self.staging_bucket = None
        self.credentials = None
        self.dataset_name = f"{self.project_id}.B2AgentsForImpact"
        
    def _get_project_id(self) -> str:
        """Get project ID from gcloud config or environment."""
        try:
            # Try to get from gcloud config
            import subprocess
            result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip() != "(unset)":
                return result.stdout.strip()
        except:
            pass
        
        # Fallback to environment variable
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            raise ValueError("Could not determine project ID. Set GOOGLE_CLOUD_PROJECT environment variable.")
        return project_id


def authenticate_google_cloud(config: GoogleCloudConfig) -> Credentials:
    """Authenticate with Google Cloud using Application Default Credentials."""
    credentials, _ = google.auth.default()
    config.credentials = credentials
    
    # Test BigQuery authentication
    bq_client = bigquery.Client(project=config.project_id, credentials=credentials)
    try:
        bq_client.query("SELECT 1").result()
        print("✓ BigQuery authentication successful")
    except Exception as e:
        print(f"✗ BigQuery authentication failed: {e}")
        raise
    
    return credentials


def setup_vertex_ai(config: GoogleCloudConfig, staging_bucket: Optional[str] = None):
    """Initialize Vertex AI with project configuration."""
    if staging_bucket:
        config.staging_bucket = staging_bucket
        
    vertexai.init(
        project=config.project_id,
        location=config.location,
        staging_bucket=f"gs://{staging_bucket}" if staging_bucket else None,
    )
    
    # Set environment variables for google-genai
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
    os.environ["GOOGLE_CLOUD_PROJECT"] = config.project_id
    os.environ["GOOGLE_CLOUD_LOCATION"] = config.location
    
    print(f"✓ Vertex AI initialized for project: {config.project_id}")


def test_gemini_connection(config: GoogleCloudConfig) -> bool:
    """Test connection to Gemini API."""
    try:
        client = genai.Client(vertexai=True, project=config.project_id, location=config.location)
        resp = client.models.generate_content(model="gemini-2.5-flash", contents="hello")
        print(f"✓ Gemini API test successful: {resp.text[:50]}...")
        return True
    except Exception as e:
        print(f"✗ Gemini API test failed: {e}")
        return False


def create_unique_bucket(location: str = "US", prefix: str = "nbkt") -> storage.Bucket:
    """
    Create a Google Cloud Storage bucket with a randomly generated, globally unique name.

    Args:
        location: GCS bucket location/region (e.g., "US", "EU", "us-central1").
        prefix: Optional short prefix for readability; must be lowercase letters/digits/hyphens.

    Returns:
        The created google.cloud.storage.bucket.Bucket object.
    """
    client = storage.Client()
    # Bucket name rules: 3–63 chars, lowercase letters/digits/hyphens, must start/end with letter or digit.
    # Use a UUID4 hex (32 chars) trimmed to keep name short while being vanishingly collision-prone.
    unique_suffix = uuid4().hex[:20]  # 20 hex chars = 80 bits of entropy
    bucket_name = f"{prefix}-{unique_suffix}"

    # Very unlikely collision; still, try once more if it happens.
    try:
        bucket = client.bucket(bucket_name)
        bucket = client.create_bucket(bucket, location=location)
        print(f"✓ Created bucket: {bucket.name} (location: {bucket.location}) in project: {client.project}")
        return bucket
    except Exception as e:
        if "You already own this bucket" in str(e) or "Conflict" in str(e) or "already exists" in str(e):
            # Regenerate once and retry
            bucket_name = f"{prefix}-{uuid4().hex[:20]}"
            bucket = client.bucket(bucket_name)
            bucket = client.create_bucket(bucket, location=location)
            print(f"✓ Created bucket on retry: {bucket.name} (location: {bucket.location}) in project: {client.project}")
            return bucket
        raise


def setup_bigquery_tools(config: GoogleCloudConfig) -> BigQueryToolset:
    """Setup BigQuery tools for ADK agents."""
    if not config.credentials:
        raise ValueError("Credentials not initialized. Call authenticate_google_cloud first.")
    
    bq_credentials = BigQueryCredentialsConfig(credentials=config.credentials)
    bq_tool_cfg = BigQueryToolConfig(write_mode=WriteMode.BLOCKED)  # Read-only by default
    
    bq_tools = BigQueryToolset(
        credentials_config=bq_credentials,
        bigquery_tool_config=bq_tool_cfg
    )
    
    print("✓ BigQuery tools configured")
    return bq_tools


def initialize_google_cloud(project_id: Optional[str] = None, 
                          location: str = "us-central1",
                          create_staging_bucket: bool = True) -> tuple[GoogleCloudConfig, BigQueryToolset]:
    """
    Complete initialization of Google Cloud services.
    
    Returns:
        Tuple of (config, bigquery_tools)
    """
    print("🚀 Initializing Google Cloud services...")
    
    # Setup configuration
    config = GoogleCloudConfig(project_id, location)
    print(f"✓ Project ID: {config.project_id}")
    print(f"✓ Location: {config.location}")
    
    # Authenticate
    authenticate_google_cloud(config)
    
    # Create staging bucket if needed
    staging_bucket_name = None
    if create_staging_bucket:
        try:
            bucket = create_unique_bucket(location="US", prefix="agent-engine-staging")
            staging_bucket_name = bucket.name
        except Exception as e:
            print(f"⚠️  Could not create staging bucket: {e}")
    
    # Setup Vertex AI
    setup_vertex_ai(config, staging_bucket_name)
    
    # Test Gemini connection
    test_gemini_connection(config)
    
    # Setup BigQuery tools
    bq_tools = setup_bigquery_tools(config)
    
    print("✅ Google Cloud initialization complete!")
    return config, bq_tools


# Constants and common configurations
MODEL = "gemini-2.5-flash"

# Default agent generation config
DEFAULT_AGENT_CONFIG = types.GenerateContentConfig(
    temperature=0.6,
    top_p=0.9,
    max_output_tokens=32768,
)

# Image generation config
IMAGE_GENERATION_CONFIG = types.GenerateContentConfig(
    temperature=1.0,
    top_p=0.95,
    max_output_tokens=4096,
    response_modalities=["IMAGE"],
    safety_settings=[
        types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
        types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
        types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
        types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
    ],
)
