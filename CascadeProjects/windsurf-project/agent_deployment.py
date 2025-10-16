# -*- coding: utf-8 -*-
"""
Agent Engine Deployment Module
Handles deployment of agents to Google Cloud Agent Engine.
"""

import asyncio
from typing import Optional, List, Dict, Any

# Vertex AI Agent Engine imports
from vertexai import agent_engines
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Local imports
from google_utils import GoogleCloudConfig, initialize_google_cloud
from bigquery_agent import create_usda_bigquery_agent
from geocode_tool import get_geocoding_tools


class AgentDeploymentManager:
    """Manages deployment and testing of agents to Agent Engine."""
    
    def __init__(self, config: GoogleCloudConfig):
        self.config = config
        self.session_service = InMemorySessionService()
        self.app_name = "usda_food_app"
        self.user_id = "user_1"
        self.session_id = "session_001"
        
    async def create_session(self):
        """Create a session for testing agents."""
        session = await self.session_service.create_session(
            app_name=self.app_name,
            user_id=self.user_id,
            session_id=self.session_id
        )
        print(f"✓ Session created: App='{self.app_name}', User='{self.user_id}', Session='{self.session_id}'")
        return session
        
    def create_runner(self, agent: Agent) -> Runner:
        """Create a runner for an agent."""
        runner = Runner(
            agent=agent,
            app_name=self.app_name,
            session_service=self.session_service
        )
        print(f"✓ Runner created for agent '{agent.name}'")
        return runner
        
    async def test_agent(self, agent: Agent, test_queries: List[str]) -> Dict[str, str]:
        """Test an agent with a list of queries."""
        print(f"\n🧪 Testing agent: {agent.name}")
        print("=" * 50)
        
        runner = self.create_runner(agent)
        results = {}
        
        for query in test_queries:
            print(f"\n❓ Query: {query}")
            try:
                response = await self._call_agent_async(query, runner)
                results[query] = response
                print(f"✅ Response: {response[:200]}..." if len(response) > 200 else f"✅ Response: {response}")
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                results[query] = error_msg
                print(f"❌ {error_msg}")
                
        return results
        
    async def _call_agent_async(self, query: str, runner: Runner) -> str:
        """Send a query to an agent and return the response."""
        content = types.Content(role='user', parts=[types.Part(text=query)])
        final_response_text = "Agent did not produce a final response."
        
        async for event in runner.run_async(
            user_id=self.user_id, 
            session_id=self.session_id, 
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    final_response_text = event.content.parts[0].text
                elif event.actions and event.actions.escalate:
                    final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                break
                
        return final_response_text
        
    def deploy_to_agent_engine(self, 
                             agent: Agent, 
                             display_name: str,
                             requirements: Optional[List[str]] = None) -> Any:
        """Deploy an agent to Agent Engine."""
        print(f"\n🚀 Deploying agent '{agent.name}' to Agent Engine...")
        
        if requirements is None:
            requirements = [
                "google-cloud-aiplatform[adk,agent_engines]",
                "google-auth",
                "google-genai",
                "httpx",
                "beautifulsoup4",
                "google-cloud-storage",
                "google-cloud-bigquery",
                "google-cloud-logging",
                "google-cloud-resource-manager",
                "pandas",
                "requests"
            ]
        
        # Wrap the agent in an AdkApp object
        app = agent_engines.AdkApp(
            agent=agent,
            enable_tracing=True,
        )
        
        # Deploy to Agent Engine
        try:
            remote_app = agent_engines.create(
                display_name=display_name,
                agent_engine=app,
                requirements=requirements
            )
            
            print(f"✅ Deployment successful!")
            print(f"📍 Resource Name: {remote_app.resource_name}")
            return remote_app
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            raise


def create_image_generation_tool():
    """Create image generation tool function."""
    import time
    import uuid
    from google.cloud import storage
    from google import genai
    
    def generate_image_tool(
        prompt: str,
        *,
        bucket: str = "food-agent-generated-images",
        n: int = 1,
        return_text: bool = False,
    ) -> Dict[str, Any]:
        """Generate image(s) with Gemini 2.5 Flash Image and upload to GCS."""
        
        def _ext_for_mime(mime_type: str) -> str:
            m = (mime_type or "").lower()
            if "jpeg" in m or "jpg" in m:
                return "jpg"
            if "webp" in m:
                return "webp"
            if "png" in m:
                return "png"
            if "gif" in m:
                return "gif"
            return "png"
        
        def _upload_bytes_to_gcs(data: bytes, bucket: str, mime_type: str = "image/png") -> Dict[str, str]:
            client = storage.Client()
            bucket_obj = client.bucket(bucket)
            
            ext = _ext_for_mime(mime_type)
            blob_name = f"generated/{int(time.time())}-{uuid.uuid4().hex}.{ext}"
            
            blob = bucket_obj.blob(blob_name)
            blob.upload_from_string(data, content_type=mime_type)
            public_url = f"https://storage.googleapis.com/{bucket}/{blob_name}"
            
            return {
                "gcs_uri": f"gs://{bucket}/{blob_name}",
                "public_url": public_url,
                "mime_type": mime_type,
                "filename": blob_name,
                "markdown": f'![{blob_name}]({public_url} "Generated by Imagen")',
            }
        
        try:
            client = genai.Client(vertexai=True, project=None, location="global")
            
            contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
            response_modalities = ["IMAGE"] + (["TEXT"] if return_text else [])
            
            cfg = types.GenerateContentConfig(
                temperature=1.0,
                top_p=0.95,
                max_output_tokens=4096,
                response_modalities=response_modalities,
            )
            
            stream = client.models.generate_content_stream(
                model="gemini-2.5-flash-image-preview",
                contents=contents,
                config=cfg,
            )
            
            outputs = []
            text_out = []
            
            for chunk in stream:
                cand = getattr(chunk, "candidates", [None])[0]
                if not cand or not cand.content or not getattr(cand.content, "parts", None):
                    continue
                
                for part in cand.content.parts:
                    if getattr(part, "text", None):
                        text_out.append(part.text)
                    
                    inline = getattr(part, "inline_data", None)
                    if inline and getattr(inline, "data", None):
                        info = _upload_bytes_to_gcs(
                            inline.data,
                            bucket=bucket,
                            mime_type=inline.mime_type or "image/png",
                        )
                        outputs.append(info)
                        if len(outputs) >= n:
                            break
                
                if len(outputs) >= n:
                    break
            
            result = {"status": "success", "images": outputs}
            if return_text and text_out:
                result["text"] = "\n".join(text_out)
            return result
            
        except Exception as e:
            return {"status": "error", "error_message": str(e)}
    
    return generate_image_tool


def create_allergen_research_agent(model: str = "gemini-2.5-flash") -> Agent:
    """Create an allergen research agent."""
    from google.adk.tools import google_search
    
    instructions = """
    You are an allergen researcher.
    Use your knowledge about allergies and health, and search for information online when needed.
    When you use the Google Search tool, always cite the source of the information you find.
    Provide accurate, helpful information about food allergies, dietary restrictions, and health concerns.
    """
    
    return Agent(
        model=model,
        name="allergy_research_agent",
        description="Answer questions about allergies and related health concerns.",
        instruction=instructions,
        tools=[google_search],
        generate_content_config=types.GenerateContentConfig(
            temperature=0.6,
            top_p=0.9,
            max_output_tokens=32768,
        ),
    )


def create_image_agent(model: str = "gemini-2.5-flash") -> Agent:
    """Create an image generation agent."""
    image_tool = create_image_generation_tool()
    
    instructions = (
        "You generate images based on user prompts. "
        "When asked for an image, call `generate_image_tool` with a concise visual prompt. "
        "Return the Markdown from the tool output to the user so it can be displayed."
    )
    
    return Agent(
        model=model,
        name="imagen_tool_agent",
        description="Agent that creates images via a custom tool powered by Gemini 2.5 Flash Image.",
        instruction=instructions,
        tools=[image_tool],
        generate_content_config=types.GenerateContentConfig(
            temperature=0.6,
            top_p=0.9,
            max_output_tokens=2048,
        ),
    )


async def main():
    """Main deployment function."""
    print("🚀 Starting Agent Deployment Process...")
    
    # Initialize Google Cloud
    config, bq_tools = initialize_google_cloud()
    
    # Create deployment manager
    deployment_manager = AgentDeploymentManager(config)
    await deployment_manager.create_session()
    
    # Create agents
    print("\n🤖 Creating agents...")
    
    # BigQuery agent
    bigquery_agent = create_usda_bigquery_agent(
        project_id=config.project_id,
        dataset_name=config.dataset_name
    )
    
    # Allergen research agent
    allergen_agent = create_allergen_research_agent()
    
    # Image generation agent
    image_agent = create_image_agent()
    
    # Test queries
    test_queries = [
        "List all tables in the dataset.",
        "How many rows are in the food table?",
        "What are the top 5 foods highest in protein?"
    ]
    
    # Test BigQuery agent
    print("\n🧪 Testing BigQuery agent...")
    await deployment_manager.test_agent(bigquery_agent, test_queries[:2])
    
    # Deploy to Agent Engine
    print("\n🚀 Deploying to Agent Engine...")
    try:
        remote_app = deployment_manager.deploy_to_agent_engine(
            agent=bigquery_agent,
            display_name="usda-food-bigquery-agent"
        )
        print(f"✅ BigQuery agent deployed successfully!")
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
