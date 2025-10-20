#!/usr/bin/env python3
"""
GST Grievance Resolution System - Web Application Launcher

This script launches the professional web interface for the GST grievance resolution system.
Usage: python run_web_app.py
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import streamlit
        logger.info("✅ Streamlit is available")
    except ImportError:
        logger.error("❌ Streamlit is not installed. Please run: pip install streamlit")
        return False

    try:
        import torch
        logger.info("✅ PyTorch is available")
    except ImportError:
        logger.error("❌ PyTorch is not installed. Please run: pip install torch")
        return False

    try:
        import faiss
        logger.info("✅ FAISS is available")
    except ImportError:
        logger.error("❌ FAISS is not installed. Please run: pip install faiss-cpu")
        return False

    return True

def check_environment():
    """Check if environment variables are set"""
    env_vars = [
        'GOOGLE_API_KEY',
        'TAVILY_API_KEY',
        'TWITTER_BEARER_TOKEN',
        'DEEPSEEK_API_KEY'
    ]

    missing_vars = []
    for var in env_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        logger.warning(f"⚠️ Missing environment variables: {', '.join(missing_vars)}")
        logger.warning("Some features may not work properly without these API keys.")
        logger.info("Please set these variables in your .env file or environment.")
        logger.info("The system will still work with local knowledge base for basic functionality.")
        # Don't return False - allow the system to run with limited functionality
        return True  # Allow system to run even with missing API keys

    logger.info("✅ All environment variables are set")
    return True

def launch_streamlit():
    """Launch the Streamlit application"""
    try:
        logger.info("🚀 Launching GST Grievance Resolution System Web Interface...")
        logger.info("📋 The application will open in your default web browser")
        logger.info("🌐 Local URL: http://localhost:8501")
        logger.info("🔗 Network URL: http://localhost:8501")
        logger.info("⏹️  Press Ctrl+C to stop the server")

        # Run streamlit with the app.py file
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 'app.py',
            '--server.port', '8501',
            '--server.address', 'localhost',
            '--server.headless', 'false',
            '--browser.gatherUsageStats', 'false'
        ], check=True)

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to launch Streamlit: {e}")
        return False
    except KeyboardInterrupt:
        logger.info("\n👋 GST Grievance Resolution System stopped by user")
        return True
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main launcher function"""
    print("=" * 80)
    print("🏛️ GST Grievance Resolution System - Web Interface Launcher")
    print("=" * 80)

    # Check dependencies
    if not check_dependencies():
        logger.error("❌ Missing dependencies. Please install them and try again.")
        sys.exit(1)

    # Check environment (optional - don't exit if missing)
    check_environment()

    print("\n🔧 Starting web application...")

    # Launch Streamlit
    if not launch_streamlit():
        logger.error("❌ Failed to launch web application")
        sys.exit(1)

if __name__ == "__main__":
    main()