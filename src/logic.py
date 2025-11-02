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
        
        # Enhanced prompt template that ALWAYS requires code suggestions
        # If context has examples, use them; otherwise generate secure code
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
        - **Suggested Code:** [MANDATORY: You MUST always provide a complete, secure code snippet that fixes the identified issue. If the context contains code examples, adapt them. If not, generate a secure implementation based on Solidity best practices. Always use proper ```solidity code blocks with complete, compilable code. Never leave this empty or provide placeholders.]
        
        IMPORTANT: The "Suggested Code" section is REQUIRED for every vulnerability found. It must contain actual, complete Solidity code that can be used to fix the issue.
        
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

def generate_code_fix_with_chatgpt(code_snippet, vulnerability_description, api_key):
    """
    Fallback function to generate secure code fix using ChatGPT when knowledge base
    doesn't provide good examples.
    """
    llm = OpenAI(temperature=0, openai_api_key=api_key)
    
    prompt = f"""You are an expert Solidity security developer. Generate a secure, complete code fix for the following vulnerability.

Vulnerable Code:
```solidity
{code_snippet}
```

Vulnerability Description:
{vulnerability_description}

Provide ONLY a complete, secure Solidity code snippet that fixes this vulnerability. Include proper error handling, security checks, and best practices. Use ```solidity code blocks."""
    
    try:
        response = llm.invoke(prompt)
        return response.content.strip() if hasattr(response, 'content') else str(response).strip()
    except Exception as e:
        logger.error(f"Error generating code fix with ChatGPT: {e}")
        return "```solidity\n// Error generating code fix. Please review the recommendations above.\n```"

def has_valid_code_suggestion(result_text):
    """
    Checks if the result contains a valid code suggestion.
    Returns True if it contains code blocks with actual code.
    """
    # Check for code blocks
    if "```solidity" not in result_text and "```" not in result_text:
        return False
    
    # Extract code between code blocks
    code_blocks = re.findall(r'```(?:solidity)?\s*(.*?)```', result_text, re.DOTALL)
    
    # Check if any code block has meaningful content
    for block in code_blocks:
        code_content = block.strip()
        # Check if it's not just comments or placeholders
        if len(code_content) > 20 and not all(c in ['/', '*', ' ', '\n', '-', '_', '.'] for c in code_content.replace(' ', '').replace('\n', '')):
            return True
    
    return False

def analyze_code_with_ai(qa_chain, code):
    """
    Parses the code into functions and analyzes each function individually for vulnerabilities.
    Includes fallback to ChatGPT for code generation when knowledge base doesn't provide good examples.
    """
    logger.info(f"Starting AI analysis for code snippet of length {len(code)}.")
    functions_to_analyze = parse_solidity_code(code)
    
    full_analysis = ""
    api_key = get_openai_api_key()

    if not functions_to_analyze:
         logger.warning("Could not parse the Solidity code. Analyzing the full snippet as a fallback.")
         return "Could not parse the Solidity code. Please provide a valid contract or function."

    for i, func in enumerate(functions_to_analyze):
        logger.info(f"Analyzing function {i+1}/{len(functions_to_analyze)}: {func['name']}")
        query = f"Analyze this Solidity code for security vulnerabilities and provide secure fixes: \n```solidity\n{func['code']}\n```"
        try:
            response = qa_chain.invoke({"query": query})
            result = response["result"]
            
            # Check if result contains vulnerabilities but lacks proper code suggestions
            if "Vulnerability:" in result or "**Severity:**" in result:
                # Extract vulnerability description for fallback if needed
                vulnerability_match = re.search(r'### Vulnerability:\s*(.+?)(?:\n|$)', result, re.IGNORECASE)
                description_match = re.search(r'\*\*Description:\*\*\s*(.+?)(?:\*\*Recommendation|\*\*Suggested Code|$)', result, re.DOTALL)
                
                vulnerability_name = vulnerability_match.group(1).strip() if vulnerability_match else "Security Issue"
                vulnerability_desc = description_match.group(1).strip() if description_match else vulnerability_name
                
                # Check if Suggested Code section is empty or invalid
                suggested_code_match = re.search(r'\*\*Suggested Code:\*\*\s*(.+?)(?:\n\n|\n###|$)', result, re.DOTALL)
                
                if not suggested_code_match or not has_valid_code_suggestion(result):
                    logger.info(f"Generated code suggestion is weak/empty for {func['name']}. Using ChatGPT fallback.")
                    # Generate secure code using ChatGPT as fallback
                    generated_code = generate_code_fix_with_chatgpt(func['code'], vulnerability_desc, api_key)
                    
                    # Replace or append the Suggested Code section
                    if suggested_code_match:
                        # Replace existing weak suggestion
                        old_suggestion = suggested_code_match.group(0)
                        result = result.replace(old_suggestion, f"**Suggested Code:** {generated_code}")
                    else:
                        # Append if missing
                        result += f"\n\n**Suggested Code:** {generated_code}"
            
            full_analysis += f"## Analysis for: `{func['name']}`\n\n"
            full_analysis += result
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

