"""
Preprocessing Agent for GST Grievance Resolution System
"""

import json
import logging
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from ..models.schemas import (
    AgentState,
    PreprocessingOutput,
    ExtractedEntity,
    CoreIssue
)

logger = logging.getLogger(__name__)


class PreprocessingAgent:
    """Agent for preprocessing user queries and extracting entities"""

    def __init__(self, llm):
        self.llm = llm
        self.parser = JsonOutputParser(pydantic_object=PreprocessingOutput)
        self.prompt = ChatPromptTemplate.from_template("""
        You are a GST (Goods and Services Tax) preprocessing specialist. Your task is to clean and analyze the user's query.

        ANALYSIS TASKS:
        1. Clean the text - remove typos, expand abbreviations, fix grammar
        2. Detect the primary intent of the query
        3. Extract core issues (problems the user is facing)
        4. Identify key entities (GSTIN, dates, amounts, form numbers, etc.)
        5. Detect the language

        INTENTS TO CONSIDER:
        - informational: User wants information about a GST topic
        - procedural: User wants to know how to do something
        - error_resolution: User is facing an error or problem
        - compliance_clarification: User wants clarification on compliance requirements
        - refund_status: User asking about refund status

        EXAMPLE CORE ISSUES:
        - "Cannot file GSTR-1 due to validation error"
        - "Need to know due date for GSTR-3B filing"
        - "GST registration portal not working"
        - "Confusion about input tax credit claim"

        ENTITIES TO EXTRACT:
        - GSTIN numbers
        - Form names/numbers (GSTR-1, GSTR-3B, etc.)
        - Dates and periods
        - Amounts
        - Error codes
        - Portal/system names

        USER QUERY: {query}

        Provide a structured JSON response with the analysis.

        {format_instructions}
        """)

    def process(self, state: AgentState) -> AgentState:
        try:
            logger.info("🔄 Agent 1: Preprocessing...")

            if not self.llm:
                logger.error("❌ Preprocessing LLM not initialized")
                state["errors"].append("Preprocessing LLM not initialized")
                # Set default output
                state["preprocessing_output"] = PreprocessingOutput(
                    cleaned_text=state["user_query"],
                    detected_intent="informational",
                    core_issues=[CoreIssue(issue_text=state["user_query"], keywords=["query"], priority=1)],
                    entities=[],
                    language="en"
                )
                return state

            response = self.llm.invoke(self.prompt.format(
                query=state["user_query"],
                format_instructions=self.parser.get_format_instructions()
            ))

            # Parse JSON response
            preprocessing_output = PreprocessingOutput(**json.loads(response.content))
            state["preprocessing_output"] = preprocessing_output

            logger.info(f"✅ Found {len(preprocessing_output.core_issues)} issues")
            logger.info(f"   Intent: {preprocessing_output.detected_intent}")
            logger.info(f"   Entities: {len(preprocessing_output.entities)}")

            # Detailed preprocessing output
            logger.info("📋 DETAILED PREPROCESSING OUTPUT:")
            logger.info(f"   Original Query: {state['user_query']}")
            logger.info(f"   Cleaned Query: {preprocessing_output.cleaned_text}")
            logger.info(f"   Language: {preprocessing_output.language}")

            # Show core issues with details
            if preprocessing_output.core_issues:
                logger.info("   🔍 CORE ISSUES IDENTIFIED:")
                for i, issue in enumerate(preprocessing_output.core_issues, 1):
                    logger.info(f"      {i}. {issue.issue_text}")
                    logger.info(f"         Keywords: {issue.keywords}")
                    logger.info(f"         Priority: {issue.priority}")

            # Show entities with details
            if preprocessing_output.entities:
                logger.info("   🏷️  ENTITIES EXTRACTED:")
                for i, entity in enumerate(preprocessing_output.entities, 1):
                    logger.info(f"      {i}. {entity.entity_type}: {entity.value}")
                    if entity.context:
                        logger.info(f"         Context: {entity.context}")
            else:
                logger.info("   🏷️  ENTITIES: None extracted")

            return state

        except Exception as e:
            logger.error(f"❌ Preprocessing error: {e}")
            state["errors"].append(str(e))
            # Set default output on error
            state["preprocessing_output"] = PreprocessingOutput(
                cleaned_text=state["user_query"],
                detected_intent="informational",
                core_issues=[CoreIssue(issue_text=state["user_query"], keywords=["query"], priority=1)],
                entities=[],
                language="en"
            )
            return state