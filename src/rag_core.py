import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from src.knowledge_loader import load_knowledge_from_directory
from src.logger_config import logger

# Load environment variables from the .env file
load_dotenv()

def get_openai_api_key():
    """Fetches the OpenAI API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in .env file or environment variables.")
        raise ValueError("OPENAI_API_KEY not found in .env file or environment variables.")
    return api_key

def build_and_save_vector_store(docs, index_path="faiss_index"):
    """
    Builds a FAISS vector store from the documents and saves it locally.

    Args:
        docs (list): A list of document tuples (name, content).
        index_path (str): The path to save the FAISS index.
    """
    logger.info("Starting the vector store build process...")
    
    # 1. Convert the list of tuples into LangChain's Document format.
    # We use the filename as metadata to track the source of each chunk.
    from langchain.schema import Document
    langchain_docs = [Document(page_content=content, metadata={"source": filename}) for filename, content in docs]
    
    # 2. Split the documents into smaller, manageable chunks.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # Max characters per chunk
        chunk_overlap=200,    # Overlap between chunks to preserve context
        length_function=len,
    )
    chunks = text_splitter.split_documents(langchain_docs)
    logger.info(f"Split {len(langchain_docs)} documents into {len(chunks)} chunks.")

    # 3. Create embeddings for the chunks and build the FAISS vector store.
    logger.info("Creating embeddings and building the FAISS index. This may take a few moments...")
    try:
        api_key = get_openai_api_key()
        embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        vector_store = FAISS.from_documents(chunks, embeddings)
    except Exception as e:
        logger.critical(f"Failed to create embeddings or build FAISS index: {e}", exc_info=True)
        return

    # 4. Save the vector store locally for future use.
    vector_store.save_local(index_path)
    logger.info(f"Vector store successfully built and saved to '{index_path}'")

if __name__ == "__main__":
    # This script is the main entry point for building the knowledge base index.
    
    # Step 1: Load the knowledge base from the directory.
    documents = load_knowledge_from_directory()
    
    if documents:
        # Step 2: Build and save the vector store.
        build_and_save_vector_store(documents)
    else:
        logger.warning("No documents were loaded. The vector store was not built.")

