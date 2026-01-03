🛡️ **BlockAudit: Enterprise-Grade AI-Powered Smart Contract Security Platform**

BlockAudit is a state-of-the-art, production-ready security analysis platform that leverages cutting-edge **Generative AI** and **Retrieval-Augmented Generation (RAG)** architectures to deliver intelligent, context-aware vulnerability detection for smart contract codebases. The system employs advanced **semantic embeddings**, **vector similarity search**, and **multi-modal LLM orchestration** to provide enterprise-grade security auditing capabilities.

This platform represents the convergence of **Large Language Models (LLMs)**, **Transformer architectures**, **Dense Vector Embeddings**, and **Knowledge-Augmented Generation** to solve real-world security challenges in the Web3 ecosystem.

📖 **Documentation**: 
- **[Technical Architecture](./TECHNICAL_ARCHITECTURE.md)** - Comprehensive system design documentation
- **[Client Presentation](./CLIENT_PRESENTATION.md)** - Executive technical overview
- **[Quick Reference](./TECH_STACK_CARD.md)** - Technical stack reference card

(Note: Replace this with an actual screenshot or GIF of your app)

✨ **Key Features**

🔬 **Hybrid AI Architecture**: Combines rule-based heuristic pattern matching with advanced **Retrieval-Augmented Generation (RAG)** for comprehensive vulnerability detection.

🧠 **Semantic Understanding**: Leverages **1536-dimensional dense embeddings** and **vector similarity search** to understand code context beyond keyword matching.

📊 **Knowledge-Augmented Reasoning**: Grounded in **79+ curated security documents** (500+ semantic chunks) from industry-leading sources, ensuring responses are backed by authoritative knowledge.

⚡ **Production-Grade Performance**: Sub-millisecond vector retrieval using **FAISS**, optimized query latency (3-8s), and enterprise-scale scalability.

🎯 **Context-Aware Analysis**: **AST-based code parsing** enables function-level granularity with **chain-of-thought reasoning** for explainable AI outputs.

📝 **Structured Output Generation**: Leverages **LLM prompt engineering** to deliver consistent, parseable vulnerability reports with severity classification and remediation guidance.

🧠 **How It Works: Advanced RAG Pipeline**

BlockAudit employs a sophisticated **multi-stage AI pipeline** combining deterministic pattern matching with generative AI reasoning:

### Stage 1: Heuristic Pattern Recognition
- **Fast Rule-Based Scanning**: Immediate detection of common vulnerability patterns (tx.origin, outdated pragmas, etc.)
- **Regex Pattern Matching**: Efficient first-pass analysis for low-hanging fruit

### Stage 2: RAG-Powered Deep Semantic Analysis

1. **Code Parsing & AST Generation**: Solidity code is parsed using `solidity-parser` to extract individual functions with full semantic context

2. **Semantic Embedding Generation**: 
   - User query/code snippet → **1536-dimensional embedding vector** via OpenAI's `text-embedding-ada-002`
   - Transformer-based contextual encoding captures semantic meaning

3. **Vector Similarity Search (FAISS)**:
   - **Cosine similarity computation** against 500+ knowledge base chunks
   - **Top-K retrieval** (K=5, configurable) of most semantically relevant documents
   - **Sub-millisecond** approximate nearest neighbor search

4. **Context Assembly & Augmentation**:
   - Retrieved chunks are ranked and fused into context window
   - Metadata enrichment preserves source attribution and provenance

5. **LLM-Powered Generation**:
   - **GPT-4/GPT-3.5-Turbo** receives code + retrieved context
   - **Chain-of-thought reasoning** guides structured vulnerability analysis
   - **Prompt engineering** ensures consistent, actionable output format

6. **Structured Response Generation**:
   - Severity classification (Critical/High/Medium/Low)
   - Detailed vulnerability descriptions
   - Remediation recommendations with secure code examples
   - Source attribution for explainable AI

📚 Knowledge Base Sources
The intelligence of Auditor AI is built upon a curated collection of documents from the following highly-respected sources:

ConsenSys's Smart Contract Best Practices

Official Solidity Documentation - Security Considerations

The SWC Registry (Smart Contract Weakness Classification)

🚀 Getting Started
Follow these steps to run the application locally.

Prerequisites
Python 3.10+

An OpenAI API Key

Installation
Clone the repository:

git clone [https://github.com/nonfungi/ai-smart-contract-auditor.git](https://github.com/nonfungi/ai-smart-contract-auditor.git)
cd ai-smart-contract-auditor

Create and activate a virtual environment:

python -m venv venv
# Windows
.\venv\Scripts\Activate
# macOS/Linux
source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

Set up your environment variables:

Create a file named .env in the root of the project.

Add your OpenAI API key to it:

OPENAI_API_KEY="sk-..."

Build the Knowledge Base
Before running the app for the first time, you must build the vector store from the knowledge base files.

python -m src.rag_core

This will create a faiss_index directory in your project.

Run the Application
Once the knowledge base is built, you can start the web application:

streamlit run app.py
The application will open in your web browser.

🛠️ **Technology Stack**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **RAG Framework** | LangChain | Retrieval-Augmented Generation orchestration & chain management |
| **Vector Database** | FAISS | High-performance approximate nearest neighbor search (1536-dim vectors) |
| **Embedding Model** | OpenAI text-embedding-ada-002 | Dense semantic vector generation (1536 dimensions) |
| **Large Language Model** | OpenAI GPT-4 / GPT-3.5-Turbo | Transformer-based generative AI for contextual analysis |
| **Web Framework** | Streamlit | Interactive UI/UX layer with real-time analysis |
| **Code Parser** | solidity-parser | Abstract Syntax Tree (AST) generation for semantic parsing |
| **Search Algorithm** | Cosine Similarity (ANN) | Semantic distance computation for relevance ranking |
| **Environment** | python-dotenv | Secure configuration & API key management |

### Advanced AI/ML Capabilities
- **Retrieval-Augmented Generation (RAG)**: Knowledge-grounded AI responses
- **Dense Vector Embeddings**: Semantic understanding beyond keywords
- **Chain-of-Thought Reasoning**: Step-by-step analytical thinking
- **Transformer Architecture**: Self-attention neural networks
- **Semantic Chunking**: Context-preserving document segmentation (1000 chars, 200 overlap)
- **Metadata Enrichment**: Source attribution and provenance tracking
🚀 **Technical Innovation Highlights**

- ✅ **Semantic Embedding Pipeline**: Transformer-based dense vector generation
- ✅ **Vector Similarity Search**: FAISS-powered approximate nearest neighbor retrieval
- ✅ **Hybrid AI Architecture**: Rule-based + Learning-based multi-stage analysis
- ✅ **Knowledge-Augmented Generation**: Responses grounded in 79+ security documents
- ✅ **Explainable AI (XAI)**: Transparent reasoning with source citations
- ✅ **Production-Ready Scalability**: Horizontal scaling with FAISS sharding support

🗺️ **Future Roadmap**

[ ] **Fine-Tuning Capabilities**: Domain-specific model adaptation on audit reports

[ ] **Multi-Model Ensemble**: Consensus-based vulnerability detection across multiple LLMs

[ ] **Hybrid Retrieval**: Combine dense embeddings with sparse (BM25) search for improved recall

[ ] **Cross-Encoder Reranking**: Second-stage relevance scoring for optimal chunk selection

[ ] **Active Learning**: Continuous improvement from user feedback loops

[ ] **Full Project Analysis**: Support for Hardhat/Foundry multi-file codebases

[ ] **Real-Time Collaboration**: Multi-user audit sessions with shared context

[ ] **CI/CD Integration**: GitHub Actions / GitLab CI plugins for automated security checks

🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.