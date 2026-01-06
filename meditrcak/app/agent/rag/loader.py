# rag/loader.py
"""
Document Loader for RAG system.
Handles PDF, images, and text file loading with chunking.
"""

import logging
from typing import List, Dict, Any
from pathlib import Path
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    DirectoryLoader,
    TextLoader
)
from app.config.settings import settings

logger = logging.getLogger(__name__)


def load_pdf_documents(directory: str = settings.PDF_DATA_PATH) -> List[Any]:
    """
    Load all PDF documents from a directory.
    
    Args:
        directory: Path to directory containing PDFs
    
    Returns:
        List of Document objects
    """
    try:
        logger.info(f"Loading PDFs from: {directory}")
        
        loader = DirectoryLoader(
            directory,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            show_progress=True
        )
        
        documents = loader.load()
        logger.info(f"Loaded {len(documents)} PDF pages")
        
        return documents
        
    except Exception as e:
        logger.error(f"Failed to load PDFs: {e}")
        return []


def load_text_documents(directory: str = settings.PDF_DATA_PATH) -> List[Any]:
    """
    Load all text documents from a directory.
    
    Args:
        directory: Path to directory containing text files
    
    Returns:
        List of Document objects
    """
    try:
        logger.info(f"Loading text files from: {directory}")
        
        loader = DirectoryLoader(
            directory,
            glob="**/*.txt",
            loader_cls=TextLoader,
            show_progress=True
        )
        
        documents = loader.load()
        logger.info(f"Loaded {len(documents)} text documents")
        
        return documents
        
    except Exception as e:
        logger.error(f"Failed to load text files: {e}")
        return []


def chunk_documents(
    documents: List[Any],
    chunk_size: int = settings.MAX_CHUNK_SIZE,
    chunk_overlap: int = settings.CHUNK_OVERLAP
) -> List[Any]:
    """
    Split documents into chunks for better retrieval.
    
    Args:
        documents: List of Document objects
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
    
    Returns:
        List of chunked Document objects
    """
    try:
        logger.info(f"Chunking {len(documents)} documents (size={chunk_size}, overlap={chunk_overlap})")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        logger.info(f"Created {len(chunks)} chunks")
        
        return chunks
        
    except Exception as e:
        logger.error(f"Failed to chunk documents: {e}")
        return documents


def load_and_process_documents(directory: str = settings.PDF_DATA_PATH) -> List[Any]:
    """
    Load and process all documents from a directory.
    
    Combines PDF and text loading with chunking.
    
    Args:
        directory: Path to directory containing documents
    
    Returns:
        List of processed Document chunks
    """
    logger.info(f"Loading and processing documents from: {directory}")
    
    # Load PDFs
    pdf_docs = load_pdf_documents(directory)
    
    # Load text files
    text_docs = load_text_documents(directory)
    
    # Combine all documents
    all_docs = pdf_docs + text_docs
    
    if not all_docs:
        logger.warning(f"No documents found in {directory}")
        return []
    
    logger.info(f"Total documents loaded: {len(all_docs)}")
    
    # Chunk documents
    chunks = chunk_documents(all_docs)
    
    return chunks


def load_single_pdf(file_path: str) -> List[Any]:
    """
    Load a single PDF file.
    
    Args:
        file_path: Path to PDF file
    
    Returns:
        List of Document objects
    """
    try:
        logger.info(f"Loading single PDF: {file_path}")
        
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        
        logger.info(f"Loaded {len(documents)} pages from {file_path}")
        return documents
        
    except Exception as e:
        logger.error(f"Failed to load PDF {file_path}: {e}")
        return []


def extract_metadata(documents: List[Any]) -> Dict[str, Any]:
    """
    Extract metadata from loaded documents.
    
    Args:
        documents: List of Document objects
    
    Returns:
        Dict with document metadata summary
    """
    if not documents:
        return {
            "total_documents": 0,
            "sources": [],
            "total_pages": 0
        }
    
    sources = set()
    total_pages = len(documents)
    
    for doc in documents:
        if hasattr(doc, 'metadata') and 'source' in doc.metadata:
            sources.add(doc.metadata['source'])
    
    return {
        "total_documents": len(sources),
        "sources": list(sources),
        "total_pages": total_pages,
        "avg_pages_per_doc": total_pages / len(sources) if sources else 0
    }


# Example usage
if __name__ == "__main__":
    print("Document Loader Test")
    print("=" * 60)
    
    # Test loading and processing
    print("\n1. Load and Process All Documents:")
    chunks = load_and_process_documents()
    print(f"   Total chunks: {len(chunks)}")
    
    if chunks:
        print(f"   First chunk preview: {chunks[0].page_content[:100]}...")
        print(f"   Chunk metadata: {chunks[0].metadata}")
    
    # Extract metadata
    print("\n2. Document Metadata:")
    metadata = extract_metadata(chunks)
    print(f"   Total documents: {metadata['total_documents']}")
    print(f"   Total pages: {metadata['total_pages']}")
    print(f"   Sources: {metadata['sources']}")
