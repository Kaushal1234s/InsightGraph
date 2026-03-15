"""
LLM Manager for InsightGraph RAG System
"""

import os
from typing import List, Dict, Any, Optional
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

class LLMManager:
    """Manages LLM interactions for RAG system"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url=os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
        )
        self.model = "llama-3.3-70b-versatile"
    
    def get_system_prompt(self) -> str:
        """Get the system prompt for LLM"""
        return """
You are InsightGraph, an intelligent assistant that helps users analyze and understand documents from a knowledge base.

Your role is to:
1. Provide accurate, specific answers based on the retrieved document chunks
2. Always cite your sources with filenames and page numbers
3. Be helpful and conversational
4. If information is insufficient, clearly state what's missing
5. Use bullet points for structured information

Guidelines:
- Always reference specific content from the provided chunks
- Use bullet points for lists (skills, experience, education, etc.)
- If you find skills, list them clearly
- If you find experience, summarize key points
- Never make up information not present in the chunks
- Include similarity scores when relevant
"""
    
    def format_chat_prompt(self, question: str, contexts: List[Dict[str, Any]]) -> str:
        """Format chat prompt with contexts"""
        context_text = ""
        for i, ctx in enumerate(contexts, 1):
            context_text += f"Context {i} (Similarity: {ctx.get('similarity_score', 0):.2f}):\n"
            context_text += f"{ctx.get('text', '')}\n"
            if ctx.get('filename'):
                context_text += f"[Source: {ctx['filename']}, Page {ctx.get('page', '?')}]\n"
            context_text += "\n"
        
        return f"""
Based on the retrieved document chunks, please provide a helpful response to the user's question: "{question}"

Retrieved Contexts:
{context_text}

Instructions:
1. Analyze the provided document chunks carefully
2. Extract relevant information that answers the user's question
3. Structure your response clearly with bullet points or numbered lists
4. Always cite the source documents and page numbers
5. If multiple documents are relevant, organize information by document
6. Be specific and factual - only use information from the chunks
7. Mention similarity scores if they're high (>0.7)

Response Format:
- Start with a direct answer
- Use bullet points for lists (skills, experience, education, etc.)
- Include source citations like [Source: Document Name, Page X, Similarity: 0.85]
- End with a helpful follow-up question if appropriate
"""
    
    def generate_response(self, question: str, contexts: List[Dict[str, Any]], 
                         max_tokens: int = 1000, stream: bool = False) -> Dict[str, Any]:
        """Generate response from LLM"""
        try:
            if not contexts:
                # No documents found response
                messages = [
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": f"I searched for '{question}' but found no relevant documents. Please help the user understand this and suggest how they can get better results."}
                ]
            else:
                # Normal response with contexts
                system_prompt = self.get_system_prompt()
                user_prompt = self.format_chat_prompt(question, contexts)
                
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            
            if stream:
                # Streaming response
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=True,
                    max_tokens=max_tokens
                )
                return {"stream": response, "type": "stream"}
            else:
                # Non-streaming response
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    stream=False,
                    max_tokens=max_tokens
                )
                return {
                    "content": response.choices[0].message.content,
                    "type": "complete",
                    "usage": response.usage.dict() if response.usage else None
                }
                
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            return {
                "error": str(e),
                "type": "error",
                "content": f"I encountered an error while processing your request: {str(e)}"
            }
    
    def get_error_response(self, error: str, task: str) -> str:
        """Get formatted error response"""
        return f"""
I encountered an error while processing your request.

Error Details: {error}

What I was trying to do: {task}

Please try:
1. Rephrasing your question
2. Using different keywords
3. Checking if documents are uploaded

I'm here to help - would you like to try again?
"""
