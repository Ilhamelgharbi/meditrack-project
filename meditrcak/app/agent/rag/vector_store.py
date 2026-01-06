# rag/vector_store.py
"""
Vector store module for medical document retrieval using FAISS.

This module implements a cached RAG (Retrieval-Augmented Generation) system
for medical knowledge retrieval. All components are pre-loaded at import time
to ensure fast query responses.

Architecture:
    - Embeddings: HuggingFace SentenceTransformer (all-MiniLM-L6-v2)
    - Vector Store: FAISS with pre-computed embeddings
    - Retriever: k=3 most relevant documents per query
    
Performance:
    - Initial load: ~20s (one-time at module import)
    - Query time: <100ms after initialization
    - Memory: ~500MB for embeddings + vector index
"""

import logging
from typing import Optional, List
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.tools import tool

from app.config.settings import settings

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logger = logging.getLogger(__name__)

# Suppress verbose logging from external libraries
logging.getLogger('sentence_transformers').setLevel(logging.WARNING)
logging.getLogger('faiss').setLevel(logging.WARNING)
logging.getLogger('huggingface_hub').setLevel(logging.WARNING)


# ============================================================================
# CONFIGURATION
# ============================================================================

# Retrieval configuration
RETRIEVAL_TOP_K = 2  # Number of documents to retrieve per query
BATCH_SIZE = 32      # Batch size for embedding generation
DEVICE = 'cpu'       # Compute device (cpu/cuda)


# ============================================================================
# CACHED COMPONENTS (Module-level singletons)
# ============================================================================

def _initialize_vectorstore() -> tuple[FAISS, VectorStoreRetriever]:
    """
    Initialize and cache the vector store and retriever.
    
    This function is called once at module import time. All components
    are loaded into memory and reused for subsequent queries.
    
    Returns:
        tuple: (vectorstore, retriever)
        
    Raises:
        FileNotFoundError: If vector store files don't exist
        Exception: If loading fails for any reason
    """
    try:
        logger.info("Initializing vector store components...")
        
        # Validate vector store path exists
        if not Path(settings.DB_FAISS_PATH).exists():
            raise FileNotFoundError(
                f"Vector store not found at {settings.DB_FAISS_PATH}. "
                "Please run the ingestion script first."
            )
        
        # Load embeddings model
        logger.debug(f"Loading embeddings model: {settings.EMBEDDING_MODEL_NAME}")
        embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL_NAME,
            model_kwargs={'device': DEVICE},
            encode_kwargs={
                'normalize_embeddings': True,
                'batch_size': BATCH_SIZE
            }
        )
        
        # Load FAISS vector store
        logger.debug(f"Loading FAISS index from: {settings.DB_FAISS_PATH}")
        vectorstore = FAISS.load_local(
            settings.DB_FAISS_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        
        # Create retriever
        retriever = vectorstore.as_retriever(
            search_kwargs={"k": RETRIEVAL_TOP_K}
        )
        
        logger.info("✓ Vector store initialized successfully")
        return vectorstore, retriever
        
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}", exc_info=True)
        raise


# ============================================================================
# LAZY INITIALIZATION (only load when first accessed)
# ============================================================================

_vectorstore = None
_retriever = None

def _get_vectorstore():
    """Lazy load vectorstore only when first accessed."""
    global _vectorstore, _retriever
    if _vectorstore is None:
        logger.info("Loading medical knowledge vectorstore...")
        _vectorstore, _retriever = _initialize_vectorstore()
    return _vectorstore

def _get_retriever():
    """Lazy load retriever only when first accessed."""
    _get_vectorstore()  # Ensure vectorstore is loaded
    return _retriever


# ============================================================================
# PUBLIC API
# ============================================================================

def get_vectorstore() -> FAISS:
    """
    Get the cached FAISS vector store instance.
    
    Returns:
        FAISS: Pre-loaded vector store singleton
    """
    return _get_vectorstore()


def get_retriever() -> VectorStoreRetriever:
    """
    Get the cached retriever instance.
    
    Returns:
        VectorStoreRetriever: Pre-configured retriever with k=3
    """
    return _get_retriever()


def search_documents(query: str, top_k: Optional[int] = None) -> List[Document]:
    """
    Search for relevant medical documents.
    
    Args:
        query: Search query text
        top_k: Number of documents to return (default: RETRIEVAL_TOP_K)
        
    Returns:
        List of Document objects with content and metadata
    """
    try:
        vectorstore = _get_vectorstore()
        retriever = _get_retriever()
        
        if top_k and top_k != RETRIEVAL_TOP_K:
            # Create temporary retriever with custom k
            custom_retriever = vectorstore.as_retriever(
                search_kwargs={"k": top_k}
            )
            return custom_retriever.invoke(query)
        else:
            return retriever.invoke(query)
            
    except Exception as e:
        logger.error(f"Document search failed for query: {query[:50]}... Error: {e}")
        return []


# ============================================================================
# LANGCHAIN TOOL
# ============================================================================

@tool(
    "retrieve_medical_documents",
    description=(
        "Retrieve verified medical knowledge, clinical guidelines, and "
        "evidence-based documents from the medical vector store. "
        "Use this tool for general medical questions about diseases, "
        "causes, symptoms, treatments, or medical explanations."
    )
)
def retrieve_medical_documents(query: str) -> str:
    """
    LangChain tool for retrieving medical documents.
    
    Args:
        query: Medical question or search query
        
    Returns:
        Formatted string with retrieved documents or error message
    """
    try:
        docs = search_documents(query)
        
        if not docs:
            return "No relevant medical information found for this query."
        
        # Format documents for LLM consumption
        formatted_docs = []
        for i, doc in enumerate(docs, 1):
            content = doc.page_content.strip()
            formatted_docs.append(f"Document {i}:\n{content}")
        
        return "\n\n".join(formatted_docs)
        
    except Exception as e:
        logger.error(f"Tool execution failed: {e}", exc_info=True)
        return "Error retrieving medical information. Please try again."