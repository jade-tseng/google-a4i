import os
import sys
import logging

sys.path.append("..")
from callback_logging import log_query_to_model, log_model_response
from dotenv import load_dotenv
import google.cloud.logging
from google.adk import Agent
from google.genai import types
from typing import Optional, List, Dict
from google.adk.tools import google_search

from google.adk.tools.tool_context import ToolContext
from google.adk.tools.agent_tool import AgentTool
import requests

load_dotenv()

cloud_logging_client = google.cloud.logging.Client()
cloud_logging_client.setup_logging()

# Tools
def get_user_location() -> dict:
    """Gets current location based on IP address."""
    try:
        response = requests.get('https://ipapi.co/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "success",
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "city": data.get("city", "Unknown"),
                "region": data.get("region", "Unknown"),
                "country": data.get("country_name", "Unknown")
            }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

# Specialist Agents
hospital_agent = Agent(
    name="hospital_agent",
    model=os.getenv("MODEL"),
    description="Finds nearby hospitals and medical facilities",
    instruction="""Find hospitals and emergency medical facilities near the given location.

Use google_search with queries like "hospitals near [location]" or "hospitals near [latitude],[longitude]"

Present 3-5 results with:
- Facility name
- Full address
- Phone number (if available)
- Distance (if available)

Prioritize emergency rooms and trauma centers.""",
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    tools=[google_search]
)

shelter_agent = Agent(
    name="shelter_agent",
    model=os.getenv("MODEL"),
    description="Finds nearby emergency shelters and temporary housing",
    instruction="""Find emergency shelters and temporary housing near the given location.

Use google_search with queries like "emergency shelters near [location]" or "Red Cross shelters near [latitude],[longitude]"

Present 3-5 results with:
- Shelter name
- Full address
- Contact information
- Capacity/availability (if found)

Prioritize currently open and accessible shelters.""",
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    tools=[google_search]
)

dietary_agent = Agent(
    name="dietary_agent",
    model=os.getenv("MODEL"),
    description="Finds nearby food distribution sites and meal services",
    instruction="""Find food distribution sites and emergency meal services near the given location.

Use google_search with queries like "food banks near [location]" or "emergency food near [latitude],[longitude]"

Present 3-5 results with:
- Organization name
- Full address
- Operating hours (if available)
- Contact information

Prioritize currently operating sites.""",
    before_model_callback=log_query_to_model,
    after_model_callback=log_model_response,
    tools=[google_search]
)

# Root Orchestrator Agent
root_agent = Agent(
    name="emergency_responder",
    model=os.getenv("MODEL"),
    description="Disaster emergency responder coordinating resource searches",
    instruction="""You are a compassionate disaster emergency responder helping people find critical resources.

LOCATION HANDLING:
- If user asks about resources "near me" or doesn't specify location: call get_user_location() first
- Extract the latitude, longitude, and city from the location result
- If user provides a specific location (city, address): use that instead

ROUTING TO SPECIALISTS:
When you have the location, transfer to the appropriate specialist agent:
- For shelters: transfer to shelter_agent with "Find emergency shelters near [city] at coordinates [latitude], [longitude]"
- For hospitals: transfer to hospital_agent with "Find hospitals near [city] at coordinates [latitude], [longitude]"
- For food: transfer to dietary_agent with "Find food distribution sites near [city] at coordinates [latitude], [longitude]"

Always be empathetic and clear - people are in crisis situations.""",
    generate_content_config=types.GenerateContentConfig(
        temperature=0.3,
    ),
    tools=[get_user_location, AgentTool(agent=shelter_agent), AgentTool(agent=hospital_agent), AgentTool(agent=dietary_agent)]
)