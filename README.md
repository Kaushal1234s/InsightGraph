# InsightGraph - Agentic RAG System

Enterprise-grade Knowledge Graph RAG application built with Next.js, FastAPI, Cognee, and Neo4j Aura.

## Architecture
- **Frontend**: Next.js 14 + Tailwind + React Force Graph
- **Gateway**: FastAPI with native Cognee integration
- **Brain**: Cognee + Neo4j Aura (free tier)
- **LLM**: Groq (llama3-70b-8192)

## Quick Start

1. **Copy environment variables**
   ```bash
   cp .env.example .env
   # Add your GROQ_API_KEY to .env
   ```

2. **Install dependencies**
   ```bash
   # API dependencies
   cd apps/api
   pip install -r requirements.txt
   
   # Web dependencies  
   cd ../web
   npm install
   ```

3. **Run the services**
   ```bash
   # Start API (FastAPI + Cognee)
   cd apps/api
   python -m uvicorn main:app --reload --port 8000
   
   # Start Web (Next.js)
   cd apps/web
   npm run dev
   ```

4. **Access the application**
   - Web UI: http://localhost:3000
   - API Docs: http://localhost:8000/docs

## Project Structure
```
├── apps/
│   ├── web/          # Next.js frontend
│   └── api/          # FastAPI gateway + Cognee
├── packages/
│   └── shared/       # Shared types and schemas
├── .env.example      # Environment variables template
└── README.md
```

## Features
- PDF/ZIP file upload (80MB limit)
- Knowledge graph construction with Cognee
- Agent-powered Q&A with LangChain + Groq
- Interactive graph visualization
- Streaming responses with source citations

## Environment Variables
See `.env.example` for all required variables. Key variables:
- `GROQ_API_KEY`: Your Groq API key
- `NEO4J_*`: Neo4j Aura connection details (pre-filled)
- `MAX_UPLOAD_MB`: File upload limit (default: 80MB)
