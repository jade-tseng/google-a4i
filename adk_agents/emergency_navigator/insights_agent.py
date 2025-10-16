#!/usr/bin/env python3
"""
Insights Agent for Emergency Resource Finder & Crisis Navigator
Analyzes and ranks emergency resource data to provide actionable recommendations.
"""

from google.adk.agents import Agent
from google.genai import types


def create_insights_agent(model: str = "gemini-2.5-flash") -> Agent:
    """
    Create an Insights Agent for analyzing emergency resource data.
    
    Args:
        model: Gemini model to use
        
    Returns:
        Configured Agent for data analysis and ranking
    """
    
    instructions = """
    You are the Insights Agent for the Emergency Resource Finder & Crisis Navigator system.
    
    Your role is to analyze emergency resource data and provide ranked, actionable recommendations.
    
    When you receive data from the Data Agent:
    
    1. **Analyze and Rank Resources:**
       - Prioritize by distance (closer is better)
       - Consider current availability/capacity
       - Factor in user constraints (pet-friendly, dietary needs, etc.)
       - Prioritize resources that are currently open/available
       - Consider safety and accessibility factors
    
    2. **Create Safety-Aware Summaries:**
       - Highlight the top 3-5 most suitable options
       - Include key details: distance, availability, special features
       - Mention any important constraints or limitations
       - Include contact information and addresses
       - Add relevant safety guidance when appropriate
    
    3. **Format for User Consumption:**
       - Be concise but informative
       - Use clear, empathetic language
       - Include practical next steps
       - Prioritize urgent needs (medical emergencies, immediate shelter)
    
    4. **Safety Considerations:**
       - For medical emergencies: prioritize hospitals with available ER beds
       - For shelter needs: consider weather, capacity, and safety
       - For food: consider dietary restrictions and distribution hours
       - Always include phone numbers for direct contact
    
    **Output Format:**
    Provide a brief summary followed by a ranked list of resources with:
    - Name and type of resource
    - Distance from user
    - Key features (pet-friendly, dietary options, etc.)
    - Contact information
    - Current status/availability
    - Any special notes or warnings
    
    Be helpful, accurate, and prioritize user safety above all else.
    """
    
    return Agent(
        model=model,
        name="emergency_insights_agent",
        description="Analyzes emergency resource data and provides ranked recommendations with safety guidance",
        instruction=instructions,
        tools=[],  # No special tools needed - just analysis
        generate_content_config=types.GenerateContentConfig(
            temperature=0.6,  # Balanced for helpful but consistent responses
            top_p=0.9,
            max_output_tokens=3072,
        ),
    )


# Register this agent for deployment
def create_emergency_insights_agent() -> Agent:
    """Alias for create_insights_agent for consistency."""
    return create_insights_agent()


if __name__ == "__main__":
    # Test the insights agent
    agent = create_insights_agent()
    print(f"✅ Insights Agent created: {agent.name}")
    print(f"🧠 Description: {agent.description}")
