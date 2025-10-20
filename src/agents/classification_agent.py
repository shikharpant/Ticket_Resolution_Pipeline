"""
Classification Agent for GST Grievance Resolution System
"""

import logging
import re
from typing import Dict, Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from ..models.schemas import (
    AgentState,
    ClassificationOutput
)
from ..models.schemas import GrievanceCategory

logger = logging.getLogger(__name__)


class ClassificationAgent:
    """Agent for classifying GST grievances using user-selected category"""

    def __init__(self, llm=None):
        # LLM is retained for future enhancements but current classification validates user input.
        self.llm = llm
        self.allowed_categories = {category.value for category in GrievanceCategory}
        self.normalized_lookup = {
            self._normalize(category): category
            for category in self.allowed_categories
        }

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", value.strip().lower())

    def process(self, state: AgentState) -> AgentState:
        try:
            logger.info("🔄 Agent 2: Using user-selected category...")

            # Get user-selected category from state
            selected_category = state.get("selected_category")

            if not selected_category:
                logger.warning("⚠️ No user category selected, defaulting to Others")
                selected_category = GrievanceCategory.OTHERS.value

            normalized = self._normalize(selected_category)
            if normalized in self.normalized_lookup:
                resolved_category = self.normalized_lookup[normalized]
                confidence = 100.0
            else:
                logger.warning("⚠️ Unrecognized category '%s', defaulting to Others", selected_category)
                resolved_category = GrievanceCategory.OTHERS.value
                confidence = 50.0

            # Create classification output based on user selection
            classification_output = ClassificationOutput(
                primary_category=resolved_category,
                secondary_categories=[],
                confidence_scores={resolved_category: confidence},
                sub_type=None
            )

            state["classification_output"] = classification_output

            # Detailed classification output
            logger.info("📊 DETAILED CLASSIFICATION OUTPUT:")
            logger.info(f"   Primary Category: {classification_output.primary_category}")
            logger.info("   Secondary Categories: None")
            logger.info("   🎯 CONFIDENCE SCORES:")
            logger.info(f"      {classification_output.primary_category}: {confidence}% (User input validated)")
            logger.info("   Sub-type: None")
            logger.info("   📝 CLASSIFICATION CONTEXT:")
            logger.info("      Source: Direct user selection with validation against approved categories")

            return state

        except Exception as e:
            logger.error(f"❌ Classification error: {e}")
            state["errors"].append(str(e))
            # Set default output on error
            state["classification_output"] = ClassificationOutput(
                primary_category=GrievanceCategory.OTHERS.value,
                secondary_categories=[],
                confidence_scores={GrievanceCategory.OTHERS.value: 50.0},
                sub_type=None
            )
            return state
