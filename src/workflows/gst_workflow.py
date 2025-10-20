"""
Main workflow orchestration for GST Grievance Resolution System
"""

import time
import uuid
import logging
from datetime import datetime
from typing import Dict, Any

from langgraph.graph import StateGraph, END

from ..models.schemas import AgentState
from ..agents.preprocessing_agent import PreprocessingAgent
from ..agents.classification_agent import ClassificationAgent
from ..agents.resolution_agents import (
    RetrievalOrchestratorAgent,
    ResolverAgent,
    ResponseGenerationAgent
)
from ..utils.embeddings import (
    initialize_all,
    local_embeddings
)
from ..config.settings import Config

logger = logging.getLogger(__name__)


def should_escalate(state: AgentState) -> str:
    """Determine if escalation is needed based on confidence"""
    resolver_output = state.get("resolver_output")
    if resolver_output is not None and resolver_output.requires_escalation:
        return "escalate"
    return "continue"


def handle_escalation(state: AgentState) -> Dict[str, Any]:
    """Handle escalation for complex cases"""
    logger.info("🔄 Agent 6: Escalating...")
    # Return only the key that needs updating
    return {"escalation_requested": True}


def create_workflow(progress_callback=None) -> StateGraph:
    """Create the LangGraph workflow for GST grievance resolution"""

    # Initialize all models if not already done
    from ..utils.embeddings import initialize_all, local_embeddings

    # Ensure all models are initialized
    if local_embeddings is None:
        logger.info("🔄 Initializing models...")
        if not initialize_all():
            logger.error("❌ Failed to initialize models")
            # Continue with basic functionality even if some models fail
            logger.warning("⚠️ Some models failed to initialize, using fallback mode")

    # Get LLMs from centralized config
    preprocessor_llm = Config.get_preprocessor_llm()
    classifier_llm = Config.get_classifier_llm()
    resolver_llm = Config.get_resolver_llm()

    # Initialize agents with proper error handling
    try:
        preprocessing_agent = PreprocessingAgent(preprocessor_llm)
        logger.info("✅ Preprocessing agent initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize preprocessing agent: {e}")
        preprocessing_agent = None

    try:
        classification_agent = ClassificationAgent(classifier_llm)
        logger.info("✅ Classification agent initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize classification agent: {e}")
        classification_agent = None

    try:
        retrieval_agent = RetrievalOrchestratorAgent(
            embeddings=local_embeddings,
            kb_folder="./",
            status_callback=None  # Progress tracking handled at workflow level
        )
        logger.info("✅ Retrieval orchestrator agent initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize retrieval agent: {e}")
        retrieval_agent = None

    try:
        resolver_agent = ResolverAgent(resolver_llm)
        logger.info("✅ Resolver agent initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize resolver agent: {e}")
        resolver_agent = None

    try:
        response_agent = ResponseGenerationAgent()
        logger.info("✅ Response generation agent initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize response agent: {e}")
        response_agent = None

    # Create workflow graph
    workflow = StateGraph(AgentState)

    # Add nodes with progress tracking
    def preprocessing_with_progress(state):
        if progress_callback:
            progress_callback("🔍 Agent 1: Preprocessing", "Cleaning and analyzing your query...", 0.2)
        return preprocessing_agent.process(state)

    def classification_with_progress(state):
        if progress_callback:
            progress_callback("📊 Agent 2: Classification", "Categorizing your GST issue...", 0.4)
        return classification_agent.process(state)

    def retrieval_with_progress(state):
        if progress_callback:
            progress_callback("🔎 Agent 3: Multi-Source Retrieval", "Searching knowledge bases and web...", 0.6)
        return retrieval_agent.process(state)

    def resolver_with_progress(state):
        if progress_callback:
            progress_callback("🤖 Agent 4: Resolution", "Analyzing information and generating resolution...", 0.8)
        return resolver_agent.process(state)

    def response_generation_with_progress(state):
        if progress_callback:
            progress_callback("✍️ Agent 5: Response Generation", "Formatting final response...", 1.0)
        return response_agent.process(state)

    def escalation_with_progress(state):
        if progress_callback:
            progress_callback("⚠️ Agent 6: Escalation", "Case requires manual escalation...", 0.9)
        return handle_escalation(state)

    workflow.add_node("preprocessing", preprocessing_with_progress)
    workflow.add_node("classification", classification_with_progress)
    workflow.add_node("retrieval", retrieval_with_progress)
    workflow.add_node("resolver", resolver_with_progress)
    workflow.add_node("response_generation", response_generation_with_progress)
    workflow.add_node("escalation", escalation_with_progress)

    # Set entry point
    workflow.set_entry_point("preprocessing")

    # Add edges
    workflow.add_edge("preprocessing", "classification")
    workflow.add_edge("classification", "retrieval")
    workflow.add_edge("retrieval", "resolver")
    workflow.add_edge("response_generation", END)
    workflow.add_edge("escalation", END)

    # Add conditional edge for escalation - this replaces the direct resolver->response_generation edge
    workflow.add_conditional_edges(
        "resolver",
        should_escalate,
        {
            "escalate": "escalation",
            "continue": "response_generation"
        }
    )

    return workflow


class GSTGrievanceResolver:
    """Main resolver class for GST grievances"""

    def __init__(self):
        """Initialize the resolver with workflow"""
        self.progress_callback = None
        self.workflow = create_workflow(self._update_progress)
        self.app = self.workflow.compile()

    def set_progress_callback(self, callback):
        """Set a callback function to receive real-time progress updates"""
        self.progress_callback = callback

    def _update_progress(self, agent_name: str, description: str, progress: float):
        """Update progress if callback is set"""
        if self.progress_callback:
            self.progress_callback(agent_name, description, progress)

    def process_query(self, query: str, session_id: str = None, selected_category: str = None) -> Dict[str, Any]:
        """
        Process a GST grievance query through the complete workflow

        Args:
            query: User's GST query
            session_id: Optional session ID for tracking
            selected_category: User-selected grievance category

        Returns:
            Complete resolution result with metadata
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = str(uuid.uuid4())

        # Initialize state
        initial_state = AgentState(
            user_query=query,
            session_id=session_id,
            selected_category=selected_category,
            conversation_history=[],
            preprocessing_output=None,
            classification_output=None,
            retrieval_output=None,
            resolver_output=None,
            final_response=None,
            timestamp=datetime.now().isoformat(),
            processing_time=0.0,
            errors=[],
            iteration_count=0,
            escalation_requested=False
        )

        # Process workflow
        start_time = time.time()
        logger.info("=" * 80)
        logger.info("🚀 Starting GST Grievance Resolution")
        logger.info(f"📝 Query: {query}")
        logger.info("=" * 80)

        try:
            # Execute using the compiled LangGraph workflow with progress tracking
            logger.info("🚀 Executing optimized workflow...")
            logger.info(f"⚡ OPTIMIZATION: Using centralized LLM configuration")
            logger.info(f"⚡ OPTIMIZATION: Reused pre-initialized agents (was: re-initializing per query)")

            # Execute workflow with progress callbacks
            final_state = self.app.invoke(initial_state)
            processing_time = time.time() - start_time

            # Prepare result with detailed source information
            retrieval_output = final_state.get("retrieval_output")

            # Create detailed sources for web interface
            detailed_sources = {}
            if retrieval_output:
                # Local knowledge base sources
                detailed_sources["localSources"] = [
                    {
                        "title": f"Document {i+1}",
                        "content": result.content,
                        "citation": result.citation,
                        "relevanceScore": result.relevance_score,
                        "date": result.date
                    }
                    for i, result in enumerate(retrieval_output.local_results[:10])
                ]

                # Web search sources
                detailed_sources["webSources"] = [
                    {
                        "title": f"Web Result {i+1}",
                        "content": result.content,
                        "citation": result.citation,
                        "relevanceScore": result.relevance_score,
                        "date": result.date
                    }
                    for i, result in enumerate(retrieval_output.web_results[:10])
                ]

                # Twitter sources
                detailed_sources["twitterSources"] = [
                    {
                        "title": f"Tweet {i+1}",
                        "content": result.content,
                        "citation": result.citation,
                        "relevanceScore": result.relevance_score,
                        "date": result.date
                    }
                    for i, result in enumerate(retrieval_output.twitter_results[:5])
                ]

                # LLM reasoning sources
                detailed_sources["llmSources"] = [
                    {
                        "title": f"LLM Analysis {i+1}",
                        "content": result.content,
                        "citation": result.citation,
                        "relevanceScore": result.relevance_score,
                        "date": result.date
                    }
                    for i, result in enumerate(retrieval_output.llm_reasoning[:5])
                ]

            result = {
                "session_id": session_id,
                "query": query,
                "response": final_state["final_response"].direct_answer if final_state.get("final_response") else "No response generated",
                "confidence": final_state["resolver_output"].overall_confidence if final_state.get("resolver_output") else 0,
                "requires_escalation": final_state["escalation_requested"],
                "processingTime": processing_time,
                "sources": {
                    "localCount": len(retrieval_output.local_results) if retrieval_output else 0,
                    "webCount": len(retrieval_output.web_results) if retrieval_output else 0,
                    "twitterCount": len(retrieval_output.twitter_results) if retrieval_output else 0,
                    "llmCount": len(retrieval_output.llm_reasoning) if retrieval_output else 0,
                    "totalCount": retrieval_output.total_sources if retrieval_output else 0
                },
                "detailedSources": detailed_sources,
                "errors": final_state["errors"],
                "timestamp": final_state["timestamp"]
            }

            logger.info("=" * 80)
            logger.info(f"✅ Complete. Time: {processing_time:.2f}s")
            logger.info(f"🎯 Confidence: {result['confidence']}%")
            logger.info("=" * 80)

            return result

        except Exception as e:
            logger.error(f"❌ Workflow failed: {e}")
            processing_time = time.time() - start_time

            return {
                "session_id": session_id,
                "query": query,
                "response": "I apologize, but an error occurred while processing your query. Please try again or contact support.",
                "confidence": 0,
                "requires_escalation": True,
                "processingTime": processing_time,
                "sources": {"localCount": 0, "webCount": 0, "twitterCount": 0, "llmCount": 0, "totalCount": 0},
                "errors": [str(e)],
                "timestamp": datetime.now().isoformat()
            }


# Global resolver instance
_resolver = None


def get_resolver() -> GSTGrievanceResolver:
    """Get or create the global resolver instance"""
    global _resolver
    if _resolver is None:
        _resolver = GSTGrievanceResolver()
    return _resolver


def process_gst_grievance(query: str, session_id: str = None, selected_category: str = None, progress_callback=None) -> Dict[str, Any]:
    """
    Process a GST grievance query (convenience function)

    Args:
        query: User's GST query
        session_id: Optional session ID for tracking
        selected_category: User-selected grievance category
        progress_callback: Optional callback function for real-time progress updates

    Returns:
        Complete resolution result with metadata
    """
    resolver = get_resolver()
    if progress_callback:
        resolver.set_progress_callback(progress_callback)
    return resolver.process_query(query, session_id, selected_category)
