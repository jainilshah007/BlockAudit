import os
import sys
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA

# Load environment variables from the .env file
load_dotenv()

def get_openai_api_key():
    """Fetches the OpenAI API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file or environment variables.")
    return api_key

def initialize_qa_chain(index_path="faiss_index"):
    """
    Initializes and returns the QA chain for querying.
    """
    if not os.path.exists(index_path):
        print(f"Error: FAISS index not found at '{index_path}'. Please run 'python -m src.rag_core' first to build it.", file=sys.stderr)
        return None

    print("Loading the knowledge base (this might take a moment)...")
    try:
        api_key = get_openai_api_key()
        embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        
        # Load the vector store from the local disk
        vector_store = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        
        # Create the Question-Answering chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=OpenAI(temperature=0, openai_api_key=api_key),
            chain_type="stuff",
            retriever=vector_store.as_retriever(),
            return_source_documents=True
        )
        print("Auditor is ready. You can start asking questions.")
        return qa_chain
    except Exception as e:
        print(f"An error occurred during initialization: {e}", file=sys.stderr)
        return None


def query_auditor(qa_chain, query):
    """
    Queries the Auditor's knowledge base using the initialized chain.
    """
    print("\nThinking...")
    result = qa_chain.invoke({"query": query})
    return result

if __name__ == "__main__":
    qa_chain = initialize_qa_chain()
    
    if qa_chain:
        # Create a loop to continuously ask questions
        while True:
            # Get a question from the user
            user_query = input("\nPlease enter your question or contract snippet (type 'exit' to quit): \n> ")
            
            if user_query.lower() == 'exit':
                print("Exiting Auditor. Goodbye!")
                break
            
            if not user_query.strip():
                print("Please enter a valid question.")
                continue

            response = query_auditor(qa_chain, user_query)
            
            print("\n--- Auditor's Response ---")
            print(response["result"])
            
            print("\n--- Sources Used ---")
            for doc in response["source_documents"]:
                # For better readability, we only display the filename
                source_file = os.path.basename(doc.metadata.get('source', 'Unknown'))
                print(f"-> {source_file}")

