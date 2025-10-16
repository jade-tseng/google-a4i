#!/usr/bin/env python3
"""
Emergency Resource Finder & Crisis Navigator Agent for ADK Web Server
"""

import os

# Set up Vertex AI environment variables
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "true"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

import vertexai

# Import the root agent from local file
from .root_agent import root_agent

print(f"✅ Emergency Resource Finder & Crisis Navigator Agent loaded for ADK web server")
print(f"🚨 Agent: {root_agent.name}")
print(f"📋 Description: {root_agent.description}")
