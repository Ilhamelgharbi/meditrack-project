<div align="center">

# 🏥 MediTrack AI

### Intelligent Medication Management & Healthcare Assistant

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5+-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docker.com)
[![LangChain](https://img.shields.io/badge/LangChain-AI-FF6B35?style=for-the-badge)](https://langchain.com)

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-tech-stack">Tech Stack</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-docker-deployment">Docker</a> •
  <a href="#-api-documentation">API</a> •
  <a href="#-architecture">Architecture</a>
</p>

---

**MediTrack AI** is a comprehensive healthcare management platform combining medication tracking, patient management, and an intelligent AI assistant powered by **LangChain/LangGraph** and **Groq**. The platform supports multimodal interactions including text, voice, and image-based pill identification.

</div>

---

## ✨ Features

### 🤖 AI Medical Assistant (Rachel)
| Feature | Description |
|---------|-------------|
| **Medical RAG** | Retrieval-Augmented Generation with GALE Medical Encyclopedia |
| **Pill Identification** | Image-based medication recognition using CLIP + FAISS |
| **Voice Interaction** | Speech-to-text (Whisper) & text-to-speech (ElevenLabs) |
| **21 Specialized Tools** | Medication lookup, reminders, adherence tracking, and more |
| **Context Memory** | Maintains conversation history with SQLite persistence |
| **Multi-Role Support** | Separate agents for patients and administrators |

### 💊 Medication Management
- 📋 Prescription tracking with dosage schedules
- ⏰ Smart automated reminders via WhatsApp
- 📈 Adherence analytics with visual charts
- 🔔 Customizable notification preferences
- 📸 Pill identification by photo upload

### 👥 Multi-Role System
| Role | Capabilities |
|------|-------------|
| **Patient** | Personal dashboard, medications, reminders, AI chat, adherence stats |
| **Administrator** | Patient management, global analytics, medication catalog, system oversight |

### 📱 WhatsApp Integration
- Automated medication reminders via Twilio
- Quick reply buttons (✅ Taken / ⏭️ Skipped)
- Real-time adherence tracking from responses
- Natural conversation with AI agent

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| **FastAPI** | High-performance async REST API |
| **LangChain** | AI agent orchestration |
| **LangGraph** | Multi-step agent workflows |
| **Groq** | Ultra-fast LLM inference (Llama 3.3 70B) |
| **FAISS** | Vector similarity search for RAG |
| **CLIP** | Image embeddings for pill identification |
| **SQLAlchemy** | Database ORM with SQLite |
| **Twilio** | WhatsApp messaging integration |

### Frontend
| Technology | Purpose |
|------------|---------|
| **React 18** | Modern UI with hooks |
| **TypeScript** | Type-safe development |
| **Vite** | Lightning-fast build tooling |
| **TailwindCSS** | Utility-first styling |
| **Recharts** | Data visualization |
| **React Router** | Client-side routing |
| **Lucide Icons** | Beautiful icon set |

### DevOps
| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Multi-service orchestration |
| **GitHub Actions** | CI/CD pipelines |

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.11+**
- **Node.js 18+**
- **Docker & Docker Compose** (optional)

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/Ilhamelgharbi/meditrack-project.git
cd meditrack-project
```

### 2️⃣ Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Required: GROQ_API_KEY
# Optional: TWILIO_*, ELEVENLABS_API_KEY
```

### 3️⃣ Backend Setup
```bash
cd meditrcak

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload --port 8000
```

### 4️⃣ Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### 5️⃣ Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

---

## 🐳 Docker Deployment

### Quick Start with Docker Compose
```bash
# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### Available Compose Files
| File | Description |
|------|-------------|
| `docker-compose.yml` | Full stack (frontend + backend) |
| `docker-compose.backend.yml` | Backend only |
| `docker-compose.simple.yml` | Simplified deployment |

### Docker Services
```yaml
services:
  backend:   # FastAPI server on port 8000
  frontend:  # React app on port 80
```

---

## 📚 API Documentation

### Authentication
```http
POST /api/auth/register    # User registration
POST /api/auth/login       # User login (returns JWT)
GET  /api/auth/me          # Get current user
```

### Patient Endpoints
```http
GET  /api/patients/                    # List patients (admin)
GET  /api/patients/{id}                # Get patient details
GET  /api/patients/{id}/medications    # Patient medications
GET  /api/patients/{id}/adherence      # Adherence statistics
```

### Medication Endpoints
```http
GET  /api/medications/                 # List all medications
POST /api/medications/                 # Create medication (admin)
GET  /api/medications/{id}             # Get medication details
```

### AI Chat Endpoints
```http
POST /api/chat/message                 # Send message to AI agent
POST /api/chat/voice                   # Voice input (audio file)
POST /api/chat/identify-pill           # Pill identification (image)
GET  /api/chat/history                 # Get chat history
```

### WhatsApp Webhook
```http
POST /api/whatsapp/webhook             # Twilio incoming messages
GET  /api/whatsapp/webhook             # Webhook verification
```

> 📖 **Interactive Docs**: Visit `/docs` for Swagger UI or `/redoc` for ReDoc

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
├──────────────────────────┬──────────────────────────────────────┤
│     React Frontend       │          WhatsApp (Twilio)           │
│   (TypeScript + Vite)    │         Mobile Interface             │
└──────────────┬───────────┴──────────────────┬───────────────────┘
               │                              │
               ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER (FastAPI)                      │
├──────────────────────────────────────────────────────────────────┤
│  /auth  │  /patients  │  /medications  │  /chat  │  /whatsapp   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI AGENT LAYER (LangGraph)                  │
├─────────────────┬───────────────────────┬───────────────────────┤
│  Patient Agent  │    Admin Agent        │   WhatsApp Agent      │
│  (Rachel)       │    (Rachel)           │   (Rachel)            │
├─────────────────┴───────────────────────┴───────────────────────┤
│                         21 TOOLS                                 │
│  medication_lookup │ reminder_config │ adherence_stats │ ...    │
├─────────────────────────────────────────────────────────────────┤
│           RAG System (FAISS + Medical Knowledge Base)            │
│           Pill Identifier (CLIP + Drug Image Embeddings)         │
└─────────────────────────────┬───────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                │
├──────────────────────────┬──────────────────────────────────────┤
│   SQLite Database        │        Vector Stores (FAISS)         │
│   (Users, Medications,   │        (Medical Docs, Pill Images)   │
│    Reminders, History)   │                                      │
└──────────────────────────┴──────────────────────────────────────┘
```

---

## 📁 Project Structure

```
meditrack-project/
├── 📂 meditrcak/                 # Backend (FastAPI)
│   ├── 📂 app/
│   │   ├── 📂 agent/             # AI Agent (LangChain/LangGraph)
│   │   │   ├── agent.py          # Main agent logic
│   │   │   ├── tools/            # 21 specialized tools
│   │   │   ├── rag/              # RAG system
│   │   │   └── vectorstore/      # FAISS indexes
│   │   ├── 📂 auth/              # Authentication
│   │   ├── 📂 patients/          # Patient management
│   │   ├── 📂 medications/       # Medication management
│   │   ├── 📂 reminders/         # Reminder system
│   │   ├── 📂 adherence/         # Adherence tracking
│   │   ├── 📂 whatsapp/          # WhatsApp integration
│   │   └── 📂 database/          # SQLAlchemy models
│   ├── main.py                   # FastAPI entry point
│   ├── requirements.txt          # Python dependencies
│   └── Dockerfile                # Backend container
│
├── 📂 frontend/                  # Frontend (React + TypeScript)
│   ├── 📂 src/
│   │   ├── 📂 components/        # Reusable UI components
│   │   ├── 📂 pages/             # Route pages
│   │   ├── 📂 services/          # API services
│   │   ├── 📂 contexts/          # React contexts
│   │   └── 📂 hooks/             # Custom hooks
│   ├── package.json              # Node dependencies
│   └── Dockerfile                # Frontend container
│
├── docker-compose.yml            # Full stack deployment
├── .env.example                  # Environment template
└── README.md                     # This file
```

---

## ⚙️ Environment Variables

```env
# Required
GROQ_API_KEY=your_groq_api_key

# Optional - WhatsApp Integration
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886

# Optional - Voice Features
ELEVENLABS_API_KEY=your_elevenlabs_key

# Database
DATABASE_URL=sqlite:///./meditrack.db

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 🧪 Testing

```bash
cd meditrcak

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_agent.py -v
```

---

## 📄 License

This project is part of an academic thesis (Fil Rouge) for educational purposes.

---

## 👨‍💻 Author

**Ilham El Gharbi**  
- GitHub: [@Ilhamelgharbi](https://github.com/Ilhamelgharbi)

---

<div align="center">

**Built with ❤️ for better healthcare**

[![Made with LangChain](https://img.shields.io/badge/Made%20with-LangChain-FF6B35?style=flat-square)](https://langchain.com)
[![Powered by Groq](https://img.shields.io/badge/Powered%20by-Groq-00D4AA?style=flat-square)](https://groq.com)

</div>
