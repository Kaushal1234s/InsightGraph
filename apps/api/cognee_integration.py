"""
Cognee integration module for InsightGraph
Handles document ingestion and graph search operations
"""

import os
import asyncio
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import aiofiles
from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)

class CogneeIntegration:
    """Integration layer for Cognee operations"""
    
    def __init__(self):
        self.neo4j_uri = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USERNAME")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.neo4j_database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        # Validate environment variables
        if not all([self.neo4j_uri, self.neo4j_user, self.neo4j_password]):
            raise ValueError("Missing required Neo4j environment variables")
        
        self.driver = None
        self._initialize_driver()
    
    def _initialize_driver(self):
        """Initialize Neo4j driver"""
        try:
            self.driver = GraphDatabase.driver(
                self.neo4j_uri,
                auth=(self.neo4j_user, self.neo4j_password)
            )
            # Test connection
            with self.driver.session(database=self.neo4j_database) as session:
                session.run("RETURN 1")
            logger.info("Neo4j connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    async def ingest_file(self, file_path: str, filename: str, document_id: str) -> Dict[str, Any]:
        """
        Ingest a file into the knowledge graph
        
        Args:
            file_path: Path to the file
            filename: Original filename
            document_id: Unique document identifier
            
        Returns:
            Dict with ingestion results
        """
        try:
            # For now, create a simple document node in Neo4j
            # TODO: Replace with actual Cognee processing
            await self._create_document_node(document_id, filename, file_path)
            
            # If it's a PDF, extract some basic info
            if filename.lower().endswith('.pdf'):
                await self._process_pdf_content(document_id, file_path)
            elif filename.lower().endswith('.zip'):
                await self._process_zip_content(document_id, file_path)
            
            return {
                "status": "success",
                "document_id": document_id,
                "message": f"Successfully ingested {filename}"
            }
            
        except Exception as e:
            logger.error(f"Error ingesting file {filename}: {e}")
            return {
                "status": "error",
                "document_id": document_id,
                "message": f"Failed to ingest {filename}: {str(e)}"
            }
    
    async def _create_document_node(self, document_id: str, filename: str, file_path: str):
        """Create a document node in Neo4j"""
        file_size = os.path.getsize(file_path)
        
        with self.driver.session(database=self.neo4j_database) as session:
            query = """
            CREATE (d:Document {
                id: $document_id,
                name: $filename,
                type: $file_type,
                size: $file_size,
                created_at: datetime()
            })
            RETURN d
            """
            
            file_type = Path(filename).suffix.lower()
            session.run(query, {
                "document_id": document_id,
                "filename": filename,
                "file_type": file_type,
                "file_size": file_size
            })
    
    async def _process_pdf_content(self, document_id: str, file_path: str):
        """Process PDF content and create chunks"""
        # TODO: Implement actual PDF processing with Cognee
        # For now, create mock chunks
        
        with self.driver.session(database=self.neo4j_database) as session:
            # Create some mock chunks
            chunks = [
                "This is the first chunk of the document.",
                "This is the second chunk containing important information.",
                "This is the third chunk with additional details."
            ]
            
            for i, chunk_text in enumerate(chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                
                # Create chunk node
                chunk_query = """
                CREATE (c:Chunk {
                    id: $chunk_id,
                    text: $text,
                    page: $page,
                    created_at: datetime()
                })
                RETURN c
                """
                session.run(chunk_query, {
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "page": i + 1
                })
                
                # Link to document
                link_query = """
                MATCH (d:Document {id: $document_id})
                MATCH (c:Chunk {id: $chunk_id})
                CREATE (d)-[:HAS_CHUNK]->(c)
                """
                session.run(link_query, {
                    "document_id": document_id,
                    "chunk_id": chunk_id
                })
    
    async def _process_zip_content(self, document_id: str, file_path: str):
        """Process ZIP file contents"""
        # TODO: Implement ZIP extraction and batch processing
        # For now, just create a document node
        pass
    
    async def search_graph(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Search the knowledge graph
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            Dict with search results including nodes, edges, and contexts
        """
        try:
            # TODO: Implement actual Cognee search
            # For now, return mock results with better matching
            
            with self.driver.session(database=self.neo4j_database) as session:
                # More flexible search - check if any query words appear in chunks
                query_words = query.lower().split()
                search_conditions = []
                for word in query_words:
                    if len(word) > 2:  # Only search words longer than 2 characters
                        search_conditions.append(f"toLower(c.text) CONTAINS '{word}'")
                
                # Fallback to return all chunks if no specific words found
                if not search_conditions:
                    search_query = """
                    MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
                    RETURN d, c, 
                           d.id as doc_id, d.name as doc_name,
                           c.id as chunk_id, c.text as chunk_text, c.page as page
                    LIMIT $limit
                    """
                    params = {"limit": top_k}
                else:
                    search_query = f"""
                    MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
                    WHERE {' OR '.join(search_conditions)}
                    RETURN d, c, 
                           d.id as doc_id, d.name as doc_name,
                           c.id as chunk_id, c.text as chunk_text, c.page as page
                    LIMIT $limit
                    """
                    params = {"limit": top_k}
                
                results = session.run(search_query, params)
                
                contexts = []
                nodes = []
                edges = []
                
                for record in results:
                    doc = record["d"]
                    chunk = record["c"]
                    
                    # Add document node
                    nodes.append({
                        "id": doc["id"],
                        "name": doc["name"],
                        "type": "document"
                    })
                    
                    # Add chunk node
                    nodes.append({
                        "id": chunk["id"],
                        "name": f"Chunk {chunk.get('page', '?')}",
                        "type": "chunk",
                        "text": chunk["text"]
                    })
                    
                    # Add edge
                    edges.append({
                        "source": doc["id"],
                        "target": chunk["id"],
                        "type": "HAS_CHUNK"
                    })
                    
                    # Add context
                    contexts.append({
                        "chunk_id": chunk["id"],
                        "text": chunk["text"],
                        "document_id": doc["id"],
                        "document_name": doc["name"],
                        "page": chunk.get("page")
                    })
                
                # If no results from word search, return some chunks anyway
                if not contexts:
                    fallback_query = """
                    MATCH (d:Document)-[:HAS_CHUNK]->(c:Chunk)
                    RETURN d, c, 
                           d.id as doc_id, d.name as doc_name,
                           c.id as chunk_id, c.text as chunk_text, c.page as page
                    LIMIT 3
                    """
                    results = session.run(fallback_query)
                    
                    for record in results:
                        doc = record["d"]
                        chunk = record["c"]
                        
                        contexts.append({
                            "chunk_id": chunk["id"],
                            "text": chunk["text"],
                            "document_id": doc["id"],
                            "document_name": doc["name"],
                            "page": chunk.get("page")
                        })
                
                return {
                    "nodes": nodes,
                    "edges": edges,
                    "contexts": contexts,
                    "query": query,
                    "total_results": len(contexts)
                }
                
        except Exception as e:
            logger.error(f"Error searching graph: {e}")
            return {
                "nodes": [],
                "edges": [],
                "contexts": [],
                "query": query,
                "total_results": 0,
                "error": str(e)
            }
    
    async def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """Get processing status for a document"""
        try:
            with self.driver.session(database=self.neo4j_database) as session:
                query = """
                MATCH (d:Document {id: $document_id})
                OPTIONAL MATCH (d)-[:HAS_CHUNK]->(c:Chunk)
                RETURN d.id as doc_id, d.name as doc_name, d.created_at as created_at,
                       count(c) as chunk_count
                """
                
                result = session.run(query, {"document_id": document_id})
                record = result.single()
                
                if record:
                    return {
                        "document_id": record["doc_id"],
                        "document_name": record["doc_name"],
                        "created_at": record["created_at"].isoformat() if record["created_at"] else None,
                        "chunk_count": record["chunk_count"],
                        "status": "completed"
                    }
                else:
                    return {
                        "document_id": document_id,
                        "status": "not_found"
                    }
                    
        except Exception as e:
            logger.error(f"Error getting document status: {e}")
            return {
                "document_id": document_id,
                "status": "error",
                "error": str(e)
            }
    
    def close(self):
        """Close Neo4j driver"""
        if self.driver:
            self.driver.close()

# Global instance
cognee_integration = CogneeIntegration()
