from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import uuid
import os
import tempfile
import aiofiles
from dotenv import load_dotenv
from cognee_integration import cognee_integration

load_dotenv()

app = FastAPI(title="InsightGraph API", version="1.0.0")

# CORS for Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (for demo)
jobs: Dict[str, Dict[str, Any]] = {}

class AskRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str

@app.get("/")
async def root():
    return {"message": "InsightGraph API is running"}

@app.post("/v1/upload", response_model=JobResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Upload PDF or ZIP file for knowledge graph ingestion"""
    
    # Validate file type
    allowed_types = ["pdf", "zip"]
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_types)}"
        )
    
    # Validate file size (80MB)
    max_size = int(os.getenv("MAX_UPLOAD_MB", "80")) * 1024 * 1024
    file_content = await file.read()
    if len(file_content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Max size: {max_size // (1024*1024)}MB"
        )
    
    # Create job
    job_id = str(uuid.uuid4())
    document_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "pending",
        "filename": file.filename,
        "file_type": file_ext,
        "document_id": document_id,
        "progress": 0,
        "message": "File uploaded, starting ingestion..."
    }
    
    # Save file to temp location
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}")
    async with aiofiles.open(temp_file.name, 'wb') as f:
        await f.write(file_content)
    temp_file.close()
    
    # Start background ingestion
    background_tasks.add_task(
        process_file_ingestion, 
        job_id, 
        file.filename, 
        file_ext, 
        temp_file.name,
        document_id
    )
    
    return JobResponse(
        job_id=job_id,
        status="pending",
        message=f"File '{file.filename}' uploaded and processing started"
    )

@app.get("/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get ingestion job status"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return jobs[job_id]

@app.post("/v1/ask")
async def ask_question(request: AskRequest):
    """Ask question with streaming response"""
    
    async def generate_response():
        try:
            # Search the knowledge graph first
            search_results = await cognee_integration.search_graph(request.question)
            
            # Start streaming response
            yield f"data: {{\"type\": \"token\", \"content\": \"I found relevant information in your knowledge graph. \"}}\n\n"
            
            if search_results["contexts"]:
                context_count = len(search_results["contexts"])
                yield f"data: {{\"type\": \"token\", \"content\": \"Based on {context_count} relevant document chunks:\\n\\n\"}}\n\n"
                
                for i, context in enumerate(search_results["contexts"][:3]):  # Limit to top 3
                    doc_name = context["document_name"]
                    text_preview = context["text"][:200]
                    yield f"data: {{\"type\": \"token\", \"content\": \"{i+1}. From \\\"{doc_name}\\\"\"}}\n\n"
                    yield f"data: {{\"type\": \"token\", \"content\": \"{text_preview}...\\n\\n\"}}\n\n"
                
                # Send sources
                import json
                sources_json = json.dumps(search_results['contexts'])
                yield f"data: {{\"type\": \"sources\", \"sources\": {sources_json}}}\n\n"
                
                # Final answer
                yield f"data: {{\"type\": \"token\", \"content\": \"\\nBased on the retrieved information, I can help answer your question. \"}}\n\n"
                total_results = search_results['total_results']
                yield f"data: {{\"type\": \"token\", \"content\": \"The search found {total_results} relevant chunks across your documents.\"}}\n\n"
            else:
                yield f"data: {{\"type\": \"token\", \"content\": \"I could not find specific information matching your question in the uploaded documents. \"}}\n\n"
                yield f"data: {{\"type\": \"token\", \"content\": \"Try uploading relevant documents or rephrasing your question.\"}}\n\n"
            
            yield f"data: {{\"type\": \"final\", \"content\": \"Response complete.\"}}\n\n"
            
        except Exception as e:
            yield f"data: {{\"type\": \"error\", \"message\": \"Error: {str(e)}\"}}\n\n"
    
    return StreamingResponse(
        generate_response(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@app.get("/v1/graph/{document_id}")
async def get_document_graph(document_id: str):
    """Get graph visualization for a specific document"""
    try:
        # Get document and its chunks
        with cognee_integration.driver.session(database=cognee_integration.neo4j_database) as session:
            query = """
            MATCH (d:Document {id: $document_id})
            OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
            OPTIONAL MATCH (c)-[:MENTIONS]->(e:Entity)
            RETURN d, c, e
            """
            
            results = session.run(query, {"document_id": document_id})
            
            nodes = []
            edges = []
            node_ids = set()
            
            for record in results:
                doc = record["d"]
                chunk = record["c"]
                entity = record["e"]
                
                # Add document node
                if doc and doc["id"] not in node_ids:
                    nodes.append({
                        "id": doc["id"],
                        "name": doc["name"],
                        "type": "document",
                        "color": "#3b82f6",
                        "size": 10
                    })
                    node_ids.add(doc["id"])
                
                # Add chunk node
                if chunk and chunk["id"] not in node_ids:
                    nodes.append({
                        "id": chunk["id"],
                        "name": f"Chunk {chunk.get('page', '?')}",
                        "type": "chunk",
                        "color": "#10b981",
                        "size": 5
                    })
                    node_ids.add(chunk["id"])
                    
                    # Add edge from document to chunk
                    edges.append({
                        "source": doc["id"],
                        "target": chunk["id"],
                        "type": "HAS_CHUNK",
                        "color": "#94a3b8"
                    })
                
                # Add entity node and edge
                if entity and entity["id"] not in node_ids:
                    nodes.append({
                        "id": entity["id"],
                        "name": entity.get("name", entity["id"]),
                        "type": "entity",
                        "color": "#f59e0b",
                        "size": 7
                    })
                    node_ids.add(entity["id"])
                    
                    # Add edge from chunk to entity
                    edges.append({
                        "source": chunk["id"],
                        "target": entity["id"],
                        "type": "MENTIONS",
                        "color": "#94a3b8"
                    })
            
            return {
                "nodes": nodes,
                "edges": edges
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_file_ingestion(
    job_id: str, 
    filename: str, 
    file_type: str, 
    file_path: str,
    document_id: str
):
    """Background task to process file ingestion with Cognee"""
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = 10
        jobs[job_id]["message"] = "Initializing Cognee..."
        
        # Use Cognee integration
        result = await cognee_integration.ingest_file(file_path, filename, document_id)
        
        if result["status"] == "success":
            jobs[job_id]["status"] = "completed"
            jobs[job_id]["progress"] = 100
            jobs[job_id]["message"] = f"Successfully processed '{filename}'"
        else:
            jobs[job_id]["status"] = "failed"
            jobs[job_id]["message"] = result["message"]
        
        # Clean up temp file
        os.unlink(file_path)
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = f"Processing failed: {str(e)}"
        # Try to clean up temp file
        try:
            os.unlink(file_path)
        except:
            pass

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources"""
    cognee_integration.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
