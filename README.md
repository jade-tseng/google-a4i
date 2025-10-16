# Emergency Resource Finder & Crisis Navigator

A multi-agent system for finding emergency resources like shelters, hospitals, and food centers during crisis situations, built with Google Cloud ADK (Agent Development Kit).

## 🚨 System Overview

This system helps users find nearby emergency resources with safety-first guidance. It uses a coordinated multi-agent approach to query emergency resource databases and provide ranked, actionable recommendations.

## 🏗️ Architecture

### ADK Agent Structure
```
adk_agents/
└── emergency_navigator/           # Single ADK application
    ├── __init__.py               # Package initialization
    ├── agent.py                  # ADK entry point
    ├── root_agent.py            # Main orchestrating agent
    ├── data_agent.py            # Emergency data queries
    ├── insights_agent.py        # Resource analysis & ranking
    └── .env                     # Environment configuration
```

### Agent Roles

1. **Root Agent** (`erfcn_root_agent`)
   - Main orchestrator for emergency resource navigation
   - Interprets user intent and coordinates sub-agents
   - Provides safety-first responses with emergency contacts

2. **Data Agent** (`emergency_data_agent`)
   - Queries BigQuery for emergency resource data
   - Handles location-based searches and filtering
   - Accesses shelters, hospitals, and food distribution centers

3. **Insights Agent** (`emergency_insights_agent`)
   - Analyzes and ranks emergency resources
   - Considers distance, availability, and user constraints
   - Provides safety-aware recommendations

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

#### Local ADK Web Server (Recommended)
```bash
# Start the web server for interactive testing
adk web adk_agents --port 8080

# Access at: http://127.0.0.1:8080
```

#### Deploy to Google Agent Engine
```bash
# Deploy agents to Google Cloud (if individual agents exist)
python deploy.py --list                    # List available agents
python deploy.py --agent emergency_data   # Deploy specific agent
```

## 🤖 System Capabilities

### Emergency Resource Types
- **Shelters**: Emergency housing with capacity, pet policies, accessibility info
- **Hospitals**: Emergency rooms with bed availability and specialties
- **Food Centers**: Distribution centers with dietary options and hours

### Key Features
- **Location-Based Search**: Uses geocoding to find nearby resources
- **Smart Filtering**: Pet-friendly, dietary restrictions, capacity requirements
- **Safety-First Responses**: Emergency contacts and crisis guidance
- **Real-Time Data**: Current availability and status information
- **Distance Calculation**: Prioritizes closer resources

### Agent Workflow
1. **User Input**: "Find pet-friendly shelters near downtown with space for 3 people"
2. **Root Agent**: Parses intent, extracts constraints (location, pet-friendly, capacity=3)
3. **Data Agent**: Queries BigQuery for matching shelters within radius
4. **Insights Agent**: Ranks results by distance, availability, and constraints
5. **Root Agent**: Provides formatted response with top recommendations and safety info

## 🛠️ Tools Available

- **BigQuery Tools**: Emergency resource database querying
- **Geocoding Tools**: Address/coordinate conversion for location searches
- **Agent Communication**: Inter-agent messaging and coordination

## 📊 Database Schema

The system expects a BigQuery dataset with emergency resource tables:

- **shelters**: Emergency housing facilities with capacity, policies, contact info
- **hospitals**: Medical facilities with ER status, bed availability, specialties
- **food_centers**: Food distribution locations with dietary options, hours
- **locations**: Geographic data for all resources (coordinates, addresses)

### Expected Dataset Structure
```
{project_id}.emergency_resources/
├── shelters              # Emergency shelter information
├── hospitals             # Hospital and medical facilities
├── food_centers          # Food distribution centers
└── locations             # Geographic reference data
```

## 🔧 Configuration

### Environment Variables
Set up your environment in `.env` file:
```bash
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_MAPS_API_KEY=your-maps-api-key  # Optional for geocoding
```

### Dataset Configuration
The system expects emergency resource data in BigQuery:
- **Dataset**: `{project_id}.emergency_resources`
- **Location**: `us-central1` (default)
- **Access**: Read-only queries for resource information

## 🚀 Deployment Options

### Option 1: Local ADK Web Server
```bash
# Start interactive web interface
adk web adk_agents --port 8080

# Benefits:
# - Interactive web UI for testing
# - Real-time agent communication
# - Local development and debugging
```

### Option 2: Google Agent Engine
```bash
# Deploy individual agents to cloud (if available)
python deploy.py --list
python deploy.py --agent emergency_data

# Benefits:
# - Scalable cloud deployment
# - Production-ready hosting
# - Integration with other Google Cloud services
```

## 📝 Example Queries

### Shelter Searches
- "Find pet-friendly shelters near downtown with space for 3 people"
- "Emergency shelter within 10 miles that accepts families"
- "Wheelchair accessible shelters in San Francisco"

### Hospital Searches  
- "Nearest hospital with available emergency room beds"
- "Hospitals with pediatric emergency services within 15 miles"
- "Find trauma centers near highway 101"

### Food Assistance
- "Food banks with gluten-free options open today"
- "Emergency food distribution within walking distance"
- "Food centers that serve halal meals near me"

## 🔍 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Ensure `gcloud auth application-default login` is run
   - Check project ID is correctly set

2. **BigQuery Access Issues**
   - Verify emergency_resources dataset exists and is accessible
   - Check BigQuery API is enabled in Google Cloud Console
   - Ensure proper IAM permissions for BigQuery Data Viewer role

3. **ADK Web Server Issues**
   - Check if port is already in use (try different port)
   - Verify all agent files are in correct directory structure
   - Ensure relative imports are working correctly

4. **Geocoding Issues**
   - Set `GOOGLE_MAPS_API_KEY` environment variable
   - Enable Maps JavaScript API in Google Cloud Console
   - Check API key has proper permissions

### Debug Mode
Set environment variable for detailed logging:
```bash
export GOOGLE_CLOUD_LOG_LEVEL=DEBUG
```

### Testing Agent Communication
```bash
# Test individual agent files
cd adk_agents/emergency_navigator
python -c "from data_agent import create_data_agent; print('✅ Data agent works')"
python -c "from insights_agent import create_insights_agent; print('✅ Insights agent works')"
```

## 🚨 Safety Guidelines

### Emergency Protocols
- **Immediate Danger**: Always direct users to call 911 first
- **Mental Health Crisis**: Provide 988 crisis hotline (call or text)
- **Medical Emergencies**: Prioritize hospitals with available ER beds
- **Shelter Needs**: Consider weather, safety, and capacity constraints

### Data Privacy
- Only use publicly available emergency resource data
- Never store or log personal user information
- Provide general guidance, not medical advice

## 🤝 Contributing

1. **Agent Development**: Follow ADK multi-agent patterns
2. **Safety First**: Always prioritize user safety in responses  
3. **Testing**: Test both local ADK server and cloud deployment
4. **Documentation**: Update README for any structural changes

## 📄 License

This project is part of the Google Cloud ADK emergency response system demonstration.
