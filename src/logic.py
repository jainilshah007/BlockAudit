import os
import re
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings, OpenAI
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from src.parser import parse_solidity_code
from src.logger_config import logger

# Load environment variables from the .env file
load_dotenv()

def get_openai_api_key():
    """Fetches the OpenAI API key from environment variables."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("OPENAI_API_KEY not found in .env file or environment variables.")
        raise ValueError("OPENAI_API_KEY not found.")
    return api_key

@st.cache_resource
def initialize_qa_chain(index_path="faiss_index"):
    """
    Initializes and returns the QA chain, loading the vector store from disk.
    This function is cached to prevent reloading the model on every interaction.
    """
    logger.info("Attempting to initialize the QA chain...")
    if not os.path.exists(index_path):
        logger.error(f"FAISS index not found at '{index_path}'. Aborting initialization.")
        return None
    
    try:
        api_key = get_openai_api_key()
        embeddings = OpenAIEmbeddings(openai_api_key=api_key)
        vector_store = FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)
        logger.info("FAISS index loaded successfully.")
        
        # This custom prompt template instructs the LLM to act as a security expert
        # and structure its response in a clear, actionable format.
        prompt_template = """
        You are an expert smart contract security auditor. Your task is to analyze the given Solidity code snippet based on the provided context of known vulnerabilities and best practices.
        Focus ONLY on the provided code snippet.

        Context:
        {context}

        Code Snippet / Question:
        {question}

        Based on the context, provide a detailed security analysis. Structure your response in Markdown format as follows:
        
        ### Vulnerability: [Name of the Vulnerability]
        - **Severity:** [Critical / High / Medium / Low / Informational]
        - **Description:** [A detailed explanation of the vulnerability and why it is a risk.]
        - **Recommendation:** [Actionable steps and suggested code changes to fix the vulnerability.]
        - **Suggested Code:** [Provide a secure code snippet that fixes the identified issue. Use Solidity markdown formatting.]
        
        If no vulnerabilities are found, state: "- **Severity:** None" and omit the other fields.
        """
        
        PROMPT = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=OpenAI(temperature=0, openai_api_key=api_key),
            chain_type="stuff",
            retriever=vector_store.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
        logger.info("QA chain initialized successfully.")
        return qa_chain
    except Exception as e:
        logger.critical(f"A critical error occurred during QA chain initialization: {e}", exc_info=True)
        st.error(f"Failed to initialize the QA chain. See auditor.log for details.")
        return None

def analyze_code_with_ai(qa_chain, code):
    """
    Parses the code into functions and analyzes each function individually for vulnerabilities.
    """
    logger.info(f"Starting AI analysis for code snippet of length {len(code)}.")
    functions_to_analyze = parse_solidity_code(code)
    
    full_analysis = ""

    if not functions_to_analyze:
         logger.warning("Could not parse the Solidity code. Analyzing the full snippet as a fallback.")
         return "Could not parse the Solidity code. Please provide a valid contract or function."

    for i, func in enumerate(functions_to_analyze):
        logger.info(f"Analyzing function {i+1}/{len(functions_to_analyze)}: {func['name']}")
        query = f"Analyze this Solidity code for security vulnerabilities: \n```solidity\n{func['code']}\n```"
        try:
            response = qa_chain.invoke({"query": query})
            full_analysis += f"## Analysis for: `{func['name']}`\n\n"
            full_analysis += response["result"]
            full_analysis += "\n\n---\n\n"
        except Exception as e:
            logger.error(f"Error analyzing function {func['name']}: {e}", exc_info=True)
            full_analysis += f"## Analysis for: `{func['name']}`\n\n> An error occurred during the analysis of this function. Please check the logs.\n\n"

    logger.info("AI analysis completed.")
    return full_analysis


def run_heuristic_checks(code):
    """
    Runs simple, rule-based checks for common, low-hanging fruit vulnerabilities.
    """
    logger.info("Running heuristic checks...")
    alerts = []
    if re.search(r"tx\.origin", code):
        alerts.append("⚠️ **Heuristic Alert:** Found usage of `tx.origin`. This is highly insecure for authorization. Always use `msg.sender` instead.")
    
    pragma_match = re.search(r"pragma solidity\s*\^?([0-9\.]+);", code)
    if pragma_match:
        version = pragma_match.group(1)
        if version.startswith("0.4.") or version.startswith("0.5."):
             alerts.append("⚠️ **Heuristic Alert:** Outdated Solidity version detected. Consider upgrading to a more recent version (e.g., ^0.8.0) to benefit from security improvements.")

    if not alerts:
        alerts.append("✅ **Heuristic Check:** No common low-hanging fruit vulnerabilities were detected.")
    
    logger.info(f"Heuristic checks found {len(alerts)} alert(s).")
    return alerts

