# HR Resource Query Chatbot

## Overview

An AI-powered HR assistant chatbot that helps HR teams find employees using natural language processing and Retrieval-Augmented Generation (RAG). The system allows users to ask questions like "Find Python developers with 3+ years experience" and get intelligent, contextual responses with matching employee recommendations.

## Features

### Core Features
- **Natural Language Queries**: Ask questions in plain English
- **RAG-Powered Responses**: Intelligent retrieval, augmentation, and generation
- **Semantic Search**: Uses sentence transformers for semantic similarity
- **Real-time Chat Interface**: Interactive Streamlit frontend
- **Advanced Filtering**: Structured search with multiple criteria
- **Rich Analytics Dashboard**: Visualization of employee data and statistics

### Advanced Features
- **Multi-modal Search**: Combine natural language with structured filters
- **Confidence Scoring**: Each response includes confidence metrics
- **Employee Profiles**: Detailed information with projects and specializations
- **Department Analytics**: Distribution and statistics by department
- **Skills Analysis**: Most in-demand skills and expertise mapping
- **Availability Tracking**: Real-time availability status

## Architecture

### System Components
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │────│    FastAPI       │────│   RAG System    │
│   Frontend      │    │    Backend       │    │   + Embeddings  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  User Interface │    │   REST API       │    │ Sentence        │
│  Chat & Search  │    │   Endpoints      │    │ Transformers    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### RAG Pipeline
1. **Retrieval**: Query encoding and semantic similarity search
2. **Augmentation**: Context combination with employee profiles
3. **Generation**: Natural language response formatting

### Technology Stack
- **Backend**: FastAPI, Python 3.8+
- **Frontend**: Streamlit
- **AI/ML**: Sentence Transformers, scikit-learn
- **Data**: JSON-based employee database
- **API**: RESTful with automatic OpenAPI documentation

## Setup & Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Backend Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd hr-chatbot
```

2. **Set up backend environment**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Create sample data**
```bash
mkdir -p data
# The system includes built-in sample data with 16 employees
```

4. **Start the FastAPI server**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000` with automatic documentation at `http://localhost:8000/docs`

### Frontend Setup

1. **Set up frontend environment**
```bash
cd frontend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Start Streamlit application**
```bash
streamlit run streamlit_app.py
```

The frontend will be available at `http://localhost:8501`

### Quick Start (All-in-One)
```bash
# Terminal 1 - Backend
cd backend && uvicorn main:app --reload

# Terminal 2 - Frontend  
cd frontend && streamlit run streamlit_app.py
```

## API Documentation

### Core Endpoints

#### POST /chat
Process natural language queries and return AI-generated responses.

**Request:**
```json
{
  "query": "Find Python developers with 3+ years experience",
  "max_results": 5
}
```

**Response:**
```json
{
  "response": "Based on your requirements, I found 3 excellent candidates...",
  "matched_employees": [...],
  "confidence_score": 0.85
}
```

#### GET /employees
Retrieve all employees in the system.

#### GET /employees/search
Structured search with filters:
- `skills`: Comma-separated skills
- `min_experience`: Minimum years of experience
- `max_experience`: Maximum years of experience
- `availability`: available, busy, on_leave
- `department`: Department name
- `max_results`: Maximum results to return

#### GET /employees/{employee_id}
Get specific employee by ID.

#### GET /stats
System statistics including employee counts, skill distribution, and department analytics.

### Example API Calls

```bash
# Natural language query
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"query": "Find React developers for healthcare project"}'

# Structured search
curl "http://localhost:8000/employees/search?skills=Python,AWS&min_experience=3&availability=available"

# Get statistics
curl "http://localhost:8000/stats"
```

### Sample Interactions

```
User: "Find Python developers with 3+ years experience"
Bot: "I found 3 excellent candidates:

**Alice Johnson** (5 years experience)
• Skills: Python, React, AWS, Docker, FastAPI
• Recent projects: E-commerce Platform, Healthcare Dashboard
• Status: available | Location: Austin

**Dr. Sarah Chen** (6 years experience)  
• Skills: Python, TensorFlow, PyTorch, Machine Learning
• Recent projects: Medical Diagnosis Platform, X-ray Analysis
• Status: available | Location: San Francisco

**Michael Rodriguez** (4 years experience)
• Skills: Python, scikit-learn, pandas, Healthcare Data
• Recent projects: Patient Risk Prediction System
• Status: available | Location: New York"
```



# API Configuration
API_HOST=localhost
API_PORT=8000

# OpenAI Configuration (optional - for enhanced generation)
# OPENAI_API_KEY=your_openai_api_key_here

# Streamlit Configuration
STREAMLIT_PORT=8501

# Development Settings
DEBUG=True
LOG_LEVEL=INFO