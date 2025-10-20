"""
Retrieval Agents for GST Grievance Resolution System
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Optional, Dict, Any

from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from openai import OpenAI

from ..models.schemas import (
    AgentState,
    RetrievalSource,
    RetrievalOutput,
    CoreIssue,
    ExtractedEntity
)
from ..config.settings import Config

logger = logging.getLogger(__name__)


class LocalRetrievalAgent:
    """
    PRODUCTION: Load pre-built knowledge base with graph support
    Handles large-scale PDF ingestion output (20K+ chunks)
    """

    def __init__(self, embeddings=None, kb_folder: str = "./", enable_graph: bool = True):
        """
        Initialize with pre-built knowledge base

        Args:
            embeddings: Pre-initialized HuggingFace embeddings
            kb_folder: Path to knowledge base folder
            enable_graph: Enable knowledge graph integration
        """
        self.embeddings = embeddings
        self.kb_folder = kb_folder
        self.enable_graph = enable_graph
        self.vector_store = None
        self.graph_retriever = None
        self.kb_metadata = {}

        if not embeddings:
            logger.error("❌ No local embeddings provided!")
            return

        # Load pre-built knowledge base
        self._load_knowledge_base()

        # Load knowledge graph if enabled
        if self.enable_graph:
            self._load_knowledge_graph()

    def _load_knowledge_base(self):
        """Load pre-processed knowledge base from disk"""
        kb_path = Path(self.kb_folder)
        faiss_path = kb_path / "faiss_index"
        metadata_path = kb_path / "kb_metadata.json"

        if not faiss_path.exists():
            logger.error(f"❌ No processed knowledge base found at {faiss_path}")
            logger.info("💡 Expected structure:")
            logger.info("   ./faiss_index/ - FAISS vector store")
            logger.info("   ./kb_metadata.json - Metadata")
            logger.info("   ./knowledge_graph.db - Graph database")
            logger.info("\n💡 Run your PDF ingestion pipeline first!")
            return

        try:
            logger.info(f"🔄 Loading knowledge base from {self.kb_folder}")

            # Load FAISS index
            self.vector_store = FAISS.load_local(
                str(faiss_path),
                self.embeddings,
                allow_dangerous_deserialization=True
            )

            # Load metadata
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    self.kb_metadata = json.load(f)

            # Log stats
            total_docs = self.kb_metadata.get('total_files', self.kb_metadata.get('total_pdfs', 'Unknown'))
            total_chunks = self.kb_metadata.get('total_chunks', 'Unknown')
            embedding_model = self.kb_metadata.get('embedding_model', 'Unknown')

            logger.info(f"✅ Loaded knowledge base:")
            logger.info(f"   📄 Documents: {total_docs}")
            logger.info(f"   📊 Chunks: {total_chunks}")
            logger.info(f"   🧠 Model: {embedding_model}")
            logger.info(f"   💾 Size: {self._get_index_size():.2f} MB")

        except Exception as e:
            logger.error(f"❌ Failed to load knowledge base: {e}")
            logger.error(f"   Check that embedding model matches: {Config.LOCAL_EMBEDDING_MODEL}")
            self.vector_store = None

    def _load_knowledge_graph(self):
        """Load knowledge graph for relationship-based retrieval"""
        graph_path = Path(self.kb_folder) / "knowledge_graph.db"

        if not graph_path.exists():
            logger.warning(f"⚠️ Knowledge graph not found at {graph_path}")
            logger.info("   Graph-enhanced retrieval disabled")
            return

        try:
            # Import graph retriever
            from ..utils.knowledge_graph import LightweightKnowledgeGraph

            self.graph_retriever = LightweightKnowledgeGraph(db_path=str(graph_path))
            self.graph_retriever.load()
            logger.info(f"✅ Loaded knowledge graph:")
            logger.info(f"   🕸️ Nodes: {self.graph_retriever.graph.number_of_nodes()}")
            logger.info(f"   🔗 Edges: {self.graph_retriever.graph.number_of_edges()}")

        except Exception as e:
            logger.warning("⚠️ Knowledge graph module not found. Skipping graph loading.")
            logger.error(f"❌ Failed to load knowledge graph: {e}")
            self.graph_retriever = None

    def _get_index_size(self) -> float:
        """Calculate total size of knowledge base in MB"""
        if not Path(self.kb_folder).exists():
            return 0.0
        total_bytes = sum(f.stat().st_size for f in Path(self.kb_folder).rglob('*') if f.is_file())
        return total_bytes / (1024 * 1024)

    def retrieve(self, query: str, k: int = 5, filter_category: Optional[str] = None,
                 use_graph: bool = True) -> List[RetrievalSource]:
        """
        Retrieve relevant chunks using hybrid vector + graph search

        Args:
            query: Search query
            k: Number of results to return
            filter_category: Optional category filter
            use_graph: Enable knowledge graph enhancement

        Returns:
            List of retrieval sources with relevance scores
        """
        if not self.vector_store:
            logger.warning("⚠️ Vector store not available")
            return []

        try:
            # --- PHASE 1: VECTOR SEARCH ---
            # Fetch more than k for filtering and re-ranking
            fetch_k = k * 3 if use_graph and self.graph_retriever else k * 2

            docs = self.vector_store.similarity_search_with_score(query, k=fetch_k)

            vector_results = []
            for doc, score in docs:
                # Apply category filter if specified
                if filter_category and doc.metadata.get('category') != filter_category:
                    continue

                # Build citation from metadata
                filename = doc.metadata.get('filename', doc.metadata.get('source', 'Unknown'))
                page = doc.metadata.get('page', '')
                citation = f"{filename}"
                if page:
                    citation += f", p{page}"

                vector_results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': score,
                    'citation': citation
                })

            # --- PHASE 2: GRAPH ENHANCEMENT (Optional) ---
            if use_graph and self.graph_retriever:
                vector_results = self._apply_graph_boost(query, vector_results)

            # --- PHASE 3: RANK, FILTER AND FORMAT ---
            vector_results.sort(key=lambda x: x['score'])

            # Apply relevance score filter - only include results with score < 0.15 (equivalent to > 0.85 similarity)
            # In FAISS, lower scores mean higher similarity, so we filter out results with poor similarity
            initial_count = len(vector_results)
            vector_results = [result for result in vector_results if result['score'] < 0.15]
            filtered_count = len(vector_results)

            # Limit to k results after filtering
            vector_results = vector_results[:k]

            # Format results
            results = []
            for result in vector_results:
                results.append(RetrievalSource(
                    source_type="local_knowledge_base",
                    content=result['content'],
                    citation=result['citation'],
                    relevance_score=float(result['score']),
                    date=result['metadata'].get('date')
                ))

            logger.info(f"   📖 Retrieved {len(results)} chunks from knowledge base")
            logger.info(f"      🎯 Relevance filter applied: {filtered_count}/{initial_count} passed threshold (score < 0.15)")
            if use_graph and self.graph_retriever:
                logger.info(f"      🕸️ Graph-enhanced retrieval active")

            # Detailed local retrieval output
            logger.info("📚 DETAILED LOCAL RETRIEVAL OUTPUT:")
            for i, result in enumerate(results, 1):
                logger.info(f"   📄 Chunk {i}:")
                logger.info(f"      Source: {result.citation}")
                logger.info(f"      Relevance Score: {result.relevance_score:.4f}")
                logger.info(f"      Content Preview: {result.content[:200]}...")
                if result.date:
                    logger.info(f"      Date: {result.date}")

            return results

        except Exception as e:
            logger.error(f"❌ Retrieval error: {e}")
            return []

    def _apply_graph_boost(self, query: str, vector_results: List[Dict]) -> List[Dict]:
        """Apply knowledge graph boost to vector search results"""
        try:
            # Extract entities from query for graph search
            entities = self._extract_entities(query)
            related_entities = []

            for entity in entities:
                related = self.graph_retriever.find_related(entity, max_depth=2, max_results=5)
                related_entities.extend(related)

            if not related_entities:
                return vector_results

            # Boost scores for documents containing related entities
            boosted_results = []
            for result in vector_results:
                content = result['content'].lower()
                boost = 0

                for related in related_entities:
                    entity_name = related['entity'].lower()
                    weight = related['weight']

                    if entity_name in content:
                        boost += weight * 0.1  # Boost by 10% of weight

                result['score'] = result['score'] - boost  # Lower is better in FAISS
                boosted_results.append(result)

            logger.info(f"      🎯 Graph boost applied ({len(related_entities)} related entities)")
            return boosted_results

        except Exception as e:
            logger.warning(f"⚠️ Graph boost failed: {e}")
            return vector_results

    def _extract_entities(self, text: str) -> List[str]:
        """Simple entity extraction for graph search"""
        # Look for GST-related terms
        gst_terms = re.findall(r'\b(GST|GSTIN|GSTR-[0-9]+|GSTN|CBIC)\b', text.upper())
        return list(set(gst_terms))

    def get_stats(self) -> dict:
        """Get knowledge base statistics"""
        stats = {
            'source_files': self.kb_metadata.get('total_files', 0),
            'document_count': self.kb_metadata.get('total_chunks', 0),
            'index_size_mb': self._get_index_size(),
            'graph_nodes': 0,
            'graph_edges': 0
        }

        if self.graph_retriever:
            graph_stats = self.graph_retriever.get_stats()
            stats['graph_nodes'] = graph_stats['nodes']
            stats['graph_edges'] = graph_stats['edges']

        return stats

    def search_with_graph(self, entity: str, max_related: int = 10) -> List[str]:
        """Search for related entities using knowledge graph"""
        if not self.graph_retriever:
            logger.warning("⚠️ Knowledge graph not loaded")
            return []

        try:
            related = self.graph_retriever.find_related(entity, max_results=max_related)
            return [r['entity'] for r in related]
        except Exception as e:
            logger.error(f"❌ Graph search error: {e}")
            return []


class WebRetrievalAgent:
    """Web search agent using Tavily or DuckDuckGo"""

    def __init__(self, provider: str = "auto", unrestricted: bool = True, llm=None):
        """
        Initialize web search agent

        Args:
            provider: "tavily", "duckduckgo", or "auto"
            unrestricted: Enable unrestricted web search
            llm: Optional LLM for query optimization (will use centralized config if None)
        """
        self.provider = self._auto_detect_provider() if provider == "auto" else provider
        self.unrestricted = unrestricted
        # Use provided LLM or get from centralized config
        self.llm = llm if llm is not None else Config.get_web_query_llm()
        self.client = None

        self._initialize_provider()

    def _auto_detect_provider(self) -> str:
        """Auto-detect best available search provider"""
        try:
            from tavily import TavilyClient
            if Config.TAVILY_API_KEY:
                logger.info("✅ Tavily API key found, using Tavily")
                return "tavily"
        except ImportError:
            pass

        try:
            from langchain_community.tools import DuckDuckGoSearchRun
            logger.info("✅ Using DuckDuckGo (free, no API key)")
            return "duckduckgo"
        except ImportError:
            pass

        logger.warning("⚠️ No search provider available - install tavily-python or duckduckgo-search")
        return "none"

    def _initialize_provider(self):
        """Initialize the selected search provider"""
        if self.provider == "tavily":
            self._initialize_tavily()
        elif self.provider == "duckduckgo":
            self._initialize_duckduckgo()

    def _initialize_tavily(self):
        """Initialize Tavily client"""
        try:
            from tavily import TavilyClient
            self.client = TavilyClient(api_key=Config.TAVILY_API_KEY)
            logger.info("✅ Tavily client initialized")
            if self.unrestricted:
                logger.info("🌐 Unrestricted web search enabled (no domain filtering)")
        except Exception as e:
            logger.error(f"❌ Web search client initialization failed: {e}")
            logger.info("💡 Check web search API key in .env file. Refer to src/config/settings.py for details.")
            self.client = None

    def _initialize_duckduckgo(self):
        """Initialize DuckDuckGo search"""
        try:
            from langchain_community.tools import DuckDuckGoSearchRun
            from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
            self.client = DuckDuckGoSearchRun()
            logger.info("✅ DuckDuckGo search initialized")
            if self.unrestricted:
                logger.info("🌐 Unrestricted web search enabled (general internet search)")
        except Exception as e:
            logger.error(f"❌ DuckDuckGo initialization failed: {e}")
            logger.info("💡 Install with: pip install duckduckgo-search")
            self.client = None

    def retrieve(self, query: str, category: str = None,
                 keywords: List[str] = None, max_results: int = 10) -> List[RetrievalSource]:
        """
        Retrieve web search results

        Args:
            query: Search query
            category: Optional category for focused search
            keywords: Optional keywords for search enhancement
            max_results: Maximum number of results

        Returns:
            List of web search results
        """
        if not self.client:
            logger.warning("⚠️ No search provider available")
            return []

        # Build enhanced query using sophisticated logic
        if self.provider == "tavily":
            enhanced_query = self._build_focused_query_tavily(query, category, keywords)
        else:
            # Use LLM to optimize query if available
            if self.llm:
                enhanced_query = self._build_focused_query_with_llm(query, category)
            else:
                enhanced_query = self._build_focused_query_regex(query, category, keywords)

        # Execute search
        if self.provider == "tavily":
            return self.retrieve_tavily(enhanced_query, max_results)

        return []

    def _extract_key_terms(self, text: str, max_terms: int = 5) -> List[str]:
        """Extract key terms from text using regex"""
        # Simple keyword extraction - can be enhanced
        terms = re.findall(r'\b[A-Z]{2,}\b|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        return list(set(terms[:max_terms]))

    def _extract_key_terms(self, text: str, max_terms: int = 5) -> List[str]:
        """
        Extract key terms from text using regex (fallback method)

        Priority:
        1. GST form numbers (GSTR-4, GSTR-3A, etc.)
        2. Notification numbers
        3. Important keywords
        4. Financial years
        """
        import re

        key_terms = []

        # 1. GST Forms (highest priority)
        forms = re.findall(r'GSTR-?\d+[A-Z]?', text, re.IGNORECASE)
        key_terms.extend(forms[:3])

        # 2. Notification numbers
        notifications = re.findall(r'Notification\s+(?:No\.?\s*)?\d+/\d{4}', text, re.IGNORECASE)
        key_terms.extend(notifications[:2])

        # 3. Important keywords
        important_keywords = [
            'late fee', 'penalty', 'notice', 'filing', 'refund',
            'portal error', 'ITC', 'composition', 'registration', 'mismatch'
        ]
        text_lower = text.lower()
        for keyword in important_keywords:
            if keyword in text_lower and len(key_terms) < max_terms:
                key_terms.append(keyword)

        # 4. Financial years
        if len(key_terms) < max_terms:
            fys = re.findall(r'FY\s*\d{4}-?\d{2,4}', text, re.IGNORECASE)
            key_terms.extend(fys[:1])

        return key_terms[:max_terms]

    def _build_focused_query_with_llm(self, query: str, category: str = None) -> str:
        """
        Use classifier LLM to extract focused search query from long text
        Reuses existing classifier_llm - no additional model initialization
        """
        if not self.llm:
            logger.info("   ℹ️ No LLM provided, using regex extraction")
            return self._build_focused_query_regex(query, category, None)

        try:
            prompt = f"""Extract a concise web search query (max 30 words) from this GST grievance:

Query: {query[:800]}

Focus on:
- GST form numbers (GSTR-4, GSTR-3A, etc.)
- Key issues (late fee, filing, penalty, notice, error)
- Notification/section numbers
- Important entities only

Return ONLY the search query, nothing else. No explanations."""

            response = self.llm.invoke(prompt)
            focused_query = response.content.strip()[:350]

            logger.info(f"   🤖 LLM-optimized query ({len(focused_query)} chars): {focused_query[:80]}...")
            return focused_query

        except Exception as e:
            logger.warning(f"⚠️ LLM query generation failed: {e}, using regex fallback")
            return self._build_focused_query_regex(query, category, None)

    def _build_focused_query_regex(self, query: str, category: str = None,
                                    keywords: List[str] = None, max_length: int = 350) -> str:
        """
        Build a focused query using regex extraction (fallback method)
        """
        # Extract key terms
        if keywords:
            query_parts = keywords[:5]
        else:
            query_parts = self._extract_key_terms(query, max_terms=5)

        # Add category context if available
        if category and not self.unrestricted:
            category_context = {
                "gstr_filing": "GST return filing",
                "penalty_notice": "GST penalty late fee notice",
                "refund": "GST refund process",
                "registration": "GST registration",
                "itc_mismatch": "GST ITC mismatch",
                "eway_bill": "GST e-way bill",
                "portal_error": "GST portal error"
            }
            context = category_context.get(category, "GST")
            query_parts.insert(0, context)

        # Build query
        focused_query = " ".join(query_parts)

        # Truncate if still too long
        if len(focused_query) > max_length:
            focused_query = focused_query[:max_length].rsplit(' ', 1)[0]

        logger.info(f"   🔍 Regex-extracted query ({len(focused_query)} chars): {focused_query[:80]}...")
        return focused_query

    def _build_focused_query_tavily(self, query: str, category: str = None,
                                     keywords: List[str] = None) -> str:
        """
        Build query for Tavily with 400-char limit
        Strategy: Use LLM if available, else fall back to regex
        """
        # Try LLM-based extraction first (preferred)
        if self.llm:
            return self._build_focused_query_with_llm(query, category)

        # Fall back to regex extraction
        return self._build_focused_query_regex(query, category, keywords)

    def retrieve_tavily(self, query: str, max_results: int = 10) -> List[RetrievalSource]:
        """Retrieve results using Tavily API"""
        try:
            # Query should already be optimized for length by _build_focused_query_tavily
            # But add safety check as last resort
            if len(query) > 400:
                query = query[:397] + "..."
                logger.info(f"   ⚠️ Emergency truncation to {len(query)} characters for Tavily API")

            # Search with Tavily
            response = self.client.search(
                query=query,
                search_depth="advanced",
                include_answer=False,
                include_raw_content=False,
                max_results=max_results
            )

            # Filter results by relevance score > 0.5
            all_results = response.get('results', [])
            filtered_results = [result for result in all_results if result.get('score', 0.0) > 0.5]

            results = []
            for result in filtered_results:
                results.append(RetrievalSource(
                    source_type="web_search",
                    content=result.get('content', ''),
                    citation=result.get('url', ''),
                    relevance_score=result.get('score', 0.0),
                    date=result.get('published_date')
                ))

            logger.info(f"   🌐 Retrieved {len(results)} results from Tavily (filtered from {len(all_results)} total results)")
            logger.info(f"   🎯 Applied relevance filter: score > 0.5")

            # Detailed web search output
            logger.info("🌐 DETAILED WEB SEARCH OUTPUT:")
            for i, result in enumerate(results, 1):
                logger.info(f"   🔗 Web Result {i}:")
                logger.info(f"      URL: {result.citation}")
                logger.info(f"      Relevance Score: {result.relevance_score:.4f}")
                logger.info(f"      Content Preview: {result.content[:300]}...")
                if result.date:
                    logger.info(f"      Published Date: {result.date}")

            return results

        except Exception as e:
            logger.error(f"❌ Tavily search error: {e}")
            return []


class TwitterRetrievalAgent:
    """Twitter retrieval agent for real-time GST updates"""

    def __init__(self):
        self.bearer_token = Config.TWITTER_BEARER_TOKEN
        self.client = None

        if self.bearer_token:
            try:
                import tweepy
                self.client = tweepy.Client(bearer_token=self.bearer_token)
                logger.info("✅ Twitter API client initialized")
            except Exception as e:
                logger.warning(f"⚠️ Twitter API initialization failed: {e}")
        else:
            logger.warning("⚠️ Twitter API not configured. Check Twitter API key in .env file.")

    def retrieve(self, keywords: List[str], max_results: int = 10) -> List[RetrievalSource]:
        """Retrieve tweets relevant to GST keywords"""
        if not self.client:
            logger.warning("⚠️ Twitter client not available")
            return []

        try:
            # Build query for GSTN Twitter handle + keywords
            # Fix: Use exact phrase matching to avoid ambiguous "and" keyword issues
            if not keywords:
                query = f"from:{Config.GSTN_TWITTER.replace('@', '')}"
            else:
                # Use quoted phrases to avoid boolean operator conflicts
                quoted_keywords = [f'"{keyword}"' for keyword in keywords]
                query = f"from:{Config.GSTN_TWITTER.replace('@', '')} ({' OR '.join(quoted_keywords)})"
            logger.info(f"   🐦 Twitter query: {query}")

            # Search tweets with better error handling
            response = self.client.search_recent_tweets(
                query=query,
                tweet_fields=["created_at", "public_metrics", "author_id"],
                max_results=min(max_results, 10)  # Twitter API limit
            )

            results = []
            if response and hasattr(response, 'data') and response.data:
                for tweet in response.data:
                    # Validate tweet data
                    if hasattr(tweet, 'text') and hasattr(tweet, 'created_at'):
                        # Get engagement metrics safely
                        engagement = 0
                        if hasattr(tweet, 'public_metrics') and tweet.public_metrics:
                            engagement = tweet.public_metrics.get('like_count', 0)

                        results.append(RetrievalSource(
                            source_type="twitter",
                            content=tweet.text,
                            citation=f"@{Config.GSTN_TWITTER} - {tweet.created_at}",
                            relevance_score=min(engagement / 100.0, 1.0),  # Cap at 1.0
                            date=tweet.created_at.isoformat() if hasattr(tweet.created_at, 'isoformat') else str(tweet.created_at)
                        ))

            logger.info(f"   📱 Retrieved {len(results)} tweets")

            # Detailed Twitter output
            if results:
                logger.info("📱 DETAILED TWITTER OUTPUT:")
                for i, result in enumerate(results, 1):
                    logger.info(f"   🐦 Tweet {i}:")
                    logger.info(f"      Source: {result.citation}")
                    logger.info(f"      Engagement Score: {result.relevance_score:.4f}")
                    logger.info(f"      Content: {result.content[:280]}...")
                    if result.date:
                        logger.info(f"      Tweet Date: {result.date}")
            else:
                logger.info("📱 TWITTER OUTPUT: No relevant tweets found")

            return results

        except Exception as e:
            logger.error(f"❌ Twitter error: {e}")
            # Return empty list gracefully instead of failing
            return []


class LLMReasoningAgent:
    """LLM reasoning agent for complex query analysis"""

    def __init__(self):
        # Use centralized LLM from config
        self.client = Config.get_reasoning_llm()

        if self.client:
            logger.info("✅ LLM Reasoning agent initialized with centralized config")
        else:
            logger.warning("⚠️ Reasoning LLM not available. Check reasoning agent API key in .env file.")
            logger.warning("   Refer to src/config/settings.py for configuration details.")

    def retrieve(self, core_issues: List[CoreIssue], entities: List[ExtractedEntity]) -> List[RetrievalSource]:
        """Use LLM reasoning to generate additional insights"""
        if not self.client:
            logger.warning("⚠️ Reasoning LLM client not available. Skipping LLM reasoning.")
            return []

        if not core_issues:
            return []

        try:
            entity_context = self._build_entity_context(entities)

            logger.info(f"   🤖 Querying reasoning LLM for all {len(core_issues)} issues in single API call...")

            # Build concatenated prompt with all issues
            system_prompt = self._get_system_prompt()
            concatenated_prompt = self._build_concatenated_prompt(core_issues, entity_context)

            # Create unified prompt for all LLM providers
            full_prompt = f"{system_prompt}\n\n{concatenated_prompt}"

            # Use unified invoke method that works with all LLM providers
            response = self.client.invoke(full_prompt)

            if not response:
                logger.warning("⚠️ No response from reasoning LLM API")
                return []

            combined_reasoning = response.content.strip()

            # Split the combined response into individual issue analyses
            individual_analyses = self._split_combined_analysis(combined_reasoning, len(core_issues))

            results = []
            for idx, analysis in enumerate(individual_analyses):
                if analysis.strip() and idx < len(core_issues):  # Only add non-empty analyses
                    # Detailed LLM reasoning output for this issue
                    logger.info(f"   🧠 DETAILED LLM REASONING - Issue {idx+1}:")
                    logger.info(f"      Issue: {core_issues[idx].issue_text}")
                    logger.info(f"      Keywords: {', '.join(core_issues[idx].keywords)}")
                    logger.info(f"      Priority: {core_issues[idx].priority}")
                    logger.info(f"      Reasoning: {analysis[:500]}...")

                    # Clean up analysis content - remove excessive markdown formatting
                    cleaned_analysis = analysis.strip()
                    # Remove leading markdown formatting that might interfere with display
                    if cleaned_analysis.startswith('**'):
                        cleaned_analysis = cleaned_analysis[2:].lstrip()
                    if cleaned_analysis.endswith('**'):
                        cleaned_analysis = cleaned_analysis[:-2].rstrip()

                    # Format content properly
                    content_parts = [
                        f"**Core Issue {idx+1}**: {core_issues[idx].issue_text}",
                        f"**Priority**: {core_issues[idx].priority}",
                        f"**Keywords**: {', '.join(core_issues[idx].keywords)}",
                        "",
                        "**LLM Analysis:**",
                        cleaned_analysis
                    ]

                    formatted_content = "\n".join(content_parts)

                    results.append(RetrievalSource(
                        source_type="llm_reasoning",
                        content=formatted_content,
                        citation=f"Reasoning LLM Analysis - Issue {idx+1}",
                        relevance_score=0.8,
                        date=None
                    ))

            # If we couldn't split properly, add the combined response as a single result
            if len(results) == 0 and combined_reasoning.strip():
                logger.info(f"   🧠 DETAILED LLM REASONING - Combined Analysis:")
                logger.info(f"      Combined Reasoning: {combined_reasoning[:500]}...")

                # Clean up combined reasoning - remove excessive markdown formatting
                cleaned_combined = combined_reasoning.strip()
                if cleaned_combined.startswith('**'):
                    cleaned_combined = cleaned_combined[2:].lstrip()
                if cleaned_combined.endswith('**'):
                    cleaned_combined = cleaned_combined[:-2].rstrip()

                # Add core issues to combined analysis
                core_issues_parts = []
                for idx, issue in enumerate(core_issues):
                    core_issues_parts.extend([
                        f"**Core Issue {idx+1}**: {issue.issue_text}",
                        f"**Priority**: {issue.priority}",
                        f"**Keywords**: {', '.join(issue.keywords)}",
                        ""
                    ])

                combined_parts = core_issues_parts + [
                    "**Combined LLM Analysis:**",
                    cleaned_combined
                ]

                combined_content = "\n".join(combined_parts)

                results.append(RetrievalSource(
                    source_type="llm_reasoning",
                    content=combined_content,
                    citation="Reasoning LLM Analysis - Combined",
                    relevance_score=0.8,
                    date=None
                ))

            logger.info(f"   🤖 Retrieved {len(results)} LLM reasoning results from single API call")
            return results

        except Exception as e:
            logger.error(f"❌ LLM reasoning retrieval error: {e}")
            return []

    def _get_system_prompt(self) -> str:
        """Get system prompt for LLM reasoning"""
        return """
        You are a GST expert providing reasoning and insights for complex GST issues.
        Focus on:
        1. Root cause analysis
        2. Regulatory references
        3. Practical solutions
        4. Prevention strategies
        5. Related compliance requirements

        Be thorough but concise. Provide actionable insights based on GST laws and procedures.
        """

    def _build_entity_context(self, entities: List[ExtractedEntity]) -> str:
        """Build context string from extracted entities"""
        if not entities:
            return "No specific entities identified."

        context_parts = []
        for entity in entities:
            context_parts.append(f"{entity.entity_type}: {entity.value}")
            if entity.context:
                context_parts.append(f"  Context: {entity.context}")

        return "\n".join(context_parts)

    def _build_concatenated_prompt(self, core_issues: List[CoreIssue], entity_context: str) -> str:
        """Build concatenated prompt for analyzing all issues at once"""
        prompt_parts = [
            f"Analyze {len(core_issues)} GST issues and provide expert reasoning for each:",
            "",
            "ENTITY CONTEXT:",
            entity_context,
            ""
        ]

        for idx, issue in enumerate(core_issues, 1):
            prompt_parts.extend([
                f"ISSUE #{idx}:",
                f"Issue: {issue.issue_text}",
                f"Keywords: {', '.join(issue.keywords)}",
                f"Priority: {issue.priority}",
                ""
            ])

        prompt_parts.extend([
            "Please provide comprehensive analysis for EACH issue above in order, including:",
            "1. Root cause analysis",
            "2. Regulatory implications",
            "3. Recommended solutions",
            "4. Preventive measures",
            "",
            "Format your response with clear separation for each issue (e.g., 'Issue #1 Analysis:', 'Issue #2 Analysis:', etc.)."
        ])

        return "\n".join(prompt_parts)

    def _split_combined_analysis(self, combined_text: str, expected_issues: int) -> List[str]:
        """
        Split combined analysis text into individual issue analyses

        Args:
            combined_text: Combined analysis from LLM
            expected_issues: Expected number of individual analyses

        Returns:
            List of individual analyses
        """
        import re

        # Clean up the combined text first - remove excessive markdown formatting
        cleaned_text = combined_text.strip()

        # Try different splitting patterns to match actual LLM output format
        patterns = [
            r'Issue\s*#\d+\s*:',                                  # "Issue #1:" pattern (primary)
            r'Issue\s*#\d+\s*Analysis:',                          # "Issue #1 Analysis:" pattern (secondary)
            r'Analysis\s+for\s+Issue\s*#\d+',                    # "Analysis for Issue #1" pattern
            r'\n\n\d+\.\s',                                       # "1. " pattern with double newline
            r'Issue\s+\d+\s*:',                                  # "Issue 1:" pattern
            r'I\s*\d+[:.]',                                       # "I 1:" or "I 1." pattern
            r'\n\n•\s',                                           # Bullet points (fallback)
            r'\n\n-\s',                                           # Dash points (fallback)
            r'\n\n'                                               # Double newlines as last resort
        ]

        for pattern in patterns:
            parts = []
            if pattern == r'\n\n':  # Special case for double newlines
                parts = [p.strip() for p in cleaned_text.split('\n\n') if p.strip()]
            else:
                parts = [p.strip() for p in re.split(pattern, cleaned_text, flags=re.IGNORECASE) if p.strip()]

            # Filter out parts that are too short (likely formatting artifacts)
            filtered_parts = [p for p in parts if len(p) > 50]  # Keep only substantial content

            if len(filtered_parts) >= expected_issues:
                logger.info(f"   🤖 Successfully split combined analysis using pattern: {pattern}")
                return filtered_parts[:expected_issues]  # Take only expected number of parts

        # If no pattern works well, try to split by markdown headers
        logger.warning(f"   ⚠️ Standard patterns failed, trying markdown header splitting")
        header_patterns = [
            r'^\*\*[^*]+\*\*',          # "**Header**" pattern
            r'^#+\s*\w+',               # "# Header" pattern
        ]

        for header_pattern in header_patterns:
            parts = []
            lines = cleaned_text.split('\n')
            current_part = []

            for line in lines:
                if re.match(header_pattern, line.strip()) and current_part:
                    # Found a new header, save previous part
                    content = '\n'.join(current_part).strip()
                    if len(content) > 50:
                        parts.append(content)
                    current_part = [line.strip()]
                else:
                    current_part.append(line.strip())

            # Add the last part
            if current_part:
                content = '\n'.join(current_part).strip()
                if len(content) > 50:
                    parts.append(content)

            if len(parts) >= expected_issues:
                logger.info(f"   🤖 Successfully split using markdown header pattern: {header_pattern}")
                return parts[:expected_issues]

        # If all else fails, split by equal portions
        logger.warning(f"   ⚠️ Could not split combined analysis cleanly, dividing by equal portions")
        chunk_size = max(300, len(cleaned_text) // expected_issues)  # Minimum 300 chars per issue
        chunks = []
        for i in range(0, len(cleaned_text), chunk_size):
            chunk = cleaned_text[i:i+chunk_size].strip()
            if chunk:
                chunks.append(chunk)
        return chunks[:expected_issues]

    def _build_issue_prompt(self, issue: CoreIssue, entity_context: str) -> str:
        """Build prompt for analyzing specific issue (legacy method for compatibility)"""
        return f"""
        Analyze this GST issue and provide expert reasoning:

        ISSUE: {issue.issue_text}
        KEYWORDS: {', '.join(issue.keywords)}
        PRIORITY: {issue.priority}

        ENTITY CONTEXT:
        {entity_context}

        Please provide:
        1. Root cause analysis
        2. Regulatory implications
        3. Recommended solutions
        4. Preventive measures
        """