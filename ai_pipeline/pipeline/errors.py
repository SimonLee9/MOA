"""
Custom Exception Classes for AI Pipeline
Provides structured error handling with recovery information
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    WARNING = "warning"      # Can continue with degraded functionality
    ERROR = "error"          # Node failed but can retry
    CRITICAL = "critical"    # Pipeline must stop


class ErrorCategory(str, Enum):
    """Error categories for classification"""
    NETWORK = "network"           # Network/connection issues
    EXTERNAL_API = "external_api" # Third-party API errors
    VALIDATION = "validation"     # Input/output validation errors
    PROCESSING = "processing"     # Internal processing errors
    TIMEOUT = "timeout"           # Operation timeout
    RESOURCE = "resource"         # Resource unavailable
    AUTHENTICATION = "auth"       # Auth/credential errors


class PipelineError(Exception):
    """
    Base exception for pipeline errors

    Attributes:
        message: Human-readable error message
        node: Name of the node where error occurred
        severity: Error severity level
        category: Error category for classification
        recoverable: Whether error can be recovered with retry
        retry_delay: Suggested delay before retry (seconds)
        context: Additional context information
    """

    def __init__(
        self,
        message: str,
        node: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        category: ErrorCategory = ErrorCategory.PROCESSING,
        recoverable: bool = True,
        retry_delay: int = 0,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.node = node
        self.severity = severity
        self.category = category
        self.recoverable = recoverable
        self.retry_delay = retry_delay
        self.context = context or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization"""
        return {
            "error": self.message,
            "node": self.node,
            "severity": self.severity.value,
            "category": self.category.value,
            "recoverable": self.recoverable,
            "retry_delay": self.retry_delay,
            "context": self.context,
        }


class STTError(PipelineError):
    """Speech-to-Text processing errors"""

    def __init__(
        self,
        message: str,
        audio_url: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop("context", {})
        context["audio_url"] = audio_url
        super().__init__(
            message=message,
            node="stt",
            category=ErrorCategory.EXTERNAL_API,
            context=context,
            **kwargs
        )


class STTNetworkError(STTError):
    """Network error during STT"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            recoverable=True,
            retry_delay=5,
            **kwargs
        )


class STTTimeoutError(STTError):
    """Timeout during STT processing"""

    def __init__(self, message: str, timeout_seconds: int = 0, **kwargs):
        context = kwargs.pop("context", {})
        context["timeout_seconds"] = timeout_seconds
        super().__init__(
            message=message,
            category=ErrorCategory.TIMEOUT,
            recoverable=True,
            retry_delay=10,
            context=context,
            **kwargs
        )


class STTAudioError(STTError):
    """Invalid audio file error"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            recoverable=False,
            severity=ErrorSeverity.CRITICAL,
            **kwargs
        )


class LLMError(PipelineError):
    """LLM (Claude) processing errors"""

    def __init__(
        self,
        message: str,
        node: str = "llm",
        prompt_type: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop("context", {})
        context["prompt_type"] = prompt_type
        super().__init__(
            message=message,
            node=node,
            category=ErrorCategory.EXTERNAL_API,
            context=context,
            **kwargs
        )


class LLMRateLimitError(LLMError):
    """Rate limit exceeded for LLM API"""

    def __init__(self, message: str, retry_after: int = 60, **kwargs):
        super().__init__(
            message=message,
            recoverable=True,
            retry_delay=retry_after,
            **kwargs
        )


class LLMResponseError(LLMError):
    """Invalid response from LLM"""

    def __init__(self, message: str, response_text: Optional[str] = None, **kwargs):
        context = kwargs.pop("context", {})
        if response_text:
            context["response_preview"] = response_text[:200]
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            recoverable=True,
            retry_delay=0,
            context=context,
            **kwargs
        )


class SummarizerError(LLMError):
    """Summarization errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            node="summarizer",
            prompt_type="summarize",
            **kwargs
        )


class ActionExtractorError(LLMError):
    """Action extraction errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            node="extract_actions",
            prompt_type="extract_actions",
            **kwargs
        )


class CritiqueError(LLMError):
    """Critique node errors"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            node="critique",
            prompt_type="critique",
            **kwargs
        )


class MCPError(PipelineError):
    """MCP tool execution errors"""

    def __init__(
        self,
        message: str,
        tool_name: Optional[str] = None,
        **kwargs
    ):
        context = kwargs.pop("context", {})
        context["tool_name"] = tool_name
        super().__init__(
            message=message,
            node="executor",
            category=ErrorCategory.EXTERNAL_API,
            context=context,
            **kwargs
        )


class MCPConnectionError(MCPError):
    """MCP server connection error"""

    def __init__(self, message: str, server_type: Optional[str] = None, **kwargs):
        context = kwargs.pop("context", {})
        context["server_type"] = server_type
        super().__init__(
            message=message,
            recoverable=True,
            retry_delay=5,
            context=context,
            **kwargs
        )


class MCPToolNotFoundError(MCPError):
    """Requested MCP tool not available"""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            recoverable=False,
            **kwargs
        )


class ValidationError(PipelineError):
    """Input/output validation errors"""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ):
        context = kwargs.pop("context", {})
        context["field"] = field
        if value is not None:
            context["value"] = str(value)[:100]
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            recoverable=False,
            context=context,
            **kwargs
        )


class MaxRetriesExceededError(PipelineError):
    """Maximum retry attempts exceeded"""

    def __init__(
        self,
        message: str,
        max_retries: int = 0,
        **kwargs
    ):
        context = kwargs.pop("context", {})
        context["max_retries"] = max_retries
        super().__init__(
            message=message,
            severity=ErrorSeverity.CRITICAL,
            recoverable=False,
            context=context,
            **kwargs
        )
