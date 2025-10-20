"""
Resolution Agents for GST Grievance Resolution System
"""

import json
import logging
from typing import Dict, Any, List, Callable, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from ..models.schemas import (
    AgentState,
    ResolverOutput,
    FinalResponse,
    RetrievalOutput
)
from ..config.settings import Config

logger = logging.getLogger(__name__)


class RetrievalOrchestratorAgent:
    """Orchestrates all retrieval agents (Local KB, Web, Twitter, LLM Reasoning)"""

    def __init__(self, embeddings=None, kb_folder: str = "./", status_callback: Optional[Callable[[str, float], None]] = None):
        """
        Initialize retrieval orchestrator

        Args:
            embeddings: Pre-initialized embeddings
            kb_folder: Knowledge base folder path
        """
        # Initialize all retrieval agents
        self.local_agent = LocalRetrievalAgent(
            embeddings=embeddings,
            kb_folder=kb_folder,
            enable_graph=True
        )

        self.web_agent = WebRetrievalAgent(
            provider="auto",
            unrestricted=Config.WEB_SEARCH_UNRESTRICTED
        )

        self.twitter_agent = TwitterRetrievalAgent()
        self.llm_agent = LLMReasoningAgent()
        self.status_callback = status_callback

        # Log initialization status
        logger.info("✅ Retrieval orchestrator initialized")
        stats = self.local_agent.get_stats()
        logger.info(f"   📊 Local KB:")
        logger.info(f"      Files: {stats['source_files']}")
        logger.info(f"      Chunks: {stats['document_count']}")
        logger.info(f"      Size: {stats['index_size_mb']:.2f} MB")
        if stats['graph_nodes'] > 0:
            logger.info(f"      Graph: {stats['graph_nodes']} nodes, {stats['graph_edges']} edges")
        logger.info(f"   🌐 Web search: {self.web_agent.provider} (LLM optimization: {'enabled' if self.web_agent.llm else 'disabled'})")
        logger.info(f"   🤖 LLM reasoning: {'enabled' if self.llm_agent.client else 'disabled'}")

    def process(self, state: AgentState) -> AgentState:
        """Process retrieval from all sources"""
        try:
            logger.info("🔄 Agent 3: Retrieving from multiple sources (4 agents)...")
            self._notify_status("Initiating parallel retrieval", 0.62)

            # Get preprocessing and classification outputs safely
            preprocessing = state.get("preprocessing_output")
            classification = state.get("classification_output")

            if not preprocessing:
                logger.error("❌ No preprocessing output available")
                state["errors"].append("No preprocessing output available")
                # Set empty retrieval output
                state["retrieval_output"] = RetrievalOutput(
                    twitter_results=[],
                    local_results=[],
                    web_results=[],
                    llm_reasoning=[],
                    total_sources=0,
                    retrieval_time=0.0
                )
                return state

            # Build keyword list
            all_keywords = []
            all_keywords.extend([issue.issue_text for issue in preprocessing.core_issues])
            all_keywords.extend([entity.value for entity in preprocessing.entities])
            if classification:
                all_keywords.extend([classification.primary_category])
                all_keywords.extend(classification.secondary_categories or [])

            # Execute parallel retrieval
            logger.info("   🔄 Executing parallel retrieval from 4 sources...")

            # Twitter retrieval
            self._notify_status("TwitterRetrievalAgent: searching timeline", 0.64)
            twitter_results = self.twitter_agent.retrieve(all_keywords, Config.MAX_TWITTER_RESULTS)

            # Local knowledge base retrieval
            self._notify_status("LocalRetrievalAgent: querying FAISS + graph", 0.68)
            local_results = self.local_agent.retrieve(
                query=state["user_query"],
                k=Config.MAX_LOCAL_RESULTS,
                filter_category=classification.primary_category if (classification and not Config.WEB_SEARCH_UNRESTRICTED) else None,
                use_graph=True
            )

            # Web search retrieval
            self._notify_status("WebRetrievalAgent: calling Tavily", 0.72)
            web_results = self.web_agent.retrieve(
                query=state["user_query"],
                category=classification.primary_category if (classification and not Config.WEB_SEARCH_UNRESTRICTED) else None,
                keywords=all_keywords,
                max_results=Config.MAX_WEB_RESULTS
            )

            # LLM reasoning retrieval
            self._notify_status("LLMReasoningAgent: synthesizing insights", 0.76)
            llm_reasoning = self.llm_agent.retrieve(
                core_issues=preprocessing.core_issues,
                entities=preprocessing.entities
            )

            self._notify_status("Aggregating retrieval results", 0.78)

            # Combine results
            retrieval_output = RetrievalOutput(
                twitter_results=twitter_results,
                local_results=local_results,
                web_results=web_results,
                llm_reasoning=llm_reasoning,
                total_sources=len(twitter_results) + len(local_results) + len(web_results) + len(llm_reasoning),
                retrieval_time=0.0  # Could be measured if needed
            )

            state["retrieval_output"] = retrieval_output

            logger.info(f"✅ Retrieved {retrieval_output.total_sources} sources")
            logger.info(f"   📱 Twitter: {len(twitter_results)}")
            logger.info(f"   📖 Local KB: {len(local_results)}")
            logger.info(f"   🌐 Web: {len(web_results)}")
            logger.info(f"   🤖 LLM Reasoning: {len(llm_reasoning)}")
            self._notify_status("Completed multi-source retrieval", 0.79)

            return state

        except Exception as e:
            logger.error(f"❌ Retrieval error: {e}")
            state["errors"].append(str(e))
            # Set empty retrieval output on error
            state["retrieval_output"] = RetrievalOutput(
                twitter_results=[],
                local_results=[],
                web_results=[],
                llm_reasoning=[],
                total_sources=0,
                retrieval_time=0.0
            )
            self._notify_status("Retrieval error encountered", 0.6)
            return state

    def _notify_status(self, description: str, progress: float):
        if self.status_callback:
            try:
                self.status_callback(description, progress)
            except Exception as exc:
                logger.debug(f"⚠️ Failed to send retrieval status update: {exc}")


class ResolverAgent:
    """Agent for resolving GST issues using retrieved information"""

    def __init__(self, llm):
        self.llm = llm
        self.parser = JsonOutputParser(pydantic_object=ResolverOutput)

    def process(self, state: AgentState) -> AgentState:
        """Process resolution using retrieved information"""
        try:
            resolver_model = Config.RESOLVER_MODEL
            logger.info(f"🔄 Agent 4: Resolving with {resolver_model}...")

            if not self.llm:
                logger.error("❌ Resolver LLM not initialized")
                state["errors"].append("Resolver LLM not initialized")
                # Set fallback resolver output
                state["resolver_output"] = ResolverOutput(
                    resolutions=[], overall_confidence=0, requires_escalation=True
                )
                return state

            # Get state components safely
            retrieval = state.get("retrieval_output")
            preprocessing = state.get("preprocessing_output")
            classification = state.get("classification_output")

            if not retrieval:
                logger.error("❌ No retrieval output available")
                state["errors"].append("No retrieval output available")
                state["resolver_output"] = ResolverOutput(
                    resolutions=[], overall_confidence=0, requires_escalation=True
                )
                return state

            if not preprocessing:
                logger.error("❌ No preprocessing output available")
                state["errors"].append("No preprocessing output available")
                state["resolver_output"] = ResolverOutput(
                    resolutions=[], overall_confidence=0, requires_escalation=True
                )
                return state

            # Format context for LLM
            context_parts = []

            # Add local knowledge base results
            if retrieval.local_results:
                context_parts.append("Local Knowledge Base:")
                for i, result in enumerate(retrieval.local_results[:5], 1):
                    context_parts.append(f"{i}. {result.content}\n   Source: {result.citation}")

            # Add web search results
            if retrieval.web_results:
                context_parts.append("\nWeb Search Results:")
                for i, result in enumerate(retrieval.web_results[:3], 1):
                    context_parts.append(f"{i}. {result.content}\n   Source: {result.citation}")

            # Add Twitter updates
            if retrieval.twitter_results:
                context_parts.append("\nTwitter Updates:")
                for i, result in enumerate(retrieval.twitter_results[:3], 1):
                    context_parts.append(f"- {result.content} ({result.citation})")

            # Add LLM reasoning
            if retrieval.llm_reasoning:
                context_parts.append("\nExpert Analysis:")
                for i, result in enumerate(retrieval.llm_reasoning[:2], 1):
                    context_parts.append(f"{i}. {result.content}")

            context_text = "\n".join(context_parts)

            # Build resolution prompt
            prompt = ChatPromptTemplate.from_template(""" 
                                                      You are an expert L1 GST (Goods & Services Tax) grievance resolution specialist. 
                                                      The user has filed a ticket with GSTN and you are responding to their ACTIVE TICKET as the first-line support agent.
                                                      ═══════════════════════════════════════════════════════════════
                                                        TICKET CONTEXT
                                                        ═══════════════════════════════════════════════════════════════
                                                        USER QUERY: {query}
                                                        CORE ISSUES IDENTIFIED: {issues}
                                                        DETECTED INTENT: {intent}
                                                        ISSUE CATEGORY: {category}

                                                        AVAILABLE INFORMATION:
                                                        {context}

                                                        ═══════════════════════════════════════════════════════════════
                                                        CRITICAL CONSTRAINTS - READ CAREFULLY
                                                        ═══════════════════════════════════════════════════════════════
                                                        ❌ DO NOT ask the user to "file a grievance ticket" - THIS IS the ticket response
                                                        ❌ DO NOT claim backend system access or modification capabilities
                                                        ❌ DO NOT promise "manual overrides" or "administrative tagging"
                                                        ❌ DO NOT suggest "raise a service request" - you ARE responding to the service request
                                                        ❌ DO NOT say "please submit a ticket" - ticket already exists and is active
                                                        ❌ DO NOT provide generic "we are looking into it" without concrete steps
                                                        ❌ DO NOT Create false expectations about agent intervention timelines
                                                        ✅ DO provide direct troubleshooting steps within current ticket workflow
                                                        ✅ DO Empower taxpayer with self-verification steps
                                                        ✅ DO comprehensive legal grounding with actual citations
                                                        ✅ DO guide user on updating THIS TICKET with additional information if needed
                                                        ✅ DO provide escalation pathways within the existing ticket system

                                                        ═══════════════════════════════════════════════════════════════
                                                        L1 RESPONSE STRUCTURE REQUIREMENTS
                                                        ═══════════════════════════════════════════════════════════════

                                                        Your response must be comprehensive, addressing ALL core issues in a unified resolution that includes:

                                                        1. TICKET METADATA
                                                        - Userprovided ticket {category} and {intent}
                                                        - Assign priority (Critical/High/Medium/Low) based on business impact
                                                        - Set current status: "Open - Under L1 Review"

                                                        2. ISSUE SUMMARY (2-3 sentences)
                                                        - Restate the taxpayer's problem in technical GST terms
                                                        - Identify specific forms, ARNs, periods, or transactions involved
                                                        - State the core impediment clearly

                                                        3. ROOT CAUSE ANALYSIS (Mandatory)
                                                        - Explain the underlying GST provision/portal mechanism causing the issue
                                                        - Reference specific notifications, rules, or circulars
                                                        - Clarify any misconceptions in the taxpayer's understanding
                                                        - Provide 2-4 bullet points maximum

                                                        4. LEGAL & STATUTORY BASIS (Mandatory - Critical for Quality)
                                                        - Cite specific CGST/SGST/IGST Act sections 
                                                        - Reference applicable CGST Rules with sub-rules 
                                                        - Include notification numbers and dates 
                                                        - Mention relevant circulars or GSTN advisories
                                                        - THIS IS MANDATORY - responses without legal grounding score below 70

                                                        5. IMMEDIATE RESOLUTION STEPS (Step-by-Step)
                                                        - Provide numbered, hierarchical action steps
                                                        - Include exact portal navigation paths (e.g., "Login → Services → Ledgers → Form DRC-03A")
                                                        - Specify what to verify and expected results at each step
                                                        - Add troubleshooting sub-section for common errors (browser cache, date formats, sync delays)
                                                        - Each step must be actionable and testable

                                                        6. ALTERNATIVE SOLUTIONS (If primary resolution fails)
                                                        - Option A: Technical workaround specific to the issue
                                                        - Option B: How to UPDATE THIS TICKET with additional information (not "file new ticket")
                                                        - Option C: Jurisdictional officer contact via portal or reach out to GST Seva Kendra in jurisdiction (Dashboard → Services → View Jurisdictional Details)
                                                        - Provide expected timeline for each escalation path

                                                        7. REQUIRED DOCUMENTATION CHECKLIST
                                                        - List all documents user should keep ready for escalation
                                                        - Format as checkbox list 

                                                        8. IMPORTANT NOTES & PREVENTIVE GUIDANCE
                                                        - Any undertakings or declarations taxpayer must make
                                                        - Compliance obligations during pendency
                                                        - How to avoid this issue in future filings
                                                        - Multiple filing/adjustment capabilities if applicable

                                                        10. NEXT STEPS - TICKET LIFECYCLE
                                                            - Immediate actions required from taxpayer (specific steps 1-3)
                                                            - Follow-up protocol: "Update THIS TICKET with outcome within [timeframe]"
                                                            - Auto-escalation trigger if no response/resolution by [date]
                                                            - Clear ticket status and assignment

                                                        ═══════════════════════════════════════════════════════════════
                                                        CONFIDENCE SCORING GUIDELINES
                                                        ═══════════════════════════════════════════════════════════════
                                                        Assign confidence based on:

                                                        95-100: HIGH CONFIDENCE
                                                        - Clear legal basis with specific sections/rules/notifications cited
                                                        - Standard issue with documented resolution procedure
                                                        - All necessary information available in context
                                                        - Portal navigation path verified
                                                        - Expected outcome predictable

                                                        85-94: GOOD CONFIDENCE  
                                                        - Reasonable legal basis, may lack some notification details
                                                        - Resolution procedure exists but may have variations
                                                        - Most necessary information available
                                                        - Minor uncertainties in timeline or exact steps

                                                        70-84: MODERATE CONFIDENCE
                                                        - Generic legal basis (act mentioned but not specific rules)
                                                        - Resolution path exists but with multiple conditional branches
                                                        - Some information gaps requiring user input
                                                        - Uncertain system behavior or recent portal changes

                                                        Below 70: LOW CONFIDENCE - REQUIRES ESCALATION
                                                        - Insufficient legal basis or contradictory provisions
                                                        - No clear resolution procedure in context
                                                        - Critical information missing (ARN, dates, specific error codes)
                                                        - Issue involves recent amendments or unclear notifications
                                                        - May require officer discretion or manual intervention

                                                        MINIMUM CONFIDENCE THRESHOLD: 95
                                                        If confidence < 95, set resolution to null with detailed reason and requires_escalation to true.

                                                        ═══════════════════════════════════════════════════════════════
                                                        SPECIAL GST DOMAIN CONSIDERATIONS
                                                        ═══════════════════════════════════════════════════════════════
                                                        - Check if there have been amendments in the forms/rules which the user is quoting if any
                                                        - Distinguish payment categories: 'Voluntary' vs 'Others' vs 'Demand' (affects auto-linkage)
                                                        - Electronic Liability Register (ELR) mechanics crucial for demand/payment issues
                                                        - Consider CGST/SGST/IGST split and jurisdiction implications
                                                        - Account for composition vs regular taxpayer differences
                                                        - Reference form interconnections (e.g., DRC-03 → DRC-03A → DRC-05 → DRC-07 closure)
                                                        - Verify if retrospective amendments or transition provisions apply
                                                        - Check for GSTN advisories on known portal issues

                                                        ═══════════════════════════════════════════════════════════════
                                                        QUALITY VALIDATION CHECKLIST (Before returning response)
                                                        ═══════════════════════════════════════════════════════════════
                                                        ✓ Legal citations complete with notification/section numbers?
                                                        ✓ Step-by-step resolution within current ticket framework (no "file new ticket")?
                                                        ✓ Escalation path clear without creating circular ticket requests?
                                                        ✓ Timelines realistic and specific (not vague "soon")?
                                                        ✓ Document checklist comprehensive for L2 escalation?
                                                        ✓ Root cause explained (not just symptoms)?
                                                        ✓ Portal navigation paths accurate per 2024-25 GST portal?
                                                        ✓ Tone professional yet accessible (jargon explained)?
                                                        ✓ Every factual claim cited?
                                                        ✓ Taxpayer knows exactly what to do next within THIS TICKET?
                                                        ✓ Confidence score justified and ≥95 OR escalation triggered with reason?
                                                        ✓ "comprehensive_resolution" field contains complete user-facing markdown response?

                                                        ═══════════════════════════════════════════════════════════════
                                                        MINIMUM CONFIDENCE RULE
                                                        ═══════════════════════════════════════════════════════════════
                                                        If overall_confidence < 95:
                                                        - Set the "resolution" field to null
                                                        - Set "reason_for_null" with detailed explanation
                                                        - Set requires_escalation to true
                                                        - The overall_confidence should still be set to the actual confidence score (less than 95)

                                                        Return ONLY the JSON object with this exact structure to match the ResolverOutput schema:
                                                        {{
                                                            "resolutions": [
                                                                {{
                                                                    "issue": "COMPREHENSIVE RESOLUTION FOR ALL ISSUES",
                                                                    "resolution": "Complete markdown-formatted response addressing all issues with ticket metadata, issue summary, root cause analysis, legal basis, immediate resolution steps, alternative solutions, required documentation, important notes, and next steps",
                                                                    "confidence": 95,
                                                                    "legal_basis": "Specific CGST/SGST/IGST sections, rules, notifications with dates and numbers",
                                                                    "source_citations": ["source1", "source2"],
                                                                    "reason_for_null": "Reason if resolution is null (only if confidence < 95)"
                                                                }}
                                                            ],
                                                            "overall_confidence": 95,
                                                            "requires_escalation": false
                                                        }}

                                                        The "resolution" field must contain the complete, markdown-formatted, user-facing response ready to send to the taxpayer, including all the detailed sections mentioned in the instructions above.
                                                        """)


            response = self.llm.invoke(prompt.format(
                query=state["user_query"],
                issues=[issue.issue_text for issue in preprocessing.core_issues],
                intent=preprocessing.detected_intent,
                category=classification.primary_category if classification else "general",
                context=context_text
            ))

            # Parse JSON response
            resolver_output = ResolverOutput(**json.loads(response.content))
            state["resolver_output"] = resolver_output

            logger.info(f"✅ Confidence: {resolver_output.overall_confidence}%")

            # Detailed resolver output
            logger.info(f"🎯 DETAILED RESOLVER OUTPUT ({resolver_model}):")
            logger.info(f"   Overall Confidence: {resolver_output.overall_confidence}%")
            logger.info(f"   Requires Escalation: {resolver_output.requires_escalation}")
            logger.info(f"   Resolution Type: Unified Comprehensive Resolution")

            if resolver_output.resolutions:
                for i, resolution in enumerate(resolver_output.resolutions, 1):
                    logger.info(f"   🔧 Unified Resolution {i}:")
                    logger.info(f"      Resolution Type: {resolution.issue}")
                    if resolution.resolution:
                        logger.info(f"      Unified Resolution: {resolution.resolution[:400]}...")
                    else:
                        logger.info(f"      Resolution: NULL (insufficient information)")
                        if resolution.reason_for_null:
                            logger.info(f"      Reason for Null: {resolution.reason_for_null}")

                    logger.info(f"      Confidence: {resolution.confidence}%")
                    if resolution.legal_basis:
                        logger.info(f"      Legal Basis: {resolution.legal_basis[:200]}...")
                    if resolution.source_citations:
                        logger.info(f"      Source Citations: {', '.join(resolution.source_citations[:3])}")
            else:
                logger.info("   🔧 No unified resolution generated")

            return state

        except Exception as e:
            logger.error(f"❌ Resolver error: {e}")
            state["errors"].append(str(e))

            # Set fallback resolver output
            state["resolver_output"] = ResolverOutput(
                resolutions=[], overall_confidence=0, requires_escalation=True
            )
            return state


class ResponseGenerationAgent:
    """Agent for generating final user response"""

    def process(self, state: AgentState) -> AgentState:
        """Generate final response for user"""
        try:
            logger.info("🔄 Agent 5: Generating response...")

            resolver = state.get("resolver_output")
            retrieval = state.get("retrieval_output")

            if not resolver:
                logger.error("❌ No resolver output available")
                state["errors"].append("No resolver output available")
                # Set default response
                state["final_response"] = FinalResponse(
                    direct_answer="I apologize, but I encountered an error while processing your query. Please try again.",
                    detailed_explanation=None,
                    legal_basis=None,
                    additional_resources=[],
                    confidence_score=0,
                    requires_manual_review=True
                )
                return state

            if not retrieval:
                logger.error("❌ No retrieval output available")
                state["errors"].append("No retrieval output available")
                # Set default response
                state["final_response"] = FinalResponse(
                    direct_answer="I apologize, but I couldn't retrieve relevant information for your query.",
                    detailed_explanation=None,
                    legal_basis=None,
                    additional_resources=[],
                    confidence_score=0,
                    requires_manual_review=True
                )
                return state

            # Build direct answer from resolutions - ALWAYS show available information
            parts = []
            escalation_notice = ""

            # Add escalation notice if required
            if resolver.requires_escalation:
                escalation_notice = "⚠️ **ESCALATION REQUIRED**: This case requires escalation to L2 support due to complexity. However, here is the preliminary analysis and guidance:\n\n"

            # Add unified resolution(s)
            for res in resolver.resolutions:
                # Check if this is a unified resolution
                if "COMPREHENSIVE RESOLUTION" in res.issue or "UNIFIED" in res.issue.upper():
                    resolution_section = f"**Comprehensive Resolution**:\n\n"
                else:
                    resolution_section = f"**Resolution**:\n\n"

                if res.resolution:
                    resolution_section += f"{res.resolution}\n\n"
                else:
                    if res.reason_for_null:
                        resolution_section += f"**Status**: Requires further investigation - {res.reason_for_null}\n\n"
                    else:
                        resolution_section += f"**Status**: Requires further investigation due to insufficient information.\n\n"

                # Add legal basis if available
                if res.legal_basis:
                    resolution_section += f"**Legal Basis**: {res.legal_basis}\n\n"

                # Add confidence score
                resolution_section += f"**Confidence**: {res.confidence}%\n"

                # Add source citations if available
                if res.source_citations:
                    resolution_section += f"\n**Sources**: {', '.join(res.source_citations[:3])}\n"

                parts.append(resolution_section)

            # Combine escalation notice with resolutions
            if parts:
                direct_answer = escalation_notice + "\n\n".join(parts)
            else:
                direct_answer = escalation_notice + "I apologize, but I don't have sufficient information to provide a preliminary analysis for your query."

            # Build additional resources
            additional_resources = []
            if retrieval.local_results:
                additional_resources.append("Knowledge base documentation")
            if retrieval.web_results:
                additional_resources.append("Official GST portals")
            if retrieval.twitter_results:
                additional_resources.append("Recent GSTN updates")

            # Create final response
            final_response = FinalResponse(
                direct_answer=direct_answer,
                detailed_explanation=None,  # Could be enhanced
                legal_basis=None,  # Could be extracted from resolver
                additional_resources=additional_resources,
                confidence_score=resolver.overall_confidence,
                requires_manual_review=resolver.requires_escalation
            )

            state["final_response"] = final_response

            # Detailed response generation output
            logger.info("💬 DETAILED RESPONSE GENERATION OUTPUT:")
            logger.info(f"   Direct Answer Length: {len(direct_answer)} characters")
            logger.info(f"   Requires Manual Review: {resolver.requires_escalation}")
            logger.info(f"   Confidence Score: {resolver.overall_confidence}%")
            logger.info(f"   Additional Resources: {len(additional_resources)}")
            if direct_answer:
                logger.info(f"   Response Preview: {direct_answer[:300]}...")

            logger.info("✅ Response generated successfully")
            return state

        except Exception as e:
            logger.error(f"❌ Response generation error: {e}")
            state["errors"].append(str(e))
            # Set default response on error
            state["final_response"] = FinalResponse(
                direct_answer="I apologize, but an error occurred while generating the response. Please try again.",
                detailed_explanation=None,
                legal_basis=None,
                additional_resources=[],
                confidence_score=0,
                requires_manual_review=True
            )
            return state


# Import retrieval agents at the bottom to avoid circular imports
from .retrieval_agents import (
    LocalRetrievalAgent,
    WebRetrievalAgent,
    TwitterRetrievalAgent,
    LLMReasoningAgent
)
