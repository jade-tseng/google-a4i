# -*- coding: utf-8 -*-
"""
Main Agent Orchestrator
Creates and manages the main food and nutrition agent with all sub-agents.
"""

import asyncio
from typing import List, Optional

# ADK imports
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import agent_tool, google_search
from google.genai import types

# Local imports
from google_utils import GoogleCloudConfig, initialize_google_cloud, DEFAULT_AGENT_CONFIG
from bigquery_agent import create_usda_bigquery_agent
from geocode_tool import get_geocoding_tools
from agent_deployment import (
    AgentDeploymentManager, 
    create_allergen_research_agent, 
    create_image_agent
)


class FoodNutritionAgentSystem:
    """Complete food and nutrition agent system."""
    
    def __init__(self, config: GoogleCloudConfig):
        self.config = config
        self.session_service = InMemorySessionService()
        self.app_name = "usda_food_app"
        self.user_id = "user_1"
        self.session_id = "session_001"
        
        # Agents
        self.bigquery_agent = None
        self.allergen_agent = None
        self.image_agent = None
        self.main_agent = None
        self.runner = None
        
    async def initialize(self):
        """Initialize all agents and create the main orchestrating agent."""
        print("🤖 Initializing Food & Nutrition Agent System...")
        
        # Create session
        session = await self.session_service.create_session(
            app_name=self.app_name,
            user_id=self.user_id,
            session_id=self.session_id
        )
        print(f"✓ Session created: {self.session_id}")
        
        # Create sub-agents
        print("\n📊 Creating BigQuery agent...")
        self.bigquery_agent = create_usda_bigquery_agent(
            project_id=self.config.project_id,
            dataset_name=self.config.dataset_name
        )
        
        print("🔬 Creating allergen research agent...")
        self.allergen_agent = create_allergen_research_agent()
        
        print("🎨 Creating image generation agent...")
        self.image_agent = create_image_agent()
        
        # Create main orchestrating agent
        print("🧠 Creating main orchestrating agent...")
        self.main_agent = self._create_main_agent()
        
        # Create runner
        self.runner = Runner(
            agent=self.main_agent,
            app_name=self.app_name,
            session_service=self.session_service
        )
        
        print("✅ Food & Nutrition Agent System initialized!")
        
    def _create_main_agent(self) -> Agent:
        """Create the main orchestrating agent."""
        instructions = """
        You are a friendly food and nutrition agent that helps users with:
        - Food and nutrition information from USDA databases
        - Allergy and dietary health questions
        - Food recommendations and meal planning
        - Visual content generation (food images)
        - Location-based food information
        
        You have access to several specialized sub-agents:
        - usda_food_information_bigquery_agent: Access to comprehensive USDA food and nutrition database
        - imagen_tool_agent: Can generate food-related images
        
        You also have tools for:
        - allergy_research_agent: Research allergies and health information online
        - Google Search: Find additional information when needed
        - Geocoding: Convert addresses to coordinates for location-based queries
        
        Always provide helpful, accurate information and cite sources when using web search.
        When users ask for food recommendations, consider their dietary restrictions and preferences.
        """
        
        # Get geocoding tools
        geocoding_tools = get_geocoding_tools()
        
        # Combine all tools
        tools = [
            agent_tool.AgentTool(agent=self.allergen_agent),
            google_search,
        ] + geocoding_tools
        
        return Agent(
            name="main_food_nutrition_agent",
            model="gemini-2.5-flash",
            description="Comprehensive food and nutrition assistant with access to USDA data, allergy research, and image generation.",
            instruction=instructions,
            tools=tools,
            sub_agents=[self.bigquery_agent, self.image_agent],
            generate_content_config=DEFAULT_AGENT_CONFIG,
        )
    
    async def chat(self, message: str) -> str:
        """Send a message to the agent and get a response."""
        if not self.runner:
            raise RuntimeError("Agent system not initialized. Call initialize() first.")
        
        content = types.Content(role='user', parts=[types.Part(text=message)])
        final_response = "Agent did not produce a final response."
        
        async for event in self.runner.run_async(
            user_id=self.user_id,
            session_id=self.session_id,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response = event.content.parts[0].text
                elif event.actions and event.actions.escalate:
                    final_response = f"Agent escalated: {event.error_message or 'No specific message.'}"
                break
        
        return final_response
    
    async def run_demo_conversation(self):
        """Run a demonstration conversation with the agent."""
        demo_questions = [
            "List all tables in the USDA dataset.",
            "What are the top 10 foods highest in protein per 100g?",
            "How many rows are in the food table?",
            "Give me a dinner recommendation for someone with allergies to dairy and nuts. Include a meat, starch, and vegetable.",
            "Create an image of a prepared steak dinner in a cozy atmosphere.",
            "What foods are good sources of vitamin C?",
            "Find the nutritional information for apples.",
            "What should someone with celiac disease avoid eating?"
        ]
        
        print("\n🗣️  Starting demo conversation...")
        print("=" * 60)
        
        for i, question in enumerate(demo_questions, 1):
            print(f"\n[{i}/{len(demo_questions)}] User: {question}")
            print("-" * 40)
            
            try:
                response = await self.chat(question)
                print(f"Agent: {response}")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            print("-" * 40)
    
    def get_agent_info(self) -> dict:
        """Get information about all agents in the system."""
        return {
            "main_agent": {
                "name": self.main_agent.name if self.main_agent else None,
                "description": self.main_agent.description if self.main_agent else None,
            },
            "sub_agents": [
                {
                    "name": self.bigquery_agent.name if self.bigquery_agent else None,
                    "description": self.bigquery_agent.description if self.bigquery_agent else None,
                },
                {
                    "name": self.image_agent.name if self.image_agent else None,
                    "description": self.image_agent.description if self.image_agent else None,
                }
            ],
            "tools": [
                "Google Search",
                "Geocoding Tools",
                "Allergen Research Agent"
            ],
            "config": {
                "project_id": self.config.project_id,
                "location": self.config.location,
                "dataset_name": self.config.dataset_name,
            }
        }


async def main():
    """Main function to run the food nutrition agent system."""
    print("🚀 Starting Food & Nutrition Agent System...")
    
    try:
        # Initialize Google Cloud
        print("☁️  Initializing Google Cloud...")
        config, _ = initialize_google_cloud()
        
        # Create and initialize agent system
        agent_system = FoodNutritionAgentSystem(config)
        await agent_system.initialize()
        
        # Print system info
        print("\n📋 Agent System Information:")
        info = agent_system.get_agent_info()
        print(f"Project: {info['config']['project_id']}")
        print(f"Dataset: {info['config']['dataset_name']}")
        print(f"Main Agent: {info['main_agent']['name']}")
        print(f"Sub-agents: {len(info['sub_agents'])}")
        print(f"Tools: {len(info['tools'])}")
        
        # Run demo conversation
        await agent_system.run_demo_conversation()
        
        print("\n✅ Demo completed successfully!")
        
        # Interactive mode
        print("\n💬 Entering interactive mode (type 'quit' to exit)...")
        while True:
            try:
                user_input = input("\nYou: ").strip()
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                if user_input:
                    response = await agent_system.chat(user_input)
                    print(f"\nAgent: {response}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n👋 Goodbye!")
        
    except Exception as e:
        print(f"❌ Failed to initialize system: {e}")
        raise


def create_simple_agent_for_deployment() -> Agent:
    """Create a simplified version of the main agent for deployment."""
    print("🚀 Creating simplified agent for deployment...")
    
    # Initialize with minimal setup
    config, _ = initialize_google_cloud(create_staging_bucket=False)
    
    # Create BigQuery agent
    bigquery_agent = create_usda_bigquery_agent(
        project_id=config.project_id,
        dataset_name=config.dataset_name
    )
    
    # Create allergen research agent
    allergen_agent = create_allergen_research_agent()
    
    # Create image agent
    image_agent = create_image_agent()
    
    # Get geocoding tools
    geocoding_tools = get_geocoding_tools()
    
    # Main agent instructions
    instructions = """
    You are a friendly food and nutrition agent that helps users with food and nutrition questions.
    You have access to USDA food databases, can research allergies, generate food images, and provide location services.
    Always provide helpful, accurate information and cite sources when using web search.
    """
    
    # Create main agent
    main_agent = Agent(
        name="main_food_nutrition_agent",
        model="gemini-2.5-flash",
        description="Comprehensive food and nutrition assistant",
        instruction=instructions,
        tools=[
            agent_tool.AgentTool(agent=allergen_agent),
            google_search,
        ] + geocoding_tools,
        sub_agents=[bigquery_agent, image_agent],
        generate_content_config=DEFAULT_AGENT_CONFIG,
    )
    
    print("✅ Simplified agent created for deployment")
    return main_agent


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--deploy":
        # Create agent for deployment
        agent = create_simple_agent_for_deployment()
        print(f"Agent '{agent.name}' ready for deployment")
    else:
        # Run full interactive system
        asyncio.run(main())
