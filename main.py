#!/usr/bin/env python3
"""
GST Grievance Resolution System - Main Entry Point

A multi-agent RAG system for automated GST grievance resolution using LangGraph orchestration.
"""

import os
import sys
import logging
from typing import Dict, Any

try:
    from IPython.display import display, Markdown
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False
    def display(content):
        print(content)
    def Markdown(content):
        return content

from src.utils.embeddings import initialize_all
from src.workflows.gst_workflow import process_gst_grievance

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def display_result(result: Dict[str, Any]):
    """Display the resolution result in a formatted way"""
    print("\n" + "="*80)
    print("🎯 GST GRIEVANCE RESOLUTION RESULT")
    print("="*80)

    # Main response
    print(f"\n📋 RESPONSE:")
    print(result['response'])

    # Confidence and escalation
    print(f"\n📊 CONFIDENCE: {result['confidence']}%")
    if result['requires_escalation']:
        print("⚠️  REQUIRES MANUAL ESCALATION")
    else:
        print("✅ AUTO-RESOLVED")

    # Sources
    print(f"\n📚 SOURCES: {result['sources']['total_sources']} total")
    print(f"   📖 Local Knowledge Base: {result['sources']['local_count']}")
    print(f"   🌐 Web Search: {result['sources']['web_count']}")
    print(f"   📱 Twitter Updates: {result['sources']['twitter_count']}")

    # Processing info
    print(f"\n⏱️  Processing Time: {result['processing_time']:.2f} seconds")
    print(f"🆔 Session ID: {result['session_id']}")

    # Errors if any
    if result['errors']:
        print(f"\n⚠️  ERRORS:")
        for error in result['errors']:
            print(f"   - {error}")

    print("\n" + "="*80)


def main():
    """Main application entry point"""
    print("🚀 Initializing GST Grievance Resolution System...")
    print("="*80)

    # Initialize all models and embeddings
    if not initialize_all():
        print("❌ Failed to initialize system components. Check your configuration.")
        sys.exit(1)

    print("✅ System initialized successfully!")
    print("\n📝 Available commands:")
    print("   - Type your GST query and press Enter")
    print("   - Type 'quit' or 'exit' to exit")
    print("   - Type 'help' for more information")
    print("\n💡 Example queries:")
    print("   - How do I file GSTR-1 for quarterly filing?")
    print("   - What is the due date for GSTR-3B?")
    print("   - How to claim input tax credit?")
    print("   - E-way bill generation error")
    print("\n" + "="*80)

    # Interactive loop
    while True:
        try:
            # Get user input
            query = input("\n🔍 Enter your GST query: ").strip()

            # Handle commands
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Thank you for using GST Grievance Resolution System!")
                break
            elif query.lower() == 'help':
                print("\n📖 HELP:")
                print("This system helps resolve GST-related grievances using AI.")
                print("Simply type your question about GST and press Enter.")
                print("Examples:")
                print("- Registration issues")
                print("- Return filing problems")
                print("- E-way bill generation")
                print("- Refund status")
                print("- Payment issues")
                print("- Notices and compliance")
                continue
            elif not query:
                print("⚠️  Please enter a valid query.")
                continue

            # Process the query
            print(f"\n🔄 Processing: {query}")
            result = process_gst_grievance(query)

            # Display result
            display_result(result)

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"❌ Error processing query: {e}")
            print(f"\n❌ An error occurred: {e}")
            print("Please try again or contact support.")


def demo():
    """Run a demo with predefined queries"""
    print("🎬 Running GST Grievance Resolution Demo...")
    print("="*80)

    # Initialize system
    if not initialize_all():
        print("❌ Failed to initialize system components.")
        return

    # Demo queries
    demo_queries = [
        "How do I file GSTR-1 for quarterly filing?",
        "What is the due date for GSTR-3B filing?",
        "How to claim input tax credit under GST?",
        "E-way bill is not generating, what should I do?"
    ]

    for i, query in enumerate(demo_queries, 1):
        print(f"\n🔍 Demo Query {i}: {query}")
        print("-" * 60)

        try:
            result = process_gst_grievance(query)
            display_result(result)
        except Exception as e:
            print(f"❌ Error: {e}")

        if i < len(demo_queries):
            input("\nPress Enter to continue to next demo query...")

    print("\n🎬 Demo completed!")


if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        demo()
    else:
        main()