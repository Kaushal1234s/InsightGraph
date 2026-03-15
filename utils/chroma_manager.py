"""
ChromaDB Manager for InsightGraph RAG System
"""

import os
import uuid
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import PyPDF2
import logging

logger = logging.getLogger(__name__)

class ChromaManager:
    """Manages ChromaDB operations for RAG system"""
    
    def __init__(self, persist_directory: str = "chroma_db"):
        self.persist_directory = persist_directory
        self.client = chromadb.PersistentClient(path=persist_directory)
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection = None
        self._initialize_collection()
    
    def _initialize_collection(self):
        """Initialize or get the documents collection"""
        try:
            self.collection = self.client.get_collection("documents")
            logger.info("Loaded existing collection")
        except Exception:
            self.collection = self.client.create_collection(
                name="documents",
                metadata={"description": "Document chunks for RAG"}
            )
            logger.info("Created new collection")
    
    def extract_pdf_text(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = ""
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                
                return text_content.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return f"Error extracting PDF content: {str(e)}"
    
    def create_chunks(self, text: str, chunk_size: int = 1000) -> List[str]:
        """Create meaningful chunks from text"""
        try:
            # Split by paragraphs first
            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
            
            # Create chunks of reasonable size
            chunks = []
            current_chunk = ""
            
            for paragraph in paragraphs:
                if len(current_chunk) + len(paragraph) <= chunk_size:
                    current_chunk += paragraph + "\n\n"
                else:
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph + "\n\n"
            
            # Add the last chunk
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            
            # Ensure we have at least some chunks
            if not chunks and text.strip():
                chunks = [text[:chunk_size]]
            
            return chunks
        except Exception as e:
            logger.error(f"Error creating chunks: {e}")
            return [f"Error processing text: {str(e)}"]
    
    def add_document(self, file_path: str, filename: str) -> Dict[str, Any]:
        """Add a document to ChromaDB"""
        try:
            # Extract text from PDF
            text_content = self.extract_pdf_text(file_path)
            
            # Create chunks
            chunks = self.create_chunks(text_content)
            
            # Create embeddings
            embeddings = self.embedder.encode(chunks)
            
            # Prepare metadata
            documents = chunks
            metadatas = [
                {
                    "filename": filename,
                    "chunk_id": f"{filename}_{i}",
                    "page": i + 1,
                    "chunk_index": i
                }
                for i in range(len(chunks))
            ]
            ids = [str(uuid.uuid4()) for _ in range(len(chunks))]
            
            # Add to collection
            self.collection.add(
                documents=documents,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
                ids=ids
            )
            
            return {
                "status": "success",
                "filename": filename,
                "chunks_added": len(chunks),
                "message": f"Successfully processed {len(chunks)} chunks from {filename}"
            }
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return {
                "status": "error",
                "filename": filename,
                "error": str(e),
                "message": f"Failed to process {filename}: {str(e)}"
            }
    
    def search_documents(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """Search documents using similarity search"""
        try:
            # Create query embedding
            query_embedding = self.embedder.encode([query])
            
            # Search collection
            results = self.collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=n_results
            )
            
            # Format results
            contexts = []
            for i, (doc, metadata, distance) in enumerate(zip(
                results['documents'][0], 
                results['metadatas'][0], 
                results['distances'][0]
            )):
                contexts.append({
                    "text": doc,
                    "filename": metadata.get("filename", "Unknown"),
                    "page": metadata.get("page", "?"),
                    "chunk_id": metadata.get("chunk_id", f"chunk_{i}"),
                    "similarity_score": 1 - distance  # Convert distance to similarity
                })
            
            return {
                "query": query,
                "contexts": contexts,
                "total_results": len(contexts)
            }
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return {
                "query": query,
                "contexts": [],
                "total_results": 0,
                "error": str(e)
            }
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents in the collection"""
        try:
            results = self.collection.get()
            
            documents = []
            for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
                documents.append({
                    "text": doc,
                    "filename": metadata.get("filename", "Unknown"),
                    "page": metadata.get("page", "?"),
                    "chunk_id": metadata.get("chunk_id", f"chunk_{i}")
                })
            
            return documents
        except Exception as e:
            logger.error(f"Error getting documents: {e}")
            return []
    
    def delete_document(self, filename: str) -> Dict[str, Any]:
        """Delete all chunks for a specific filename"""
        try:
            # Get all documents with the filename
            results = self.collection.get()
            ids_to_delete = []
            
            for metadata, doc_id in zip(results['metadatas'], results['ids']):
                if metadata.get("filename") == filename:
                    ids_to_delete.append(doc_id)
            
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                return {
                    "status": "success",
                    "filename": filename,
                    "chunks_deleted": len(ids_to_delete),
                    "message": f"Deleted {len(ids_to_delete)} chunks from {filename}"
                }
            else:
                return {
                    "status": "success",
                    "filename": filename,
                    "chunks_deleted": 0,
                    "message": f"No chunks found for {filename}"
                }
                
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return {
                "status": "error",
                "filename": filename,
                "error": str(e),
                "message": f"Failed to delete {filename}: {str(e)}"
            }
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            results = self.collection.get()
            
            # Count unique filenames
            filenames = set()
            for metadata in results['metadatas']:
                filenames.add(metadata.get("filename", "Unknown"))
            
            return {
                "total_chunks": len(results['documents']),
                "unique_documents": len(filenames),
                "documents": list(filenames),
                "collection_name": "documents"
            }
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {
                "total_chunks": 0,
                "unique_documents": 0,
                "documents": [],
                "collection_name": "documents",
                "error": str(e)
            }
