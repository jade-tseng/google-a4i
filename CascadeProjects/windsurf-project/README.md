# Food & Nutrition Agent System

A comprehensive multi-agent system for food and nutrition information, built with Google Cloud ADK (Agent Development Kit).

## 🏗️ Architecture

The system has been restructured from a single monolithic file into modular components:

### Core Modules

1. **`google_utils.py`** - Google Cloud authentication and utilities
   - Handles authentication with Google Cloud services
   - Initializes Vertex AI and BigQuery
   - Provides common configuration and utilities

2. **`geocode_tool.py`** - Geocoding functionality
   - Forward geocoding (address → coordinates)
   - Reverse geocoding (coordinates → address)
   - Compatible with both legacy and modern ADK versions

3. **`bigquery_agent.py`** - BigQuery data access
   - Enhanced BigQueryAgent class for data exploration
   - ADK-compatible agent creation for USDA food database
   - Comprehensive database schema and querying capabilities

4. **`agent_deployment.py`** - Agent Engine deployment
   - Deployment manager for Google Cloud Agent Engine
   - Testing framework for agents
   - Image generation tools integration

5. **`main_agent.py`** - Main orchestrating agent
   - Coordinates all sub-agents and tools
   - Interactive chat interface
   - Demo conversation capabilities

## 🚀 Quick Start

### Prerequisites

```bash
pip install google-cloud-aiplatform[adk,agent_engines] google-auth google-genai httpx beautifulsoup4 google-cloud-storage google-cloud-bigquery pandas requests
```

### Environment Setup

1. Set up Google Cloud authentication:
   ```bash
   gcloud auth application-default login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. Set environment variables (optional):
   ```bash
   export GOOGLE_CLOUD_PROJECT=your-project-id
   export GOOGLE_MAPS_API_KEY=your-maps-api-key
   ```

### Running the System

#### Interactive Mode
```bash
python main_agent.py
```

#### Deployment Mode
```bash
python main_agent.py --deploy
```

#### Individual Components
```bash
# Test BigQuery agent
python bigquery_agent.py

# Test geocoding tools
python geocode_tool.py

# Deploy to Agent Engine
python agent_deployment.py
```

## 🤖 Agent Capabilities

### Main Agent
- **Food & Nutrition Queries**: Access to comprehensive USDA food database
- **Allergy Research**: Web-based research on allergies and dietary restrictions
- **Image Generation**: Create food-related images
- **Location Services**: Geocoding for location-based food information

### Sub-Agents

1. **BigQuery Agent** (`usda_food_information_bigquery_agent`)
   - Queries USDA food and nutrition database
   - Provides nutritional information, food categories, and ingredient data
   - Read-only access with comprehensive schema knowledge

2. **Allergen Research Agent** (`allergy_research_agent`)
   - Researches allergies and health information online
   - Uses Google Search for up-to-date information
   - Cites sources for all web-based information

3. **Image Agent** (`imagen_tool_agent`)
   - Generates food-related images using Gemini 2.5 Flash Image
   - Uploads images to Google Cloud Storage
   - Returns markdown-formatted image links

## 🛠️ Tools Available

- **BigQuery Tools**: Database querying and analysis
- **Google Search**: Web search for current information
- **Geocoding Tools**: Address/coordinate conversion
- **Image Generation**: AI-powered image creation

## 📊 Database Schema

The system works with a comprehensive USDA food database containing:

- **food**: Main food items with descriptions and categories
- **food_nutrient**: Nutritional values for foods
- **nutrient**: Nutrient definitions and units
- **food_category**: Food categorization system
- **market_acquisition**: Food sourcing information
- And many more specialized tables

## 🔧 Configuration

### Project Configuration
The system automatically detects your Google Cloud project or you can specify it:

```python
from google_utils import initialize_google_cloud

config, bq_tools = initialize_google_cloud(
    project_id="your-project-id",
    location="us-central1"
)
```

### Agent Customization
Each agent can be customized with different models and configurations:

```python
from bigquery_agent import create_usda_bigquery_agent

agent = create_usda_bigquery_agent(
    project_id="your-project",
    dataset_name="your-project.your-dataset",
    model="gemini-2.5-flash"
)
```

## 🚀 Deployment

### Local Testing
```bash
python main_agent.py
```

### Agent Engine Deployment
```bash
python agent_deployment.py
```

The deployment process:
1. Initializes Google Cloud services
2. Creates and tests agents
3. Deploys to Google Cloud Agent Engine
4. Returns deployment resource name

## 📝 Example Queries

- "List all tables in the USDA dataset"
- "What are the top 10 foods highest in protein?"
- "Give me a dinner recommendation for someone with dairy allergies"
- "Create an image of a healthy breakfast"
- "What foods are good sources of vitamin C?"
- "Find nutritional information for apples"

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure `gcloud auth application-default login` is run
   - Check project ID is correctly set

2. **BigQuery Access Issues**
   - Verify dataset exists and is accessible
   - Check BigQuery API is enabled

3. **API Key Issues**
   - Set `GOOGLE_MAPS_API_KEY` environment variable
   - Enable Maps JavaScript API in Google Cloud Console

### Debug Mode
Set environment variable for detailed logging:
```bash
export GOOGLE_CLOUD_LOG_LEVEL=DEBUG
```

## 📚 API Reference

### Core Classes

- `GoogleCloudConfig`: Configuration management
- `BigQueryAgent`: Database interaction
- `AgentDeploymentManager`: Deployment orchestration
- `FoodNutritionAgentSystem`: Main system coordinator

### Key Functions

- `initialize_google_cloud()`: Setup Google Cloud services
- `create_usda_bigquery_agent()`: Create BigQuery agent
- `get_geocoding_tools()`: Get geocoding tool instances

## 🤝 Contributing

1. Follow the modular structure
2. Add comprehensive docstrings
3. Include error handling
4. Test with both local and deployed environments

## 📄 License

This project is part of the MSDS 501 Computation course materials.
