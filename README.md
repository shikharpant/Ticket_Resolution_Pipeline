# Ticket_Resolution_Pipeline
This is a **GST Grievance Resolution Multi-Agent System** that uses advanced RAG (Retrieval-Augmented Generation) with LangGraph orchestration for automated GST support ticket resolution. 

## Project Structure

```
├── src/                          # Main source code directory
│   ├── __init__.py
│   ├── agents/                   # Agent implementations
│   │   ├── __init__.py
│   │   ├── preprocessing_agent.py
│   │   ├── classification_agent.py
│   │   ├── retrieval_agents.py
│   │   └── resolution_agents.py
│   ├── config/                   # Configuration and settings
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── models/                   # Data models and schemas
│   │   ├── __init__.py
│   │   └── schemas.py
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── embeddings.py
│   │   └── knowledge_graph.py
│   └── workflows/                # Workflow orchestration
│       ├── __init__.py
│       └── gst_workflow.py
├── frontend/                     # Modern React frontend (NEW)
│   ├── src/
│   │   ├── components/          # UI components
│   │   ├── hooks/               # Custom React hooks
│   │   ├── lib/                 # API client and utilities
│   │   ├── types/               # TypeScript definitions
│   │   ├── pages/               # Application pages
│   │   └── utils/               # Helper functions
│   ├── public/                  # Static assets
│   ├── package.json             # Frontend dependencies
│   ├── vite.config.ts           # Vite configuration
│   └── README.md                # Frontend documentation
├── data/                         # Data storage
│   └── gst_knowledge_base/
├── faiss_index/                  # FAISS vector index
├── RAG_Docs/                     # Source documents
├── Agent_Ticket.ipynb           # Original notebook (for reference)
├── app.py                        # Legacy Streamlit frontend
├── backend_server.py            # FastAPI backend server (NEW)
├── run_frontend.py              # Frontend launcher (NEW)
├── run_full_system.py           # Complete system launcher (NEW)
├── run_web_app.py               # Streamlit launcher
├── main.py                       # Main application entry point
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables
├── knowledge_graph.db           # Knowledge graph database
├── kb_metadata.json             # Knowledge base metadata
└── processing_log.json          # Processing logs
```

## Architecture

### Multi-Agent System Pipeline
The system uses a **LangGraph workflow** with specialized agents:

1. **PreprocessingAgent** (`src/agents/preprocessing_agent.py`): Query cleaning and entity extraction
2. **ClassificationAgent** (`src/agents/classification_agent.py`): Intent and category classification, currently disabled as classification is based on user input.
3. **LocalRetrievalAgent** (`src/agents/retrieval_agents.py`): FAISS vector search with knowledge graph support
4. **WebRetrievalAgent** (`src/agents/retrieval_agents.py`): Web search integration using Tavily or DuckDuckGo 
5. **TwitterRetrievalAgent** (`src/agents/retrieval_agents.py`): Real-time GST updates from Twitter
6. **LLMReasoningAgent** (`src/agents/retrieval_agents.py`): Knowledge graph reasoning for complex queries
7. **ResolverAgent** (`src/agents/resolution_agents.py`): Issue resolution and confidence scoring
8. **ResponseGenerationAgent** (`src/agents/resolution_agents.py`): Final response formatting

### Key Components

#### Configuration (`src/config/settings.py`)
- **Centralized LLM Management**: All LLM initialization is centralized in the config
- **Model-Agnostic Design**: Easy swapping between different LLM providers
- **Lazy Initialization**: LLMs are created only when needed
- **API Key Management**: Secure handling of all API keys through environment variables

##### Available LLMs:
- `Config.get_preprocessor_llm()`: Query preprocessing 
- `Config.get_classifier_llm()`: Intent classification 
- `Config.get_resolver_llm()`: Issue resolution 
- `Config.get_reasoning_llm()`: Complex reasoning 
- `Config.get_web_query_llm()`: Web query optimization 

##### Model Configuration:
```python
# Easy LLM swapping
Config.swap_llm_provider('preprocessor', 'openai', 'gpt-4', temperature=0.1)
Config.REASONING_MODEL = "claude-3-sonnet"  # Change reasoning model
```

#### Data Models (`src/models/schemas.py`)
- **AgentState**: Central state management for agent workflow
- **Pydantic Models**: Structured data for preprocessing, classification, resolution
- **Enums**: GrievanceCategory, IntentType for standardized classification

#### Utilities (`src/utils/`)
- **embeddings.py**: Local embedding initialization and LLM setup (uses centralized config)
- **knowledge_graph.py**: Knowledge graph operations with NetworkX + SQLite

#### Workflow (`src/workflows/gst_workflow.py`)
- **GSTGrievanceResolver**: Main orchestrator class
- **create_workflow()**: LangGraph state machine construction
- **process_gst_grievance()**: Convenience function for query processing

#### Modern React Frontend (`frontend/`)
- **Professional React Interface**: Modern, production-ready UI with TypeScript
- **Glass Morphism Design**: Beautiful UI inspired by Claude/OpenAI with distinct aesthetics
- **Real-time Agent Tracking**: Live visualization of multi-agent processing with Framer Motion
- **Comprehensive Query Management**: GST categorization, submission, and history tracking
- **Responsive Design**: Mobile-first approach with adaptive layouts
- **Advanced Results Display**: Confidence scores, source attribution, and markdown rendering
- **WebSocket Integration**: Real-time updates and live agent status communication
- **Session Management**: Persistent query history with search and filtering

#### FastAPI Backend (`backend_server.py`)
- **RESTful API**: Complete API endpoints for all system operations
- **WebSocket Support**: Real-time communication for agent progress updates
- **Session Management**: Query session tracking and result storage
- **Error Handling**: Comprehensive API error responses and logging
- **Health Monitoring**: System status checks and agent availability

#### Application Launchers
- **`run_full_system.py`**: Complete system launcher (backend + frontend) with dependency checking
- **`run_frontend.py`**: Frontend-only launcher with Node.js/npm validation
- **`run_web_app.py`**: Legacy Streamlit launcher for backward compatibility

#### Legacy Streamlit Frontend (`app.py`)
- **Professional Streamlit Interface**: Modern web UI (legacy, maintained for compatibility)
- **Real-time Processing**: Live progress tracking with agent status updates
- **Session Management**: Query history and persistent state
- **Error Handling**: Comprehensive fallback mechanisms and user feedback

## Common Development Tasks

### Installation & Setup

#### Backend (Python)
```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

#### Frontend (React + TypeScript)
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Return to project root
cd ..
```

### Running the System

#### Complete System (Recommended)
```bash
# Launch both backend FastAPI server and React frontend
python run_full_system.py
```
This will start:
- Backend API: http://localhost:8000
- Frontend UI: http://localhost:3000
- API Documentation: http://localhost:8000/docs

#### Individual Components

**Frontend Only:**
```bash
# Launch React development server
python run_frontend.py

# Or manually:
cd frontend
npm run dev
```

**Backend Only:**
```bash
# Launch FastAPI server
python backend_server.py

# Or with uvicorn directly:
uvicorn backend_server:app --host 0.0.0.0 --port 8000 --reload
```

**Legacy Streamlit Interface:**
```bash
# Launch the legacy Streamlit interface
python run_web_app.py

# Or directly with Streamlit
streamlit run app.py
```

#### Command Line Interface
```bash
# Interactive mode
python main.py

# Demo mode with predefined queries
python main.py --demo

# Using individual components
from src.workflows.gst_workflow import process_gst_grievance
result = process_gst_grievance("How do I file GSTR-1?")
```

### Development Workflow

#### Backend Development
```bash
# Test individual agents
python -m src.agents.preprocessing_agent
python -m src.agents.classification_agent

# Test workflow
python -m src.workflows.gst_workflow

# Initialize all LLMs
from src.config.settings import Config
success = Config.initialize_all_llms()
```

#### Frontend Development
```bash
# Navigate to frontend directory
cd frontend

# Start development server with hot reload
npm run dev

# Type checking
npm run type-check

# Build for production
npm run build

# Lint code
npm run lint

# Preview production build
npm run preview
```

#### Full Stack Development
```bash
# Terminal 1: Start backend
python backend_server.py

# Terminal 2: Start frontend
cd frontend && npm run dev

# Access both services:
# Backend API: http://localhost:8000/docs
# Frontend UI: http://localhost:3000
```

### Adding New Documents
1. Place GST PDFs/PPTs in `RAG_Docs/` directory
2. Use document processing pipeline (see original notebook)
3. Update FAISS index and knowledge graph
4. Refresh `kb_metadata.json` with new statistics

### Testing Components
```python
# Test embeddings
from src.utils.embeddings import initialize_all
success = initialize_all()

# Test knowledge graph
from src.utils.knowledge_graph import LightweightKnowledgeGraph
graph = LightweightKnowledgeGraph()
graph.load()

# Test individual agents
from src.agents.preprocessing_agent import PreprocessingAgent
from src.config.settings import Config
agent = PreprocessingAgent(Config.get_preprocessor_llm())

# Test LLM swapping
Config.swap_llm_provider('reasoning', 'openai', 'gpt-4')
reasoning_llm = Config.get_reasoning_llm()
```

## Configuration

### Environment Variables (.env)
```
# LLM API Keys (refer to src/config/settings.py for details)
GOOGLE_API_KEY=your_google_api_key
DEEPSEEK_API_KEY=your_deepseek_api_key
TAVILY_API_KEY=your_tavily_api_key
TWITTER_BEARER_TOKEN=your_twitter_bearer_token
```

### Model Configuration
All model configurations are centralized in `src/config/settings.py`:

```python
# Current Models
PREPROCESSOR_MODEL = "grok-4-fast"
CLASSIFIER_MODEL = "deepseek-chat"
RESOLVER_MODEL = "grok-4-fast"
REASONING_MODEL = "deepseek-chat"  # Model-agnostic, can be swapped

# Easy LLM Swapping
Config.swap_llm_provider('preprocessor', 'openai', 'gpt-4')
Config.REASONING_MODEL = "claude-3-sonnet"
Config._reasoning_llm = None  # Clear cache to reinitialize
```

### Key Settings
- **Device Auto-Detection**: MPS (Apple Silicon), CUDA, or CPU
- **Temperature Settings**: Preprocessor (0.2), Classifier (0.1), Resolver (0.0), Reasoning (0.1)
- **Thresholds**: 95% confidence for resolution, 95% null response detection
- **Retrieval Limits**: 5 local results, 10 web results, 10 Twitter results

## Dependencies

### Core Libraries
- **LangChain & LangGraph**: Agent orchestration and LLM integration
- **FAISS**: Vector similarity search
- **sentence-transformers**: Local text embeddings
- **NetworkX**: Knowledge graph operations
- **Pydantic**: Data validation and serialization

### API Integrations
- **Google Generative AI**: Primary LLM (Gemini 2.5 Pro/Flash)
- **DeepSeek**: Reasoning LLM for complex analysis
- **Tavily**: Web search capabilities
- **Twitter API**: Real-time GST updates

### Modern Frontend Stack
- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Type-safe development experience with strict mode
- **Vite**: Fast build tool and development server with HMR
- **Tailwind CSS**: Utility-first CSS framework with custom design system
- **Framer Motion**: Declarative animations and gestures for smooth UI
- **React Markdown**: Rich text rendering for query results
- **Lucide React**: Beautiful, consistent icon library

### Legacy Frontend
- **Streamlit**: Modern web interface framework (maintained for compatibility)
- **Real-time Processing**: Live agent status updates with progress tracking
- **Professional UI**: Modern CSS styling with responsive design
- **Session Management**: Query history, persistent state, and user tracking

### Backend API
- **FastAPI**: Modern, fast web framework for building APIs
- **WebSocket**: Real-time bidirectional communication for agent updates
- **Pydantic**: Data validation and serialization with automatic documentation
- **Uvicorn**: ASGI server for production-grade performance

## Technical Specifications

### Backend
- **Primary LLMs**:
  - Preprocessing: "grok-4-fast"
  - Classification/Resolution:  "grok-4-fast"
  - Reasoning: "deepseek-chat" (model-agnostic, easily swappable)
- **Embedding Model**: sentence-transformers/all-MiniLM-L6-v2 (local)
- **Vector Index**: FAISS with persistent storage
- **Knowledge Graph**: NetworkX + SQLite for entity relationships
- **Orchestration**: LangGraph state machine workflow
- **Device Support**: Apple Silicon MPS, CUDA, CPU fallback
- **API Framework**: FastAPI with automatic OpenAPI documentation
- **Real-time Communication**: WebSocket for agent progress updates
- **Centralized LLM Management**: All LLMs initialized through config

### Frontend
- **Framework**: React 18 with TypeScript and strict mode
- **Build Tool**: Vite with hot module replacement
- **Styling**: Tailwind CSS with custom design tokens and glass morphism effects
- **Animations**: Framer Motion for smooth transitions and micro-interactions
- **State Management**: React hooks and context for local state
- **API Communication**: Axios with WebSocket integration for real-time updates
- **Development Server**: Vite dev server with proxy to backend API
- **Production Build**: Optimized static files with tree shaking and code splitting

## System Features

### Multi-Source Information Retrieval
- **Local Knowledge Base**: Pre-processed GST documents with semantic search
- **Web Search**: Real-time information via web search providers
- **Social Media**: Twitter integration for latest GST updates
- **Knowledge Graph**: Entity relationship reasoning for complex queries
- **LLM Reasoning**: Advanced analysis using model-agnostic reasoning LLM

### Intelligent Classification
- **Grievance Categories**: Registration, GSTR filing, E-way bill, refund, payments, etc.
- **Intent Types**: Informational, procedural, error resolution, compliance clarification
- **Confidence Scoring**: Automated quality assessment with escalation triggers

### Resolution Capabilities
- **Structured Responses**: Direct answers with detailed explanations
- **Legal Citations**: Source attribution and legal basis
- **Confidence Metrics**: Quality scoring and manual review flags
- **Escalation Logic**: Automatic escalation for low-confidence queries

### Frontend Features
- **Real-time Agent Visualization**: Live tracking of all 8 processing agents with progress bars
- **Professional Query Interface**: GST categorization with 15+ categories and rich text input
- **Advanced Results Display**: Markdown rendering, confidence visualization, and source breakdown
- **Session Management**: Persistent query history with search, filtering, and status tracking
- **Responsive Design**: Mobile-first approach with adaptive layouts for all screen sizes
- **Glass Morphism UI**: Modern design with blur effects, gradients, and smooth animations
- **Error Handling**: Comprehensive error states with user-friendly messages and recovery options
- **Accessibility**: WCAG compliant with keyboard navigation and screen reader support

## Development Guidelines

### Code Organization
- **Single Responsibility**: Each file has a specific purpose
- **Modular Design**: Components can be tested and modified independently
- **Type Hints**: All functions include proper type annotations
- **Error Handling**: Comprehensive logging and error management
- **Model-Agnostic Design**: No hardcoded model references outside config

### LLM Management
- **Centralized Configuration**: All LLM settings in `src/config/settings.py`
- **Model-Agnostic**: Easy swapping between providers without code changes
- **Lazy Initialization**: LLMs created only when needed
- **Error Handling**: Generic error messages that guide users to config
- **Cache Management**: Clear LLM caches when swapping models

### Testing Strategy
- **Unit Tests**: Test individual agents and utilities
- **Integration Tests**: Test workflow end-to-end
- **Performance Tests**: Monitor retrieval times and accuracy
- **Regression Tests**: Ensure updates don't break existing functionality

### Deployment Considerations

#### Frontend Deployment
- **Static Hosting**: Deploy to Vercel, Netlify, AWS S3 + CloudFront, or any static host
- **Build Optimization**: Automatic code splitting, tree shaking, and asset optimization
- **Environment Configuration**: Environment variables for different deployment targets
- **CDN Integration**: Optimized for global content delivery networks

#### Backend Deployment
- **Containerization**: Docker support for consistent deployment environments
- **Scalability**: Modular design supports horizontal scaling
- **API Gateway**: Integration with API Gateway services for production
- **Monitoring**: Built-in logging and health check endpoints

#### Security
- **API Keys**: Managed through environment variables
- **CORS Configuration**: Proper cross-origin resource sharing setup
- **Input Validation**: Comprehensive request validation with Pydantic models
- **Error Handling**: Secure error responses without information leakage


