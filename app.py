#!/usr/bin/env python3
"""
GST Grievance Resolution System - Professional Web Frontend

A production-grade web interface for the GST grievance resolution multi-agent system.
Features modern UI design, real-time processing, and sophisticated result display.
"""

import os
import streamlit as st
import sys
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="GST Grievance Resolution System",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apple-inspired CSS for professional styling
def load_custom_css():
    st.markdown("""
    <style>
        /* Global Apple-inspired styling */
        .stApp {
            background-color: #f5f5f7;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }

        /* Hide default streamlit elements */
        .stApp header, .stApp .css-1d391kg {
            display: none;
        }

        /* Apple-style container */
        .apple-container {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 20px;
            padding: 2rem;
            margin: 1rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        /* Apple-style header */
        .apple-header {
            background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
            border-radius: 16px;
            padding: 3rem;
            text-align: center;
            color: white;
            margin-bottom: 0.5rem;
            box-shadow: 0 4px 20px rgba(0, 122, 255, 0.3);
        }

        .apple-header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0 0 0.5rem 0;
            letter-spacing: -0.02em;
        }

        .apple-header p {
            font-size: 1.1rem;
            margin: 0.25rem 0;
            opacity: 0.9;
            font-weight: 400;
        }

        /* Apple-style sections */
        .apple-section {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        }

        /* Apple-style form inputs */
        .apple-input {
            background: rgba(255, 255, 255, 0.8);
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 12px;
            padding: 1rem;
            font-size: 1rem;
            color: #1d1d1f;
            -webkit-appearance: none;
            transition: all 0.2s ease;
        }

        .apple-input:focus {
            outline: none;
            border-color: #007AFF;
            box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.3);
        }

        /* Apple-style buttons */
        .apple-button {
            background: #007AFF;
            color: white;
            border: none;
            border-radius: 12px;
            padding: 1rem 2rem;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            box-shadow: 0 2px 10px rgba(0, 122, 255, 0.3);
        }

        .apple-button:hover {
            background: #0051D5;
            transform: translateY(-1px);
            box-shadow: 0 4px 20px rgba(0, 122, 255, 0.4);
        }

        .apple-button:active {
            transform: translateY(0);
            box-shadow: 0 2px 10px rgba(0, 122, 255, 0.3);
        }

        .apple-button-secondary {
            background: rgba(142, 142, 147, 0.12);
            color: #1d1d1f;
        }

        .apple-button-secondary:hover {
            background: rgba(142, 142, 147, 0.2);
        }

        /* Professional response styling */
        .response-container {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 16px;
            padding: 2rem;
            line-height: 1.6;
            color: #1d1d1f;
            text-align: justify;
            font-size: 1.05rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }

        .response-container p {
            margin: 0 0 1rem 0;
            text-align: justify;
        }

        .response-container strong {
            color: #1d1d1f;
            font-weight: 600;
        }

        /* Apple-style metrics */
        .metric-apple {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }

        .metric-apple:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
        }

        .metric-value-apple {
            font-size: 2.5rem;
            font-weight: 700;
            color: #007AFF;
            margin-bottom: 0.5rem;
        }

        .metric-label-apple {
            color: #6e6e73;
            font-size: 0.9rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Confidence badges */
        .confidence-high {
            color: #34C759;
            font-weight: 600;
        }

        .confidence-medium {
            color: #FF9500;
            font-weight: 600;
        }

        .confidence-low {
            color: #FF3B30;
            font-weight: 600;
        }

        /* Apple-style sources */
        .source-apple {
            background: rgba(255, 255, 255, 0.8);
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.8rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }

        .source-apple:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }

        .source-title-apple {
            font-weight: 600;
            color: #1d1d1f;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }

        .source-citation-apple {
            color: #8E8E93;
            font-size: 0.9rem;
            font-style: italic;
            margin-bottom: 0.5rem;
        }

        .source-content-apple {
            color: #3C3C43;
            line-height: 1.5;
            font-size: 0.95rem;
            text-align: justify;
        }

        /* Apple-style expandable */
        .streamlit-expanderHeader {
            background: rgba(255, 255, 255, 0.8);
            color: #1d1d1f;
            border-radius: 12px 12px 0 0;
            padding: 1.5rem;
            font-weight: 600;
            font-size: 1.1rem;
            border: 1px solid rgba(0, 0, 0, 0.05);
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }

        .streamlit-expanderContent {
            background: rgba(255, 255, 255, 0.8);
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 0 0 12px 12px;
            border-top: none;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
        }

        /* Processing indicator */
        .processing-apple {
            text-align: center;
            padding: 3rem;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        }

        .processing-title {
            font-size: 1.5rem;
            font-weight: 600;
            color: #1d1d1f;
            margin-bottom: 1rem;
        }

        .processing-status {
            color: #6e6e73;
            font-size: 1rem;
            margin-bottom: 1.5rem;
        }

        /* Progress bar Apple style */
        .stProgress > div > div > div {
            background: linear-gradient(90deg, #007AFF, #5856D6);
            border-radius: 5px;
        }

        /* Success/Error messages */
        .apple-success {
            background: rgba(52, 199, 89, 0.1);
            color: #34C759;
            border: 1px solid rgba(52, 199, 89, 0.2);
            border-radius: 12px;
            padding: 1rem;
            font-weight: 500;
        }

        .apple-error {
            background: rgba(255, 59, 48, 0.1);
            color: #FF3B30;
            border: 1px solid rgba(255, 59, 48, 0.2);
            border-radius: 12px;
            padding: 1rem;
            font-weight: 500;
        }

        /* Apple-style sidebar */
        .sidebar-apple {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 16px;
            padding: 1rem;
            margin: 0;
        }

        .sidebar-header-apple {
            background: linear-gradient(135deg, #F2F2F7 0%, #E5E5EA 100%);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1.5rem;
            color: #1d1d1f;
            font-weight: 600;
        }

        /* Apple-style cards */
        .apple-card {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 16px;
            padding: 1.2rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }

        .apple-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1);
        }

        .apple-card-title {
            color: #1d1d1f;
            font-size: 1.2rem;
            font-weight: 600;
            margin: 0 0 1rem 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* Status indicators */
        .status-indicator {
            padding: 0.75rem 1rem;
            border-radius: 12px;
            font-weight: 500;
            margin-bottom: 1rem;
            text-align: center;
        }

        .status-indicator.success {
            background: rgba(52, 199, 89, 0.1);
            color: #34C759;
            border: 1px solid rgba(52, 199, 89, 0.2);
        }

        .status-indicator.warning {
            background: rgba(255, 149, 0, 0.1);
            color: #FF9500;
            border: 1px solid rgba(255, 149, 0, 0.2);
        }

        .status-indicator.error {
            background: rgba(255, 59, 48, 0.1);
            color: #FF3B30;
            border: 1px solid rgba(255, 59, 48, 0.2);
        }

        /* Apple-style query input */
        .query-input-container {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        }

        /* Result container */
        .result-container {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        }

        .response-text {
            background: rgba(255, 255, 255, 0.9);
            border-radius: 12px;
            padding: 1.2rem;
            line-height: 1.6;
            color: #1d1d1f;
            text-align: justify;
            font-size: 1.05rem;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.05);
        }

        .metric-card {
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 0, 0, 0.05);
            border-radius: 12px;
            padding: 1rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }

        .metric-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }

        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            margin-bottom: 0.25rem;
        }

        .metric-label {
            color: #6e6e73;
            font-size: 0.8rem;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .error-message {
            background: rgba(255, 59, 48, 0.1);
            color: #FF3B30;
            border: 1px solid rgba(255, 59, 48, 0.2);
            border-radius: 8px;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }

        .processing-indicator {
            text-align: center;
            padding: 2rem;
            background: rgba(255, 255, 255, 0.8);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 16px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
        }

        .footer {
            text-align: center;
            padding: 2rem;
            margin-top: 2rem;
            color: #6e6e73;
            font-size: 0.9rem;
        }

        /* Typography */
        h1, h2, h3, h4, h5, h6 {
            color: #1d1d1f;
            font-weight: 600;
        }

        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(0, 0, 0, 0.05);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: rgba(0, 0, 0, 0.3);
        }

        /* Animations */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }

        .apple-fade-in {
            animation: fadeIn 0.5s ease-out;
        }

        .apple-pulse {
            animation: pulse 2s infinite;
        }
    </style>
    """, unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'system_initialized' not in st.session_state:
        st.session_state.system_initialized = False
    if 'current_result' not in st.session_state:
        st.session_state.current_result = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []

def initialize_system():
    """Initialize the GST resolution system"""
    try:
        # Import and initialize the actual GST resolution system
        from src.utils.embeddings import initialize_all
        success = initialize_all()
        if success:
            logger.info("GST resolution system initialized successfully")
            st.session_state.system_initialized = True  # Update session state
        else:
            logger.error("Failed to initialize GST resolution system")
            st.session_state.system_initialized = False
        return success
    except Exception as e:
        logger.error(f"System initialization failed: {e}")
        st.error(f"Failed to initialize GST system: {str(e)}")
        st.session_state.system_initialized = False
        return False

def display_header():
    """Display the main header"""
    st.markdown("""
    <div class="apple-header apple-fade-in">
        <h1>🏛️ GST Grievance Resolution System</h1>
        <p>Advanced AI-powered resolution for GST-related queries and issues</p>
        <p><small>Multi-Agent RAG System with LangGraph Orchestration</small></p>
    </div>
    """, unsafe_allow_html=True)

def display_sidebar():
    """Display the sidebar with system information and history"""
    with st.sidebar:
        st.markdown('<div class="sidebar-apple">', unsafe_allow_html=True)

        # System Status
        st.markdown('<div class="apple-card">', unsafe_allow_html=True)
        st.markdown('<h3 class="apple-card-title">🤖 System Status</h3>', unsafe_allow_html=True)

        # Check if resolver is available
        try:
            from src.workflows.gst_workflow import get_resolver
            resolver = get_resolver()
            if resolver and hasattr(resolver, 'app'):
                st.markdown('<div class="status-indicator success">✅ Multi-Agent System Ready</div>', unsafe_allow_html=True)

                # Display agent status
                if hasattr(resolver.app, 'graph') and hasattr(resolver.app.graph, 'nodes'):
                    agents_count = len(resolver.app.graph.nodes)
                    st.markdown(f'<div class="metric-apple"><div class="metric-value-apple">{agents_count}</div><div class="metric-label-apple">Active Agents</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-indicator warning">⚠️ Initializing System...</div>', unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f'<div class="status-indicator error">❌ System Error: {str(e)}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Quick Stats
        if st.session_state.current_result:
            st.markdown('<div class="apple-card">', unsafe_allow_html=True)
            st.markdown('<h3 class="apple-card-title">📊 Quick Stats</h3>', unsafe_allow_html=True)

            result = st.session_state.current_result
            confidence = result.get('confidence', 0)
            sources = result.get('sources', {}).get('total_sources', 0)
            processing_time = result.get('processing_time', 0)

            # Confidence with color coding
            confidence_class = "confidence-high" if confidence >= 90 else "confidence-medium" if confidence >= 70 else "confidence-low"
            st.markdown(f'<div class="metric-apple"><div class="metric-value-apple {confidence_class}">{confidence}%</div><div class="metric-label-apple">Confidence</div></div>', unsafe_allow_html=True)

            st.markdown(f'<div class="metric-apple"><div class="metric-value-apple">{sources}</div><div class="metric-label-apple">Sources Used</div></div>', unsafe_allow_html=True)

            st.markdown(f'<div class="metric-apple"><div class="metric-value-apple">{processing_time:.1f}s</div><div class="metric-label-apple">Processing Time</div></div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        # Query History
        if st.session_state.query_history:
            st.markdown('<div class="apple-card">', unsafe_allow_html=True)
            st.markdown('<h3 class="apple-card-title">📝 Query History</h3>', unsafe_allow_html=True)

            for i, query in enumerate(st.session_state.query_history[-5:], 1):
                with st.expander(f"Query {i}", expanded=False):
                    st.markdown(f'<div class="source-content-apple">{query}</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

def display_query_input():
    """Display the query input form"""
    st.markdown('<div class="query-input-container apple-fade-in">', unsafe_allow_html=True)

    # Header with New Query button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown('<h3 class="apple-card-title">🔍 Submit Your GST Query</h3>', unsafe_allow_html=True)
    with col2:
        # New Query button at the top right
        if st.button(
            "🔄 New Query",
            key="new_query_top",
            help="Start a new query",
            use_container_width=True
        ):
            st.session_state.current_result = None
            st.session_state.query_input = ""
            st.session_state.selected_category = None
            st.rerun()

    st.markdown('<p style="color: #6e6e73; margin-bottom: 1.5rem;">Enter your GST-related question or issue below:</p>', unsafe_allow_html=True)

    # Get category options from the enum
    from src.models.schemas import GrievanceCategory
    category_options = [category.value for category in GrievanceCategory]

    # Category selection with Apple styling
    selected_category = st.selectbox(
        "📋 Select Grievance Category *",
        options=category_options,
        index=None,
        key="selected_category",
        help="Select the category that best describes your GST issue",
        format_func=lambda x: f"📂 {x}" if x else "Choose a category..."
    )

    # Query input with custom styling
    query = st.text_area(
        "Your Query:",
        placeholder="Example: How do I file GSTR-1 for quarterly filing? What are the due dates?",
        height=120,
        key="query_input",
        help="Describe your GST issue in detail for better resolution"
    )

    # Submit button with Apple styling
    if st.button(
        "🚀 Submit Query",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.processing or not st.session_state.system_initialized,
        help="Click to submit your GST query for AI-powered resolution"
    ):
        if query.strip():
            if selected_category:
                st.session_state.processing = True
                st.session_state.current_result = None
                process_query(query.strip(), selected_category)  # Pass category
                st.session_state.processing = False
                st.session_state.query_history.append(f"{query.strip()} [{selected_category}]")
                st.rerun()
            else:
                st.warning("⚠️ Please select a grievance category before submitting.")
        else:
            st.warning("⚠️ Please enter a query before submitting.")

    # Help text
    st.markdown("""
    <div style="margin-top: 1rem; padding: 1rem; background: rgba(0, 122, 255, 0.05); border-radius: 8px; border-left: 3px solid #007AFF;">
        <small style="color: #6e6e73;">
        <strong>💡 Tip:</strong> Select the appropriate category and provide detailed information about your GST issue for better and faster resolution.
        Include relevant dates, error messages, and specific context if available.
        </small>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def process_query(query: str, selected_category: str):
    """Process the query through the GST resolution system"""
    try:
        # Create a placeholder for processing status
        processing_placeholder = st.empty()

        # Show processing status with agent updates
        with processing_placeholder.container():
            st.markdown('<div class="processing-apple">', unsafe_allow_html=True)
            st.markdown('<div class="processing-title">🔄 Processing Your Query</div>', unsafe_allow_html=True)
            st.markdown('<div class="processing-status">Our multi-agent system is analyzing your query...</div>', unsafe_allow_html=True)

            # Create progress bar and status text for real-time updates
            progress_bar = st.progress(0)
            status_text = st.empty()

            result = None
            error_occurred = False

            # Import the actual GST resolution system
            from src.workflows.gst_workflow import process_gst_grievance

            # Define progress callback function that will be called by the backend
            def progress_callback(agent_name: str, description: str, progress: float):
                """Real-time progress callback from backend agents"""
                # Update progress bar
                progress_bar.progress(progress)

                # Update status for the current agent
                status_text.markdown(f"""
                    <div class="processing-status" style="margin-top: 1rem;">
                        <strong style="color: #007AFF; font-size: 1.1rem;">{agent_name}</strong><br>
                        <small style="color: #6e6e73;">{description}</small>
                    </div>
                """, unsafe_allow_html=True)

            try:
                logger.info(f"🚀 Starting GST workflow execution for query: {query[:100]}...")

                # Start the actual GST workflow processing with real-time progress callback
                # The backend will now call our progress_callback function as each agent completes
                result = process_gst_grievance(query, None, selected_category, progress_callback)

                if result:
                    logger.info("✅ GST workflow completed successfully")
                    logger.info(f"   Response generated: {len(result.get('response', ''))} characters")
                    logger.info(f"   Confidence: {result.get('confidence', 0)}%")
                    logger.info(f"   Sources used: {result.get('sources', {}).get('total_sources', 0)}")

                    # Ensure final progress bar is complete
                    progress_bar.progress(1.0)
                    status_text.markdown("""
                        <div class="processing-status" style="margin-top: 1rem;">
                            <strong style="color: #34C759; font-size: 1.1rem;">✅ Processing Complete</strong><br>
                            <small style="color: #6e6e73;">Preparing your results...</small>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    logger.error("❌ GST workflow returned no result")
                    error_occurred = True
                    result = create_fallback_result(query, "Workflow returned no result")

            except Exception as e:
                logger.error(f"❌ Error in GST resolution workflow: {e}")
                error_occurred = True
                result = create_fallback_result(query, str(e))

            # Small delay to show completion status
            time.sleep(0.5)

            st.markdown('</div>', unsafe_allow_html=True)

        # Clear processing indicator
        processing_placeholder.empty()

        # Store the result
        if result:
            st.session_state.current_result = result

            # Display success message
            if not error_occurred:
                st.success("✅ Query processed successfully!")
            else:
                st.warning("⚠️ Query processed with some issues. Please review the result.")
        else:
            st.error("❌ Failed to process query. Please try again.")

    except Exception as e:
        logger.error(f"Error processing query: {e}")
        st.error(f"❌ Error processing query: {str(e)}")
        # Create fallback result
        fallback_result = create_fallback_result(query, str(e))
        st.session_state.current_result = fallback_result
    finally:
        st.session_state.processing = False

def create_fallback_result(query: str, error_message: str = "Unknown error") -> Dict[str, Any]:
    """Create a fallback result when the main system fails"""
    import uuid

    return {
        "session_id": str(uuid.uuid4()),
        "query": query,
        "response": f"""**GST Query Processing Issue**

We encountered an issue while processing your query: "{query}"

**Temporary Resolution:**
1. **Primary Action**: Please try again or contact support
2. **Alternative**: Visit the official GST portal for direct assistance
3. **Support**: Reach out to GST helpdesk at 1800-103-4786

**Common Solutions:**
- Check your internet connection
- Verify your GST credentials
- Clear browser cache and cookies
- Try during off-peak hours

**Error Details:** {error_message}

**Next Steps:**
- If the issue persists, please contact technical support
- Your query has been logged for manual review
- We apologize for the inconvenience""",
        "confidence": 0,
        "requires_escalation": True,
        "processing_time": 0.0,
        "sources": {
            "local_count": 0,
            "web_count": 0,
            "twitter_count": 0,
            "total_sources": 0
        },
        "resolution_stats": {
            "overall_confidence": 0,
            "requires_escalation": True
        },
        "errors": [error_message],
        "timestamp": datetime.now().isoformat()
    }

def display_results():
    """Display the query results"""
    if not st.session_state.current_result:
        return

    result = st.session_state.current_result

    st.markdown('<div class="result-container apple-fade-in">', unsafe_allow_html=True)

    # Result header
    st.markdown('<h3 class="apple-card-title">📋 Resolution Result</h3>', unsafe_allow_html=True)

    # Metrics row with Apple styling
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        confidence_class = "confidence-high" if result['confidence'] >= 90 else "confidence-medium" if result['confidence'] >= 70 else "confidence-low"
        st.markdown(f'<div class="metric-apple"><div class="metric-value-apple {confidence_class}">{result["confidence"]}%</div><div class="metric-label-apple">Confidence</div></div>', unsafe_allow_html=True)

    with col2:
        st.markdown(f'<div class="metric-apple"><div class="metric-value-apple">{result["sources"]["total_sources"]}</div><div class="metric-label-apple">Sources Used</div></div>', unsafe_allow_html=True)

    with col3:
        status = "✅ Resolved" if not result['requires_escalation'] else "⚠️ Escalation Required"
        status_class = "confidence-high" if not result['requires_escalation'] else "confidence-medium"
        st.markdown(f'<div class="metric-apple"><div class="metric-value-apple {status_class}">{status}</div><div class="metric-label-apple">Resolution Status</div></div>', unsafe_allow_html=True)

    with col4:
        st.markdown(f'<div class="metric-apple"><div class="metric-value-apple">{result["processing_time"]:.1f}s</div><div class="metric-label-apple">Processing Time</div></div>', unsafe_allow_html=True)

    st.markdown('<hr style="margin: 1rem 0; border: none; border-top: 1px solid rgba(0, 0, 0, 0.05);">', unsafe_allow_html=True)

    # Source Overview - Positioned between Resolution Result and AI Resolution
    sources = result["sources"]
    st.markdown('<h4 style="color: #1d1d1f; font-weight: 600; margin: 2rem 0 1rem 0;">📊 Source Overview</h4>', unsafe_allow_html=True)
    source_metrics_col1, source_metrics_col2, source_metrics_col3, source_metrics_col4 = st.columns(4)

    with source_metrics_col1:
        st.markdown(f'<div class="metric-apple"><div class="metric-value-apple">📖 {sources["local_count"]}</div><div class="metric-label-apple">Local KB</div></div>', unsafe_allow_html=True)

    with source_metrics_col2:
        st.markdown(f'<div class="metric-apple"><div class="metric-value-apple">🌐 {sources["web_count"]}</div><div class="metric-label-apple">Web Search</div></div>', unsafe_allow_html=True)

    with source_metrics_col3:
        st.markdown(f'<div class="metric-apple"><div class="metric-value-apple">📱 {sources["twitter_count"]}</div><div class="metric-label-apple">Twitter</div></div>', unsafe_allow_html=True)

    with source_metrics_col4:
        llm_count = sources.get('llm_count', 0)
        st.markdown(f'<div class="metric-apple"><div class="metric-value-apple">🤖 {llm_count}</div><div class="metric-label-apple">LLM Reasoning</div></div>', unsafe_allow_html=True)

    st.markdown('<hr style="margin: 1rem 0; border: none; border-top: 1px solid rgba(0, 0, 0, 0.05);">', unsafe_allow_html=True)

    # Main response with Apple styling
    st.markdown('<h3 class="apple-card-title">💬 AI Resolution</h3>', unsafe_allow_html=True)
    st.markdown(f'<div class="response-container">{result["response"]}</div>', unsafe_allow_html=True)

    # Source information - Interactive and Expandable
    st.markdown('<h3 class="apple-card-title">📚 Information Sources</h3>', unsafe_allow_html=True)

    # Create a clickable container for sources breakdown
    with st.expander(f"🔍 **View Detailed Source Breakdown** ({sources['total_sources']} total sources)", expanded=False):

        # Add detailed source breakdown section
        st.markdown('<h4 style="color: #1d1d1f; font-weight: 600; margin-bottom: 1rem;">📋 Detailed Source Analysis</h4>', unsafe_allow_html=True)

        # Display expandable sections for each source type
        col1, col2 = st.columns(2)

        with col1:
            # Local Knowledge Base Sources
            if sources['local_count'] > 0:
                with st.expander(f"📖 Local Knowledge Base Sources ({sources['local_count']} items)", expanded=False):
                    st.markdown("""
                    <div class="source-apple">
                    <div class="source-title-apple">Local Knowledge Base Sources:</div>
                    <div class="source-content-apple">
                    • GST documentation and regulations<br>
                    • Official GST portal guides<br>
                    • Legal provisions and sections<br>
                    • Procedural guidelines
                    </div>
                    </div>
                    """, unsafe_allow_html=True)

                    # If we have access to detailed source info, display it
                    if 'detailed_sources' in result and 'local_sources' in result['detailed_sources']:
                        for i, source in enumerate(result['detailed_sources']['local_sources'][:5], 1):
                            st.markdown(f"""
                            <div class="source-apple">
                            <div class="source-title-apple">{i}. {source.get('title', 'Unknown Document')}</div>
                            <div class="source-citation-apple">Source: {source.get('citation', 'N/A')}</div>
                            <div class="source-content-apple">Relevance: {source.get('relevance_score', 0):.2f}<br>
                            Preview: {source.get('content', '')[:200]}...</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="source-apple">
                        <div class="source-content-apple">📄 Local knowledge base includes GST regulations, procedural guides, and official documentation</div>
                        </div>
                        """, unsafe_allow_html=True)

            # Twitter Sources
            if sources['twitter_count'] > 0:
                with st.expander(f"📱 Twitter Updates ({sources['twitter_count']} updates)", expanded=False):
                    st.markdown("""
                    <div class="source-apple">
                    <div class="source-title-apple">Twitter Sources:</div>
                    <div class="source-content-apple">
                    • Official GSTN updates<br>
                    • Recent circular notifications<br>
                    • System status updates<br>
                    • Policy changes
                    </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if 'detailed_sources' in result and 'twitter_sources' in result['detailed_sources']:
                        for i, source in enumerate(result['detailed_sources']['twitter_sources'][:3], 1):
                            st.markdown(f"""
                            <div class="source-apple">
                            <div class="source-title-apple">{i}. {source.get('citation', 'Unknown Tweet')}</div>
                            <div class="source-citation-apple">Date: {source.get('date', 'N/A')}</div>
                            <div class="source-content-apple">{source.get('content', '')[:300]}...</div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="source-apple">
                        <div class="source-content-apple">🐦 Twitter sources include official GSTN updates and recent notifications</div>
                        </div>
                        """, unsafe_allow_html=True)

        with col2:
            # Web Search Sources
            if sources['web_count'] > 0:
                with st.expander(f"🌐 Web Search Results ({sources['web_count']} sources)", expanded=False):
                    if 'detailed_sources' in result and 'web_sources' in result['detailed_sources']:
                        for i, source in enumerate(result['detailed_sources']['web_sources'], 1):
                            st.markdown(f"""
                            <div class="source-apple">
                            <div class="source-title-apple">{i}. {source.get('title', source.get('citation', 'Unknown Source'))}</div>
                            <div class="source-citation-apple">
                            <a href="{source.get('citation', '#')}" target="_blank" style="color: #007AFF; text-decoration: none;">
                            🔗 {source.get('citation', 'Link')}
                            </a>
                            </div>
                            <div class="source-content-apple">
                            <strong>Relevance:</strong> {source.get('relevance_score', 0):.2f}<br>
                            <strong>Date:</strong> {source.get('date', 'N/A')}<br><br>
                            <strong>Content:</strong><br>
                            {source.get('content', 'No content available')}
                            </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="source-apple">
                        <div class="source-content-apple">🌐 Web sources include official GST portals, government notifications, and current guidelines</div>
                        </div>
                        """, unsafe_allow_html=True)

            # LLM Reasoning Sources
            if 'llm_count' in sources and sources['llm_count'] > 0:
                with st.expander(f"🤖 LLM Reasoning Analysis ({sources['llm_count']} insights)", expanded=False):
                    if 'detailed_sources' in result and 'llm_sources' in result['detailed_sources']:
                        for i, source in enumerate(result['detailed_sources']['llm_sources'], 1):
                            st.markdown(f"""
                            <div class="source-apple">
                            <div class="source-title-apple">{i}. {source.get('citation', 'Expert Analysis')}</div>
                            <div class="source-content-apple">
                            {source.get('content', 'No content available')}
                            </div>
                            </div>
                            """, unsafe_allow_html=True)
                    else:
                        st.markdown("""
                        <div class="source-apple">
                        <div class="source-content-apple">🧠 LLM reasoning provides expert analysis and insights from GST professionals</div>
                        </div>
                        """, unsafe_allow_html=True)

    
    
    # Action buttons with Apple styling
    st.markdown('<hr style="margin: 1rem 0; border: none; border-top: 1px solid rgba(0, 0, 0, 0.05);">', unsafe_allow_html=True)

    # No copy button - removed functionality

    # Errors if any with Apple styling
    if result.get('errors'):
        st.markdown('<h3 class="apple-card-title">⚠️ Processing Errors</h3>', unsafe_allow_html=True)
        for error in result['errors']:
            st.markdown(f'<div class="apple-error">❌ {error}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

def display_footer():
    """Display the footer"""
    st.markdown("""
    <div class="footer">
        <p>🏛️ GST Grievance Resolution System | Powered by Multi-Agent RAG Technology</p>
        <p><small>Built with LangGraph, Streamlit, and Advanced AI Models</small></p>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main application function"""
    # Load custom CSS
    load_custom_css()

    # Initialize session state
    initialize_session_state()

    # Initialize system if not already done
    if not st.session_state.system_initialized:
        with st.spinner("Initializing GST Resolution System..."):
            if initialize_system():
                st.success("✅ System initialized successfully!")
                # Force a rerun to update the sidebar status
                st.rerun()
            else:
                st.error("❌ Failed to initialize system. Please refresh the page.")
                st.stop()

    # Display components
    display_header()
    display_sidebar()
    display_query_input()

    # Display results if available
    if st.session_state.current_result:
        display_results()

    # Display footer
    display_footer()

if __name__ == "__main__":
    main()