import streamlit as st
from src.logic import initialize_qa_chain, run_heuristic_checks, analyze_code_with_ai
from src.logger_config import logger
import streamlit.components.v1 as components

# --- Theme and Configuration ---
st.set_page_config(
    page_title="Smart Contract Guardian",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Modern Custom CSS with next-gen blue theme
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
        padding: 2rem;
    }
    
    /* Glassmorphism card effect */
    .stTabs [data-baseweb="tab-panel"] {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        border: 1px solid rgba(99, 179, 237, 0.1);
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
    }
    
    /* Enhanced buttons */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px 0 rgba(102, 126, 234, 0.4);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px 0 rgba(102, 126, 234, 0.6);
    }
    
    /* Primary button */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, #00d4ff 0%, #0066ff 100%);
        box-shadow: 0 4px 15px 0 rgba(0, 102, 255, 0.4);
    }
    
    .stButton>button[kind="primary"]:hover {
        box-shadow: 0 6px 20px 0 rgba(0, 102, 255, 0.6);
    }
    
    /* Secondary buttons */
    .stButton>button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(99, 179, 237, 0.3);
        box-shadow: none;
    }
    
    /* Text areas */
    .stTextArea textarea {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(99, 179, 237, 0.3) !important;
        border-radius: 12px;
        color: #e0e0e0 !important;
        font-family: 'Fira Code', monospace;
    }
    
    .stTextArea textarea:focus {
        border: 1px solid rgba(0, 212, 255, 0.6) !important;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1419 0%, #1a2332 100%);
        border-right: 1px solid rgba(99, 179, 237, 0.2);
    }
    
    [data-testid="stSidebar"] .stMarkdown {
        color: #b8c5d6;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #00d4ff !important;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 10px;
        border: 1px solid rgba(99, 179, 237, 0.2);
        color: #00d4ff !important;
        font-weight: 600;
    }
    
    /* Alerts */
    .stAlert {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        border-left: 4px solid #00d4ff;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: rgba(255, 255, 255, 0.02);
        padding: 8px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        color: #b8c5d6;
        font-weight: 600;
        background: transparent;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #00d4ff 0%, #0066ff 100%);
        color: white !important;
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #00d4ff !important;
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        color: #00d4ff !important;
        font-size: 2rem !important;
        font-weight: 700;
    }
    
    /* Custom card component */
    .custom-card {
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 1.5rem;
        border: 1px solid rgba(99, 179, 237, 0.15);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    
    .custom-card:hover {
        border-color: rgba(0, 212, 255, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0, 212, 255, 0.2);
    }
    
    /* Feature icons */
    .feature-icon {
        font-size: 2rem;
        margin-bottom: 0.5rem;
        display: inline-block;
        background: linear-gradient(135deg, #00d4ff 0%, #0066ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        background: rgba(0, 212, 255, 0.2);
        color: #00d4ff;
        border: 1px solid rgba(0, 212, 255, 0.3);
    }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <div style="font-size: 4rem; background: linear-gradient(135deg, #00d4ff 0%, #0066ff 100%); 
                        -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                🛡️
            </div>
            <h2 style="color: #00d4ff; margin-top: 0.5rem; font-weight: 700;">Guardian</h2>
            <span class="status-badge">AI Powered</span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    <div class="custom-card">
        <h4 style="color: #00d4ff; margin-top: 0;">About Guardian</h4>
        <p style="color: #b8c5d6; font-size: 0.9rem; line-height: 1.6;">
        Next-generation security analysis tool powered by advanced AI. Identifies and prevents 
        vulnerabilities in Solidity smart contracts with precision.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Features in cards
    st.markdown("""
    <div class="custom-card">
        <div class="feature-icon">🔍</div>
        <h5 style="color: #fff; margin: 0.5rem 0;">Real-time Scanning</h5>
        <p style="color: #8892a6; font-size: 0.85rem;">Instant vulnerability detection</p>
    </div>
    
    <div class="custom-card">
        <div class="feature-icon">🤖</div>
        <h5 style="color: #fff; margin: 0.5rem 0;">AI Deep Analysis</h5>
        <p style="color: #8892a6; font-size: 0.85rem;">Context-aware code review</p>
    </div>
    
    <div class="custom-card">
        <div class="feature-icon">📊</div>
        <h5 style="color: #fff; margin: 0.5rem 0;">Smart Reporting</h5>
        <p style="color: #8892a6; font-size: 0.85rem;">Severity-based insights</p>
    </div>
    
    <div class="custom-card">
        <div class="feature-icon">💡</div>
        <h5 style="color: #fff; margin: 0.5rem 0;">Fix Suggestions</h5>
        <p style="color: #8892a6; font-size: 0.85rem;">Actionable recommendations</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🔬 How It Works", expanded=False):
        st.markdown("""
        **1. Heuristic Analysis**
        - Quick pattern recognition
        - Common vulnerability scan
        - Style and syntax checks
        
        **2. Deep AI Analysis**
        - Machine learning-powered review
        - Context-aware assessment
        - Best practices validation
        
        **3. Smart Recommendations**
        - Detailed fix guidance
        - Code examples
        - Security standards
        """)
    
    st.markdown("---")
    st.markdown("### 🚀 Quick Examples")
    
    example_1 = st.button("🔄 Reentrancy Attack", use_container_width=True)
    example_2 = st.button("🔑 tx.origin Vulnerability", use_container_width=True)
    example_3 = st.button("📝 Pragma Version", use_container_width=True)

# --- Main Page Content ---
st.markdown("""
    <div style="text-align: center; padding: 2rem 0 3rem 0;">
        <h1 style="font-size: 3rem; margin-bottom: 0.5rem; background: linear-gradient(135deg, #00d4ff 0%, #0066ff 100%); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Smart Contract Security Analysis
        </h1>
        <p style="color: #8892a6; font-size: 1.2rem;">
            Protect your blockchain assets with AI-powered security auditing
        </p>
    </div>
""", unsafe_allow_html=True)

# Initialize the QA chain
qa_chain = initialize_qa_chain()

if qa_chain:
    # Create tabs for different functionalities
    tab1, tab2 = st.tabs(["🔍 Contract Analysis", "📚 Security Knowledge Base"])
    
    with tab1:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("""
                <div class="custom-card" style="text-align: center;">
                    <div style="font-size: 2.5rem;">⚡</div>
                    <h4 style="color: #fff; margin: 0.5rem 0;">Fast</h4>
                    <p style="color: #8892a6; font-size: 0.85rem;">Millisecond response</p>
                </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown("""
                <div class="custom-card" style="text-align: center;">
                    <div style="font-size: 2.5rem;">🎯</div>
                    <h4 style="color: #fff; margin: 0.5rem 0;">Accurate</h4>
                    <p style="color: #8892a6; font-size: 0.85rem;">Good precision rate</p>
                </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown("""
                <div class="custom-card" style="text-align: center;">
                    <div style="font-size: 2.5rem;">🔒</div>
                    <h4 style="color: #fff; margin: 0.5rem 0;">Secure</h4>
                    <p style="color: #8892a6; font-size: 0.85rem;">Private analysis</p>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Analysis Form
        with st.form("audit_form", clear_on_submit=False):
            # Set initial input based on examples
            if example_1:
                initial_input = "What is a reentrancy attack and how can I prevent it in my code?"
            elif example_2:
                initial_input = "function withdraw(uint amount) public { require(balances[msg.sender] >= amount); (bool success, ) = msg.sender.call{value: amount}(\"\"); require(success, \"Failed to send Ether\"); balances[msg.sender] -= amount; }"
            elif example_3:
                initial_input = "pragma solidity ^0.5.0;"
            else:
                initial_input = ""
            
            st.markdown("### 📝 Submit Your Smart Contract")
            # Code input area with syntax highlighting
            user_input = st.text_area(
                "Smart Contract Code or Security Question:",
                value=initial_input,
                height=350,
                placeholder="// Paste your Solidity code here...\n// Or ask any security-related question\n\ncontract MyContract {\n    // Your code\n}",
                help="Paste your Solidity smart contract code or ask a security question",
                label_visibility="collapsed"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([3,1,1])
            with col1:
                submitted = st.form_submit_button("🔍 Analyze Contract", type="primary", use_container_width=True)
            with col2:
                st.form_submit_button("🔄 Clear", type="secondary", use_container_width=True)
            with col3:
                st.form_submit_button("💾 Export", type="secondary", use_container_width=True)

        if submitted and user_input:
            logger.info(f"New submission received. Input length: {len(user_input)}.")
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 🎯 Heuristic Analysis Results")
            
            with st.container():
                heuristic_alerts = run_heuristic_checks(user_input)
                if heuristic_alerts:
                    for alert in heuristic_alerts:
                        st.markdown(f"""
                            <div class="custom-card">
                                {alert}
                            </div>
                        """, unsafe_allow_html=True)
                else:
                    st.success("✅ No immediate vulnerabilities detected in heuristic scan")
            
            st.markdown("---")
            
            st.markdown("### 🤖 Deep AI Analysis")
            with st.spinner(" AI is performing comprehensive analysis..."):
                try:
                    analysis_result = analyze_code_with_ai(qa_chain, user_input)
                    st.markdown(f"""
                        <div class="custom-card">
                            {analysis_result}
                        </div>
                    """, unsafe_allow_html=True)
                    
                except Exception as e:
                    logger.critical(f"An unhandled exception occurred in the main analysis block: {e}", exc_info=True)
                    st.error("⚠️ A critical error occurred during analysis. The incident has been logged. Please check `auditor.log` for details.")
    
    # with tab2:
    #     st.markdown("### 📚 Security Knowledge Base")
    #     st.markdown("""
    #     <div class="custom-card">
    #         <p style="color: #b8c5d6;">
    #         Access our comprehensive database of smart contract vulnerabilities, 
    #         best practices, and security patterns. Ask any question about blockchain security.
    #         </p>
    #     </div>
    #     """, unsafe_allow_html=True)
        
    #     # Add knowledge base content here
    #     st.info("💡 Coming soon: Interactive knowledge base with searchable vulnerability database")
        
else:
    st.error("⚠️ The Guardian engine could not be initialized. Please check the console and `auditor.log` for details.")