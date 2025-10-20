"""
Embeddings and LLM initialization utilities
"""

import os
import logging
from typing import Optional

import torch
from openai import OpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
# Lazy imports to avoid tokenizer fork issues - load only when needed
# These will be imported inside functions after any potential forking
# from langchain_community.embeddings import HuggingFaceEmbeddings

from ..config.settings import Config

logger = logging.getLogger(__name__)


def initialize_local_embeddings() -> Optional["HuggingFaceEmbeddings"]:
    """Initialize local embedding model - NO API CALLS"""
    try:
        logger.info("🔄 Initializing local embedding model...")
        logger.info(f"📦 Model: {Config.LOCAL_EMBEDDING_MODEL}")
        logger.info(f"💻 Device: {Config.EMBEDDING_DEVICE}")

        # MPS-specific handling
        if Config.EMBEDDING_DEVICE == "mps":
            logger.info("🍎 MPS fallback enabled for unsupported operations")

        # Lazy imports to avoid tokenizer fork issues
        from langchain_community.embeddings import HuggingFaceEmbeddings

        # Initialize HuggingFace embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name=Config.LOCAL_EMBEDDING_MODEL,
            model_kwargs={'device': Config.EMBEDDING_DEVICE},
            encode_kwargs={'normalize_embeddings': True}
        )

        logger.info(f"✅ Local embedding model loaded successfully")
        logger.info(f"🎯 No API calls - fully offline embeddings")
        return embeddings

    except Exception as e:
        logger.error(f"❌ Failed to initialize local embeddings: {e}")
        raise


def initialize_llms() -> tuple[ChatGoogleGenerativeAI, ChatGoogleGenerativeAI, ChatGoogleGenerativeAI]:
    """Initialize LLM instances using centralized config"""

    preprocessor_llm = Config.get_preprocessor_llm()
    classifier_llm = Config.get_classifier_llm()
    resolver_llm = Config.get_resolver_llm()

    logger.info(f"✅ LLMs retrieved from centralized config:")
    logger.info(f"   Preprocessor: {Config.PREPROCESSOR_MODEL}")
    logger.info(f"   Classifier: {Config.CLASSIFIER_MODEL}")
    logger.info(f"   Resolver: {Config.RESOLVER_MODEL}")

    return preprocessor_llm, classifier_llm, resolver_llm


def test_embeddings(embeddings) -> bool:
    """Test embedding functionality"""
    try:
        test_embedding = embeddings.embed_query("Test query for GST portal")
        logger.info(f"✅ Embedding test successful! Dimension: {len(test_embedding)}")
        return True
    except Exception as e:
        logger.error(f"❌ Embedding test failed: {e}")
        return False


# Initialize global embeddings instance
local_embeddings = None
preprocessor_llm = None
classifier_llm = None
resolver_llm = None


def initialize_all():
    """Initialize all models and embeddings using centralized config"""
    global local_embeddings, preprocessor_llm, classifier_llm, resolver_llm

    try:
        # Initialize embeddings
        local_embeddings = initialize_local_embeddings()
        if not test_embeddings(local_embeddings):
            raise Exception("Embedding test failed")

        # Initialize LLMs using centralized config
        preprocessor_llm, classifier_llm, resolver_llm = initialize_llms()

        # Verify all LLMs are available
        if not all([preprocessor_llm, classifier_llm, resolver_llm]):
            raise Exception("One or more LLMs failed to initialize")

        logger.info("✅ All models initialized successfully using centralized config")
        return True

    except Exception as e:
        logger.error(f"❌ Model initialization failed: {e}")
        local_embeddings = None
        preprocessor_llm = None
        classifier_llm = None
        resolver_llm = None
        return False