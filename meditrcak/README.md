
---
title: Meditrackfinal
emoji: 😻
colorFrom: green
colorTo: indigo
sdk: docker
pinned: false
---

Check out the configuration reference at https://huggingface.co/docs/hub/spaces-config-reference

# MediTrack AI Agent Backend

![MediTrack AI](https://img.shields.io/badge/MediTrack-AI%20Agent-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)
![LangChain](https://img.shields.io/badge/LangChain-0.1.0-1C3C3C?logo=chainlink)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)
![License](https://img.shields.io/badge/License-MIT-green)

The intelligent AI-powered backend system for MediTrack, featuring multimodal AI assistance, medication management, and real-time health monitoring.

## 🌟 Core Features

### 🤖 Multimodal AI Assistant
- **Conversational AI**: Natural language medical queries and assistance
- **Voice Integration**: Speech-to-text and text-to-speech capabilities
- **Image Analysis**: Medical image processing and pill identification
- **Document Processing**: Medical report analysis and insights

### 💊 Medication Intelligence
- **Smart Adherence Tracking**: Real-time medication monitoring
- **Intelligent Reminders**: Multi-channel notification system
- **Medication Knowledge Base**: Comprehensive drug information
- **Adherence Analytics**: Pattern analysis and predictive insights

### 🏥 Healthcare Management
- **Patient Profile Management**: Complete health records
- **Medical History Tracking**: Longitudinal health data
- **Emergency Detection**: Automatic critical condition alerts
- **Provider Communication**: Integrated healthcare coordination

### 🔄 Real-Time Systems
- **WhatsApp Integration**: Direct patient communication
- **Push Notifications**: Instant mobile alerts
- **WebSocket Support**: Real-time data streaming
- **Automated Scheduling**: Intelligent reminder timing

## 🏗️ System Architecture

```
meditrcak/
├── app/
│   ├── agent/               # AI Agent Core System
│   │   ├── tools/           # Specialized agent tools
│   │   │   ├── medical/     # Medical analysis tools
│   │   │   ├── patient/     # Patient management tools
│   │   │   ├── medication/  # Medication tools
│   │   │   └── reminder/    # Reminder system tools
│   │   ├── rag/             # RAG knowledge base system
│   │   │   ├── retriever/   # Document retrieval
│   │   │   ├── generator/   # Response generation
│   │   └── vectorstore/     # FAISS vector database
│   ├── auth/                # Authentication & JWT
│   │   ├── jwt/             # JWT token management
│   │   ├── oauth/           # OAuth integration
│   │   └── security/        # Security utilities
│   ├── patients/            # Patient management API
│   │   ├── models/          # Patient data models
│   │   ├── routes/          # Patient API endpoints
│   │   └── services/        # Patient business logic
│   ├── medications/         # Medication system
│   │   ├── catalog/         # Drug database
│   │   ├── assignments/     # Patient medication assignments
│   │   └── interactions/    # Drug interaction checking
│   ├── reminders/           # Reminder scheduling system
│   │   ├── scheduler/       # Reminder scheduling logic
│   │   ├── delivery/        # Multi-channel delivery
│   │   └── escalation/      # Follow-up system
│   ├── adherence/           # Adherence tracking
│   │   ├── tracking/        # Real-time monitoring
│   │   ├── analytics/       # Adherence analytics
│   │   └── predictions/     # ML-based predictions
│   ├── whatsapp/            # WhatsApp integration
│   │   ├── webhook/         # Twilio webhook handler
│   │   ├── messaging/       # Message templates
│   │   └── templates/       # WhatsApp templates
│   ├── database/            # Database layer
│   │   ├── models/          # SQLAlchemy models
│   │   ├── connection/      # Database connections
│   │   └── migrations/      # Database migrations
│   ├── config/              # Configuration management
│   │   ├── settings/        # App settings
│   │   ├── environment/     # Environment variables
│   │   └── logging/         # Logging configuration
│   └── utils/               # Utility functions
│       ├── tts/             # Text-to-speech utilities
│       ├── stt/             # Speech-to-text utilities
│       ├── image/           # Image processing
│       └── notifications/   # Notification helpers
├── tests/                   # Comprehensive test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   ├── e2e/                 # End-to-end tests
│   └── fixtures/            # Test data fixtures
├── vectorstore/             # Vector database storage
│   ├── db_faiss/            # FAISS index files
│   └── metadata/            # Vector metadata
├── uploads/                 # File upload storage
│   ├── images/              # Medical images
│   ├── documents/           # Medical documents
│   └── audio/               # Voice recordings
├── scripts/                 # Utility scripts
│   ├── setup_database.py    # Database initialization
│   ├── populate_data.py     # Sample data population
│   └── backup_restore.py    # Backup utilities
└── requirements.txt         # Python dependencies
```

## 🚀 Quick Start

### Prerequisites
- **Python**: 3.11+
- **Git**: Latest version
- **SQLite**: Default database (PostgreSQL optional)

### Installation

#### 1. Clone and Setup
```bash
git clone https://github.com/Ilhamelgharbi/projet-fill-rouge.git
cd projet-fill-rouge/meditrcak

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt

# For ML features (optional)
pip install -r requirements-ml.txt
```

#### 3. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
nano .env
```

**Required Environment Variables:**
```env
# AI Services
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# WhatsApp Integration
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890

# Security
SECRET_KEY=your-super-secret-key-here-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key

# Database (optional, defaults to SQLite)
DATABASE_URL=sqlite:///./meditrack.db

# Vector Store Paths
DB_FAISS_PATH=app/agent/vectorstore/db_faiss
PDF_DATA_PATH=app/agent/data/
```

#### 4. Database Setup
```bash
# Initialize database
python setup_database.py

# Populate sample data
python populate_sample_data.py

# Set up vector database (for AI features)
python populate_hf_database.py
```

#### 5. Start the Server
```bash
# Development mode
python main.py

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Server URLs:**
- **API**: `http://localhost:8000`
- **Documentation**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`

## 🤖 AI Agent Capabilities

### Multimodal Query Processing
```python
# Text queries
response = await agent.query("What are the side effects of aspirin?")

# Voice queries
audio_response = await agent.voice_query(audio_file)

# Image analysis
pill_info = await agent.analyze_pill(image_file)

# Combined multimodal
result = await agent.multimodal_query(text, image, audio)
```

### Medical Knowledge Base
- **RAG System**: Retrieval-augmented generation
- **Vector Search**: Semantic similarity matching
- **Medical Ontology**: Structured medical knowledge
- **Real-time Updates**: Dynamic knowledge base

### Intelligent Tools
- **Medication Lookup**: Comprehensive drug database
- **Interaction Checking**: Drug-drug interaction analysis
- **Dosage Calculation**: Personalized dosing recommendations
- **Adherence Analysis**: Pattern recognition and insights

## 📋 API Endpoints

### Authentication
```http
POST /auth/login              # User login
POST /auth/register           # User registration
POST /auth/refresh           # Token refresh
GET  /auth/me               # Current user profile
POST /auth/logout            # User logout
```

### AI Agent
```http
POST /agent/query            # Multimodal AI queries
POST /agent/upload           # File upload for analysis
POST /agent/voice            # Voice-based interactions
POST /agent/image            # Medical image analysis
GET  /agent/health          # Agent health check
POST /agent/chat             # Conversational AI
```

### Patient Management
```http
GET    /patients             # List patients (admin) / profile (user)
POST   /patients             # Create patient
GET    /patients/{id}        # Get patient details
PUT    /patients/{id}        # Update patient
DELETE /patients/{id}        # Delete patient
GET    /patients/{id}/history # Medical history
```

### Medication System
```http
GET    /medications          # List medications
POST   /medications          # Add medication
GET    /medications/{id}     # Get medication details
PUT    /medications/{id}     # Update medication
DELETE /medications/{id}     # Delete medication
GET    /medications/search   # Search medications
POST   /medications/{id}/interactions # Check interactions
```

### Reminder System
```http
GET    /reminders            # Get user reminders
POST   /reminders            # Create reminder
GET    /reminders/{id}       # Get reminder details
PUT    /reminders/{id}       # Update reminder
DELETE /reminders/{id}       # Delete reminder
POST   /reminders/{id}/log   # Log medication taken
POST   /reminders/bulk       # Bulk reminder operations
```

### WhatsApp Integration
```http
POST   /whatsapp/webhook     # Twilio webhook handler
POST   /whatsapp/send        # Send WhatsApp message
GET    /whatsapp/templates   # List message templates
POST   /whatsapp/reminder    # Send medication reminder
```

### Analytics & Reporting
```http
GET    /analytics/adherence  # Adherence analytics
GET    /analytics/patients   # Patient population metrics
GET    /analytics/medications # Medication usage stats
GET    /analytics/reminders  # Reminder effectiveness
POST   /analytics/export     # Export analytics data
```

## 🧪 Testing

### Run Test Suite
```bash
# All tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ -v --cov=app --cov-report=html

# Specific test categories
python -m pytest tests/test_agent_*.py -v    # AI agent tests
python -m pytest tests/test_api_*.py -v      # API tests
python -m pytest tests/test_reminder_*.py -v # Reminder tests
```

### Integration Testing
```bash
# Test AI agent integration
python test_agent_integration.py

# Test WhatsApp functionality
python test_whatsapp_reminders.py

# Test complete workflow
python test_full_workflow.py
```

### Load Testing
```bash
# Basic load test
python -m pytest tests/ --durations=10 -k "not slow"

# Performance profiling
python -c "import cProfile; cProfile.run('import main; main.app')"
```

## 🔧 Configuration

### Advanced Settings

#### Database Configuration
```python
# config/settings.py
DATABASE_URL = "postgresql://user:password@localhost/meditrack"
# or
DATABASE_URL = "sqlite:///./meditrack.db"  # Default
```

#### AI Model Settings
```python
# AI model configuration
GROQ_MODEL = "mixtral-8x7b-32768"  # Default model
EMBEDDING_MODEL = "text-embedding-ada-002"
VECTOR_DIMENSION = 1536
```

#### Reminder Configuration
```python
# Reminder settings
DEFAULT_LEAD_TIME = 15  # minutes
MAX_RETRY_ATTEMPTS = 3
ESCALATION_DELAY = 30   # minutes
QUIET_HOURS_START = 22  # 10 PM
QUIET_HOURS_END = 8     # 8 AM
```

## 🐳 Docker Deployment

### Build and Run
```bash
# Build the image
docker build -t meditrcak-agent .

# Run with environment variables
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_key \
  -e DATABASE_URL=sqlite:///./meditrack.db \
  -v $(pwd)/data:/app/data \
  meditrcak-agent
```

### Docker Compose
```yaml
version: '3.8'
services:
  meditrcak-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
      - ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}
      - DATABASE_URL=sqlite:///./meditrack.db
    volumes:
      - ./vectorstore:/app/vectorstore
      - ./uploads:/app/uploads
    restart: unless-stopped
```

## 📊 Monitoring & Observability

### Health Checks
```http
GET /health         # System health
GET /agent/health   # AI agent status
GET /metrics        # Prometheus metrics
```

### Logging
- **Structured Logging**: JSON format logs
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Rotation**: Automatic log file rotation
- **External Logging**: Support for ELK stack, Datadog, etc.

### Performance Monitoring
- **Response Times**: API endpoint performance
- **Memory Usage**: Resource utilization tracking
- **Error Rates**: Failure rate monitoring
- **AI Metrics**: Model performance and accuracy

## 🔒 Security

### Authentication & Authorization
- **JWT Tokens**: Secure token-based authentication
- **Role-Based Access**: Patient, Provider, Admin roles
- **API Rate Limiting**: Request throttling protection
- **Input Validation**: Comprehensive data validation

### Data Protection
- **Encryption**: Sensitive data encryption at rest
- **HTTPS Only**: Secure communication channels
- **API Keys**: Secure key management
- **Audit Logging**: Complete action tracking

## 🚀 Production Deployment

### Environment Setup
```bash
# Production environment variables
export NODE_ENV=production
export DATABASE_URL=postgresql://user:pass@host:5432/db
export REDIS_URL=redis://host:6379
export LOG_LEVEL=INFO
```

### Scaling Considerations
- **Horizontal Scaling**: Multiple app instances
- **Database Optimization**: Connection pooling
- **Caching Layer**: Redis for session and cache storage
- **Load Balancing**: Nginx or cloud load balancers

### Backup & Recovery
```bash
# Database backup
python scripts/backup_database.py

# Vector store backup
python scripts/backup_vectorstore.py

# Full system backup
python scripts/full_backup.py
```

## 🛠️ Development

### Code Quality
```bash
# Linting
flake8 app/ tests/
black app/ tests/
isort app/ tests/

# Type checking
mypy app/ --ignore-missing-imports

# Security scanning
bandit -r app/
```

### Pre-commit Hooks
```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run on all files
pre-commit run --all-files
```

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`

### Code Examples

#### Python Client
```python
import requests

# Authentication
response = requests.post("http://localhost:8000/auth/login",
    json={"email": "user@example.com", "password": "password"})
token = response.json()["access_token"]

# AI Query
headers = {"Authorization": f"Bearer {token}"}
response = requests.post("http://localhost:8000/agent/query",
    json={"query": "What medications interact with aspirin?"},
    headers=headers)
```

#### JavaScript Client
```javascript
// Authentication
const loginResponse = await fetch('/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
});
const { access_token } = await loginResponse.json();

// AI Query
const queryResponse = await fetch('/agent/query', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${access_token}`
    },
    body: JSON.stringify({ query: 'Medication adherence tips' })
});
```

## 🤝 Contributing

### Development Workflow
1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Implement** your changes with tests
4. **Commit** your changes (`git commit -m 'Add amazing feature'`)
5. **Push** to the branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request

### Code Standards
- **PEP 8**: Python style guide compliance
- **Type Hints**: Full type annotation coverage
- **Docstrings**: Comprehensive documentation
- **Testing**: Minimum 85% code coverage
- **Security**: Regular security audits

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🙏 Acknowledgments

- **MediTrack Team**: For the vision and requirements
- **Open Source Community**: For amazing AI and healthcare libraries
- **Medical Professionals**: For domain expertise and validation

---

**MediTrack AI Agent Backend** - The intelligent heart of healthcare management, powered by advanced AI and real-time systems. 🏥🤖💊
