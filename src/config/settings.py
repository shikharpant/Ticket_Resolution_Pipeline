"""
Configuration settings for GST Grievance Resolution System
"""

import os
import torch
import logging
import traceback
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# LLM imports - will be initialized lazily
from langchain_google_genai import ChatGoogleGenerativeAI
from openai import OpenAI

# Optional imports for additional providers
try:
    from langchain_openai import ChatOpenAI
    HAS_LANGCHAIN_OPENAI = True
except ImportError:
    HAS_LANGCHAIN_OPENAI = False

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False


class OpenAIWrapper:
    """
    Wrapper for OpenAI-compatible APIs to provide LangChain-like interface
    Implements lazy loading - client created only on first invoke()
    """
    call_count = 0  # Temporary instrumentation counter

    def __init__(self, model_name: str, api_key: str, base_url: str = None, **kwargs):
        self.model_name = model_name
        self.api_key = api_key
        self.base_url = base_url
        self.kwargs = kwargs
        self.client = None  # Lazy loading - don't create client until needed

    def _get_client(self):
        """Create client only when first needed"""
        if self.client is None:
            logger.debug(f"🔄 Creating LLM client for {self.model_name}")
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                **self.kwargs
            )

    def invoke(self, prompt: str, **kwargs):
        """
        LangChain-compatible invoke method
        """
        try:
            # Create client only on first use
            self._get_client()

            # Temporary instrumentation: log each LLM call with call site
            OpenAIWrapper.call_count += 1
            stack = traceback.extract_stack(limit=3)
            caller_frame = stack[-2] if len(stack) >= 2 else stack[-1]
            caller_details = f"{Path(caller_frame.filename).name}:{caller_frame.lineno} ({caller_frame.name})"
            logger.info(
                "🧪 LLM call #%d via %s using model %s",
                OpenAIWrapper.call_count,
                caller_details,
                self.model_name
            )

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                **kwargs
            )
            # Return a response object that mimics LangChain's response format
            class LangChainResponse:
                def __init__(self, content: str):
                    self.content = content

            return LangChainResponse(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"❌ OpenAIWrapper API call failed: {e}")
            raise


class Config:
    """Configuration management for GST grievance resolution system"""

    # API Keys
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    XAI_API_KEY = os.getenv("XAI_API_KEY")
    if not XAI_API_KEY:
        raise ValueError("XAI_API_KEY is not set")
    TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

    # Model configurations - Unified to grok-4-fast for efficiency
    #PREPROCESSOR_MODEL = "grok-4-fast"
    PREPROCESSOR_MODEL = "grok-4-fast"
    CLASSIFIER_MODEL = "deepseek-chat"
    RESOLVER_MODEL = "grok-4-fast"
    REASONING_MODEL = "deepseek-chat"

    # Embedding model configuration
    LOCAL_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    # Device detection for macOS M1 (MPS), CUDA, or CPU
    @staticmethod
    def get_device():
        """Auto-detect best available device"""
        if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            logger.info("✅ Using Apple Silicon GPU (MPS)")
            return "mps"
        elif torch.cuda.is_available():
            logger.info("✅ Using NVIDIA CUDA GPU")
            return "cuda"
        else:
            logger.info("ℹ️ Using CPU (no GPU detected)")
            return "cpu"

    EMBEDDING_DEVICE = get_device.__func__()

    # Storage paths
    VECTOR_STORE_PATH = "./data/gst_knowledge_base"

    # Thresholds and configurations
    MIN_CONFIDENCE_THRESHOLD = 95
    NULL_RESPONSE_THRESHOLD = 95
    PREPROCESSOR_TEMPERATURE = 0.2
    CLASSIFIER_TEMPERATURE = 0.1
    RESOLVER_TEMPERATURE = 0.0
    WEB_QUERY_TEMPERATURE = 0.2
    MAX_RETRIEVAL_TIME = 10

    # Model-to-Provider Mapping
    MODEL_PROVIDER_MAP = {
        # OpenAI models
        'gpt-3': 'openai',
        'gpt-4': 'openai',
        'o1-preview': 'openai',
        'o1-mini': 'openai',

        # Claude models
        'claude': 'anthropic',

        # DeepSeek models
        'deepseek': 'deepseek',

        # Gemini models
        'gemini': 'google',

        # Grok models
        'grok': 'grok'
    }

    @staticmethod
    def detect_provider(model_name: str) -> str:
        """
        Automatically detect LLM provider based on model name

        Args:
            model_name: The model name string

        Returns:
            Provider name: 'google', 'openai', 'anthropic', 'deepseek', 'grok'
        """
        model_name_lower = model_name.lower()

        for keyword, provider in Config.MODEL_PROVIDER_MAP.items():
            if keyword in model_name_lower:
                return provider

        logger.warning(f"⚠️ Unknown provider for model '{model_name}', defaulting to google")
        return 'google'

    @staticmethod
    def get_api_key_for_provider(provider: str) -> Optional[str]:
        """Get API key for specific provider"""
        api_key_map = {
            'google': Config.GOOGLE_API_KEY,
            'openai': Config.OPENAI_API_KEY,
            'anthropic': Config.ANTHROPIC_API_KEY,
            'deepseek': Config.DEEPSEEK_API_KEY,
            'grok': Config.XAI_API_KEY
        }
        return api_key_map.get(provider)

    @staticmethod
    def get_base_url_for_provider(provider: str) -> Optional[str]:
        """Get base URL for specific provider (if needed)"""
        base_url_map = {
            'deepseek': 'https://api.deepseek.com',
            'grok': 'https://api.x.ai/v1',
            # Other providers use default URLs
        }
        return base_url_map.get(provider)

    # Retrieval settings
    MAX_LOCAL_RESULTS = 5
    MAX_WEB_RESULTS = 10
    MAX_TWITTER_RESULTS = 10

    # Web search settings
    WEB_SEARCH_UNRESTRICTED = True  # Set False to use domain filtering

    # GST specific URLs
    GSTN_FAQ_URL = "https://tutorial.gst.gov.in/downloads/news/FAQ.pdf"
    CBIC_BASE_URL = "https://cbic-gst.gov.in"
    GSTN_TWITTER = "@Infosys_GSTN"

    # LLM instances - centralized initialization
    _preprocessor_llm = None
    _classifier_llm = None
    _resolver_llm = None
    _reasoning_llm = None
    _web_query_llm = None

    @classmethod
    def _create_llm_instance(cls, provider: str, model_name: str, temperature: float = 0.0,
                           response_mime_type: Optional[str] = None, **kwargs):
        """
        Create LLM instance based on provider

        Args:
            provider: LLM provider ('google', 'openai', 'anthropic', 'deepseek', 'grok')
            model_name: Model name
            temperature: Temperature setting
            response_mime_type: Response MIME type (for structured output)
            **kwargs: Additional parameters

        Returns:
            LLM instance
        """
        api_key = cls.get_api_key_for_provider(provider)
        base_url = cls.get_base_url_for_provider(provider)

        if provider == 'google':
            return ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                google_api_key=api_key,
                response_mime_type=response_mime_type,
                **kwargs
            )

        elif provider == 'openai':
            if not HAS_LANGCHAIN_OPENAI:
                raise ImportError("langchain_openai not installed. Install with: pip install langchain-openai")
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=api_key,
                **kwargs
            )

        elif provider == 'anthropic':
            if not HAS_ANTHROPIC:
                raise ImportError("anthropic not installed. Install with: pip install anthropic")
            return anthropic.Anthropic(
                model=model_name,
                temperature=temperature,
                api_key=api_key,
                **kwargs
            )

        elif provider in ['deepseek', 'grok']:
            # For DeepSeek and Grok, we use the OpenAI client with custom base URL
            # Wrap it in a compatible interface that provides invoke() method
            return OpenAIWrapper(
                model_name=model_name,
                api_key=api_key,
                base_url=base_url,
                **kwargs
            )

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    @classmethod
    def get_preprocessor_llm(cls):
        """Get preprocessor LLM instance (lazy initialization)"""
        if cls._preprocessor_llm is None:
            # Auto-detect provider from model name
            provider = cls.detect_provider(cls.PREPROCESSOR_MODEL)
            api_key = cls.get_api_key_for_provider(provider)

            if not api_key:
                logger.error(f"❌ {provider.capitalize()} API key not found for preprocessor LLM. Check .env file.")
                return None

            try:
                cls._preprocessor_llm = cls._create_llm_instance(
                    provider=provider,
                    model_name=cls.PREPROCESSOR_MODEL,
                    temperature=cls.PREPROCESSOR_TEMPERATURE,
                    response_mime_type="application/json"
                )
                logger.info(f"✅ Initialized preprocessor LLM: {cls.PREPROCESSOR_MODEL} ({provider})")
            except Exception as e:
                logger.error(f"❌ Failed to initialize preprocessor LLM: {e}")
        return cls._preprocessor_llm

    @classmethod
    def get_classifier_llm(cls):
        """Get classifier LLM instance (lazy initialization)"""
        if cls._classifier_llm is None:
            # Auto-detect provider from model name
            provider = cls.detect_provider(cls.CLASSIFIER_MODEL)
            api_key = cls.get_api_key_for_provider(provider)

            if not api_key:
                logger.error(f"❌ {provider.capitalize()} API key not found for classifier LLM. Check .env file.")
                return None

            try:
                cls._classifier_llm = cls._create_llm_instance(
                    provider=provider,
                    model_name=cls.CLASSIFIER_MODEL,
                    temperature=cls.CLASSIFIER_TEMPERATURE,
                    response_mime_type="application/json"
                )
                logger.info(f"✅ Initialized classifier LLM: {cls.CLASSIFIER_MODEL} ({provider})")
            except Exception as e:
                logger.error(f"❌ Failed to initialize classifier LLM: {e}")
        return cls._classifier_llm

    @classmethod
    def get_resolver_llm(cls):
        """Get resolver LLM instance (lazy initialization)"""
        if cls._resolver_llm is None:
            # Auto-detect provider from model name
            provider = cls.detect_provider(cls.RESOLVER_MODEL)
            api_key = cls.get_api_key_for_provider(provider)

            if not api_key:
                logger.error(f"❌ {provider.capitalize()} API key not found for resolver LLM. Check .env file.")
                return None

            try:
                cls._resolver_llm = cls._create_llm_instance(
                    provider=provider,
                    model_name=cls.RESOLVER_MODEL,
                    temperature=cls.RESOLVER_TEMPERATURE,
                    response_mime_type="application/json"
                )
                logger.info(f"✅ Initialized resolver LLM: {cls.RESOLVER_MODEL} ({provider})")
            except Exception as e:
                logger.error(f"❌ Failed to initialize resolver LLM: {e}")
        return cls._resolver_llm

    @classmethod
    def get_reasoning_llm(cls):
        """Get reasoning LLM instance (lazy initialization)"""
        if cls._reasoning_llm is None:
            # Auto-detect provider from model name
            provider = cls.detect_provider(cls.REASONING_MODEL)
            api_key = cls.get_api_key_for_provider(provider)

            if not api_key:
                logger.error(f"❌ {provider.capitalize()} API key not found for reasoning LLM. Check .env file.")
                return None

            try:
                cls._reasoning_llm = cls._create_llm_instance(
                    provider=provider,
                    model_name=cls.REASONING_MODEL,
                    temperature=0.1,  # Fixed temperature for reasoning
                )
                logger.info(f"✅ Initialized reasoning LLM: {cls.REASONING_MODEL} ({provider})")
            except Exception as e:
                logger.error(f"❌ Failed to initialize reasoning LLM: {e}")
        return cls._reasoning_llm

    @classmethod
    def get_web_query_llm(cls):
        """Get web query LLM instance (lazy initialization)"""
        if cls._web_query_llm is None:
            # Auto-detect provider from model name (reuse classifier model)
            provider = cls.detect_provider(cls.CLASSIFIER_MODEL)
            api_key = cls.get_api_key_for_provider(provider)

            if not api_key:
                logger.error(f"❌ {provider.capitalize()} API key not found for web query LLM. Check .env file.")
                return None

            try:
                cls._web_query_llm = cls._create_llm_instance(
                    provider=provider,
                    model_name=cls.CLASSIFIER_MODEL,
                    temperature=0.2,  # Slightly higher for creative query building
                )
                logger.info(f"✅ Initialized web query LLM: {cls.CLASSIFIER_MODEL} ({provider})")
            except Exception as e:
                logger.error(f"❌ Failed to initialize web query LLM: {e}")
        return cls._web_query_llm

    @classmethod
    def initialize_all_llms(cls):
        """Initialize all LLMs at once"""
        logger.info("🔄 Initializing all LLMs...")
        success_count = 0

        llms = [
            ("Preprocessor", cls.get_preprocessor_llm()),
            ("Classifier", cls.get_classifier_llm()),
            ("Resolver", cls.get_resolver_llm()),
            ("Reasoning", cls.get_reasoning_llm()),
            ("Web Query", cls.get_web_query_llm())
        ]

        for name, llm in llms:
            if llm is not None:
                success_count += 1
            else:
                logger.error(f"❌ Failed to initialize {name} LLM")

        logger.info(f"✅ Initialized {success_count}/5 LLMs")
        return success_count == 5

    @classmethod
    def swap_llm_provider(cls, llm_type: str, model_name: str, **kwargs):
        """
        Swap LLM provider for specific type

        Args:
            llm_type: 'preprocessor', 'classifier', 'resolver', 'reasoning', 'web_query'
            model_name: New model name (will auto-detect provider)
            **kwargs: Additional parameters
        """
        # Auto-detect provider from model name
        new_provider = cls.detect_provider(model_name)
        logger.info(f"🔄 Swapping {llm_type} LLM to {model_name} ({new_provider})")

        # Clear existing instance
        instance_attr = f"_{llm_type}_llm"
        if hasattr(cls, instance_attr):
            setattr(cls, instance_attr, None)

        # Update model configuration
        model_attr = f"{llm_type.upper()}_MODEL"
        if hasattr(Config, model_attr):
            setattr(Config, model_attr, model_name)

        # Update temperature if provided
        if 'temperature' in kwargs:
            temp_attr = f"{llm_type.upper()}_TEMPERATURE"
            if hasattr(Config, temp_attr):
                setattr(Config, temp_attr, kwargs['temperature'])

        logger.info(f"✅ Updated {llm_type} configuration: {model_name} ({new_provider})")


# Validate configuration
if not Config.GOOGLE_API_KEY:
    logger.warning("⚠️ WARNING: Google API key not found in .env file")

# Log device information
logger.info(f"📊 Device: {Config.EMBEDDING_DEVICE}")
logger.info(f"🔧 PyTorch version: {torch.__version__}")
if Config.EMBEDDING_DEVICE == "mps":
    logger.info(f"🍎 MPS built: {torch.backends.mps.is_built()}")
