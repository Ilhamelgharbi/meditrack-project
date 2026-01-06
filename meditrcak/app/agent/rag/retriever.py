# rag/retriever.py
"""
Retrieval Chain Logic for RAG system.
Provides semantic search and context retrieval for agent queries.
"""

import logging
from typing import List, Dict, Any, Optional
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from rag.vector_store import get_retriever, search_documents
from app.config.settings import settings

logger = logging.getLogger(__name__)


# Cached QA chain at module level
_qa_chain = None


def get_qa_chain(model=None):
    """
    Get or create a RetrievalQA chain (cached).
    
    Args:
        model: LLM model (optional, will create if not provided)
    
    Returns:
        RetrievalQA chain instance
    """
    global _qa_chain
    
    if _qa_chain is not None:
        return _qa_chain
    
    try:
        from langchain_groq import ChatGroq
        
        # Create model if not provided
        if model is None:
            model = ChatGroq(
                model=settings.GROQ_MODEL_NAME,
                api_key=settings.GROQ_API_KEY,
                temperature=0.3,
                max_tokens=1024
            )
        
        # Get retriever
        retriever = get_retriever()
        
        # Custom prompt for medical QA
        prompt_template = """You are a medical information assistant. Use the following context to answer the question accurately and professionally.

Context:
{context}

Question: {question}

Instructions:
- Provide accurate medical information based on the context
- If the context doesn't contain relevant information, say so clearly
- Include relevant details like dosages, side effects, or warnings when available
- Always recommend consulting a healthcare provider for personalized advice

Answer:"""
        
        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create retrieval QA chain
        _qa_chain = RetrievalQA.from_chain_type(
            llm=model,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        logger.info("RetrievalQA chain created successfully")
        return _qa_chain
        
    except Exception as e:
        logger.error(f"Failed to create QA chain: {e}")
        return None


def retrieve_context(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Retrieve relevant context for a query.
    
    Args:
        query: Search query
        top_k: Number of documents to retrieve
    
    Returns:
        List of relevant documents with content and metadata
    """
    try:
        results = search_documents(query, top_k=top_k)
        
        documents = []
        for doc in results:
            documents.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "source": doc.metadata.get("source", "Unknown")
            })
        
        return documents
        
    except Exception as e:
        logger.error(f"Context retrieval error: {e}")
        return []


def answer_question(query: str, return_sources: bool = True) -> Dict[str, Any]:
    """
    Answer a question using the RAG system.
    
    Args:
        query: Question to answer
        return_sources: Whether to return source documents
    
    Returns:
        Dict with answer and optional source documents
    """
    qa_chain = get_qa_chain()
    
    if qa_chain is None:
        return {
            "error": "QA chain not available",
            "message": "Failed to initialize retrieval QA system"
        }
    
    try:
        logger.info(f"Answering question: {query[:50]}...")
        
        result = qa_chain({"query": query})
        
        response = {
            "question": query,
            "answer": result["result"]
        }
        
        if return_sources and "source_documents" in result:
            response["sources"] = [
                {
                    "content": doc.page_content[:200] + "...",
                    "source": doc.metadata.get("source", "Unknown"),
                    "page": doc.metadata.get("page", "N/A")
                }
                for doc in result["source_documents"]
            ]
            response["source_count"] = len(result["source_documents"])
        
        return response
        
    except Exception as e:
        logger.error(f"Question answering error: {e}")
        return {
            "error": str(e),
            "question": query
        }


def batch_retrieve(queries: List[str], top_k: int = 3) -> Dict[str, List[Dict[str, Any]]]:
    """
    Retrieve context for multiple queries at once.
    
    Args:
        queries: List of search queries
        top_k: Number of documents per query
    
    Returns:
        Dict mapping queries to their retrieved documents
    """
    results = {}
    
    for query in queries:
        results[query] = retrieve_context(query, top_k=top_k)
    
    return results


def summarize_documents(documents: List[Dict[str, Any]]) -> str:
    """
    Summarize retrieved documents into a coherent context.
    
    Args:
        documents: List of document dicts with content and metadata
    
    Returns:
        Summarized text
    """
    if not documents:
        return "No relevant information found."
    
    # Combine document contents
    combined_text = "\n\n".join([
        f"Source: {doc.get('source', 'Unknown')}\n{doc['content']}"
        for doc in documents
    ])
    
    return combined_text


# Example usage
if __name__ == "__main__":
    print("Retriever Test")
    print("=" * 60)
    
    # Test context retrieval
    print("\n1. Retrieve Context:")
    query = "What is diabetes?"
    context = retrieve_context(query, top_k=3)
    print(f"   Query: {query}")
    print(f"   Retrieved: {len(context)} documents")
    if context:
        print(f"   First result: {context[0]['content'][:100]}...")
    
    # Test question answering
    print("\n2. Answer Question:")
    result = answer_question("What are the symptoms of diabetes?")
    if "error" in result:
        print(f"   Error: {result['error']}")
    else:
        print(f"   Question: {result['question']}")
        print(f"   Answer: {result['answer'][:200]}...")
        if "sources" in result:
            print(f"   Sources: {result['source_count']}")
    
    # Test batch retrieval
    print("\n3. Batch Retrieve:")
    queries = ["diabetes symptoms", "heart disease prevention"]
    batch_results = batch_retrieve(queries, top_k=2)
    for q, docs in batch_results.items():
        print(f"   {q}: {len(docs)} documents")
