"""
InsightGraph RAG System - Streamlit Version
A modern document Q&A system with ChromaDB and Groq LLM
"""

import streamlit as st
import os
import tempfile
from dotenv import load_dotenv
import time
from utils.chroma_manager import ChromaManager
from utils.llm_manager import LLMManager

# Load environment variables
load_dotenv()

# Configure page
st.set_page_config(
    page_title="InsightGraph - Document Q&A",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        color: #000000;
        font-weight: 500;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        color: #000000;
    }
    .assistant-message {
        background-color: #f3e5f5;
        border-left: 4px solid #9c27b0;
        color: #000000;
    }
    .source-citation {
        background-color: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 0.5rem;
        margin: 0.5rem 0;
        border-radius: 0.25rem;
        font-size: 0.9rem;
        color: #000000;
        font-weight: 500;
    }
    .stats-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
        color: #000000;
        font-weight: 500;
    }
    /* Streamlit base styles override */
    .stTextInput > div > div > input {
        color: #000000 !important;
        font-weight: 500;
    }
    .stTextArea > div > div > textarea {
        color: #000000 !important;
        font-weight: 500;
    }
    .stButton > button {
        color: #000000 !important;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chroma_manager' not in st.session_state:
    st.session_state.chroma_manager = ChromaManager()
if 'llm_manager' not in st.session_state:
    st.session_state.llm_manager = LLMManager()
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

def main():
    # Header
    st.markdown('<div class="main-header">📚 InsightGraph</div>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #666;">Upload documents and ask questions about their content</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("📁 Document Management")
        
        # File upload
        uploaded_file = st.file_uploader(
            "Upload PDF documents",
            type=['pdf'],
            help="Upload PDF files to add to your knowledge base"
        )
        
        if uploaded_file:
            with st.spinner(f"Processing {uploaded_file.name}..."):
                # Save file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_file_path = tmp_file.name
                
                # Add to ChromaDB
                result = st.session_state.chroma_manager.add_document(tmp_file_path, uploaded_file.name)
                
                # Clean up
                os.unlink(tmp_file_path)
                
                if result['status'] == 'success':
                    st.success(f"✅ {result['message']}")
                    st.session_state.uploaded_files.append(uploaded_file.name)
                else:
                    st.error(f"❌ {result['message']}")
        
        # Document stats
        st.subheader("📊 Statistics")
        stats = st.session_state.chroma_manager.get_collection_stats()
        
        with st.container():
            st.markdown(f"""
            <div class="stats-card">
                <strong>Total Chunks:</strong> {stats.get('total_chunks', 0)}<br>
                <strong>Documents:</strong> {stats.get('unique_documents', 0)}<br>
                <strong>Collection:</strong> {stats.get('collection_name', 'documents')}
            </div>
            """, unsafe_allow_html=True)
        
        # Document list
        if stats.get('documents'):
            st.subheader("📄 Uploaded Documents")
            for doc in stats['documents']:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"📄 {doc}")
                with col2:
                    if st.button("🗑️", key=f"delete_{doc}"):
                        result = st.session_state.chroma_manager.delete_document(doc)
                        if result['status'] == 'success':
                            st.success(f"Deleted {doc}")
                            st.rerun()
                        else:
                            st.error(f"Error: {result['message']}")
        
        # Clear chat
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("💬 Chat Interface")
        
        # Display chat history
        chat_container = st.container()
        with chat_container:
            for i, message in enumerate(st.session_state.chat_history):
                if message['role'] == 'user':
                    st.markdown(f"""
                    <div class="chat-message user-message">
                        <strong>You:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message assistant-message">
                        <strong>Assistant:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show sources if available
                    if 'sources' in message and message['sources']:
                        st.markdown("**📚 Sources:**")
                        for source in message['sources']:
                            st.markdown(f"""
                            <div class="source-citation">
                                📄 {source.get('filename', 'Unknown')} - Page {source.get('page', '?')}
                                <br>Similarity: {source.get('similarity_score', 0):.2f}
                            </div>
                            """, unsafe_allow_html=True)
        
        # Chat input
        user_input = st.chat_input("Ask about your documents...")
        
        if user_input:
            # Add user message
            st.session_state.chat_history.append({
                'role': 'user',
                'content': user_input
            })
            
            # Search documents
            with st.spinner("🔍 Searching documents..."):
                search_results = st.session_state.chroma_manager.search_documents(user_input)
            
            # Generate LLM response
            with st.spinner("🤖 Generating response..."):
                llm_response = st.session_state.llm_manager.generate_response(
                    user_input, 
                    search_results['contexts']
                )
            
            # Add assistant response
            if llm_response['type'] == 'complete':
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': llm_response['content'],
                    'sources': search_results['contexts']
                })
            else:
                st.session_state.chat_history.append({
                    'role': 'assistant',
                    'content': llm_response.get('content', 'Error generating response'),
                    'sources': search_results['contexts']
                })
            
            # Rerun to display new messages
            st.rerun()
    
    with col2:
        st.header("🔍 Search Results")
        
        # Show recent search results
        if 'last_search' in st.session_state:
            st.write(f"**Query:** {st.session_state.last_search['query']}")
            st.write(f"**Results:** {st.session_state.last_search['total_results']} chunks found")
            
            for i, context in enumerate(st.session_state.last_search['contexts'][:3]):
                with st.expander(f"Chunk {i+1} (Similarity: {context.get('similarity_score', 0):.2f})"):
                    st.write(f"📄 {context.get('filename', 'Unknown')} - Page {context.get('page', '?')}")
                    st.write(context.get('text', ''))
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        if st.button("📋 Show All Documents"):
            all_docs = st.session_state.chroma_manager.get_all_documents()
            st.write(f"Found {len(all_docs)} total chunks")
            
            for i, doc in enumerate(all_docs[:5]):
                with st.expander(f"Chunk {i+1}"):
                    st.write(f"📄 {doc.get('filename', 'Unknown')} - Page {doc.get('page', '?')}")
                    st.write(doc.get('text', ''))
        
        if st.button("🔄 Refresh Stats"):
            st.rerun()

if __name__ == "__main__":
    main()
