"""
Error Handler: Centralized error handling and recovery for AI Math Tutor
Provides consistent error handling, logging, and recovery mechanisms
"""

import logging
import traceback
import time
from typing import Dict, Any, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from functools import wraps

# Error severity levels
class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

# Error categories
class ErrorCategory(Enum):
    API_ERROR = "api_error"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "auth_error"
    RATE_LIMIT_ERROR = "rate_limit"
    CONFIGURATION_ERROR = "config_error"
    PROCESSING_ERROR = "processing_error"
    CACHE_ERROR = "cache_error"
    UNKNOWN_ERROR = "unknown"

@dataclass
class ErrorInfo:
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    timestamp: float
    service: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = None

class ErrorHandler:
    """
    Centralized error handling system for AI Math Tutor.
    
    Features:
    - Automatic error categorization
    - Retry logic with exponential backoff
    - Error recovery strategies
    - Comprehensive logging
    - User-friendly error messages
    """
    
    def __init__(self, log_level=logging.INFO):
        self.error_log = []
        self.retry_strategies = {}
        self.recovery_handlers = {}
        self.error_stats = {
            "total_errors": 0,
            "errors_by_category": {},
            "errors_by_severity": {},
            "recovery_attempts": 0,
            "successful_recoveries": 0
        }
        
        # Setup logging
        self.logger = logging.getLogger("ai_math_tutor")
        self.logger.setLevel(log_level)
        
        # Initialize error handling strategies
        self._initialize_error_strategies()
    
    def _initialize_error_strategies(self):
        """Initialize error handling strategies."""
        
        # API Error Strategies
        self.retry_strategies[ErrorCategory.API_ERROR] = {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 10.0,
            "backoff_multiplier": 2.0
        }
        
        # Network Error Strategies
        self.retry_strategies[ErrorCategory.NETWORK_ERROR] = {
            "max_retries": 5,
            "base_delay": 2.0,
            "max_delay": 30.0,
            "backoff_multiplier": 1.5
        }
        
        # Rate Limit Strategies
        self.retry_strategies[ErrorCategory.RATE_LIMIT_ERROR] = {
            "max_retries": 2,
            "base_delay": 5.0,
            "max_delay": 60.0,
            "backoff_multiplier": 2.0
        }
        
        # Default strategy
        self.retry_strategies[ErrorCategory.UNKNOWN_ERROR] = {
            "max_retries": 2,
            "base_delay": 1.0,
            "max_delay": 5.0,
            "backoff_multiplier": 2.0
        }
    
    def categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error based on exception type and message."""
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # API Errors
        if any(keyword in error_str for keyword in ["api", "openai", "gpt", "model"]):
            return ErrorCategory.API_ERROR
        
        # Network Errors
        if any(keyword in error_str for keyword in ["connection", "timeout", "network", "dns"]):
            return ErrorCategory.NETWORK_ERROR
        
        # Authentication Errors
        if any(keyword in error_str for keyword in ["auth", "key", "permission", "unauthorized"]):
            return ErrorCategory.AUTHENTICATION_ERROR
        
        # Rate Limit Errors
        if any(keyword in error_str for keyword in ["rate", "limit", "quota", "throttle"]):
            return ErrorCategory.RATE_LIMIT_ERROR
        
        # Configuration Errors
        if any(keyword in error_str for keyword in ["config", "setting", "parameter", "missing"]):
            return ErrorCategory.CONFIGURATION_ERROR
        
        # Processing Errors
        if any(keyword in error_str for keyword in ["process", "format", "parse", "decode"]):
            return ErrorCategory.PROCESSING_ERROR
        
        # Cache Errors
        if any(keyword in error_str for keyword in ["cache", "storage", "file", "disk"]):
            return ErrorCategory.CACHE_ERROR
        
        return ErrorCategory.UNKNOWN_ERROR
    
    def determine_severity(self, category: ErrorCategory, error: Exception) -> ErrorSeverity:
        """Determine error severity based on category and context."""
        
        # Critical errors
        if category == ErrorCategory.AUTHENTICATION_ERROR:
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if category in [ErrorCategory.API_ERROR, ErrorCategory.CONFIGURATION_ERROR]:
            return ErrorSeverity.HIGH
        
        # Medium severity errors
        if category in [ErrorCategory.NETWORK_ERROR, ErrorCategory.RATE_LIMIT_ERROR]:
            return ErrorSeverity.MEDIUM
        
        # Low severity errors
        if category in [ErrorCategory.CACHE_ERROR, ErrorCategory.PROCESSING_ERROR]:
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def create_error_info(self, error: Exception, service: str, 
                         user_id: str = None, session_id: str = None,
                         metadata: Dict[str, Any] = None) -> ErrorInfo:
        """Create structured error information."""
        
        category = self.categorize_error(error)
        severity = self.determine_severity(category, error)
        
        error_id = f"err_{int(time.time() * 1000)}_{hash(str(error)) % 10000}"
        
        return ErrorInfo(
            error_id=error_id,
            category=category,
            severity=severity,
            message=str(error),
            timestamp=time.time(),
            service=service,
            user_id=user_id,
            session_id=session_id,
            metadata=metadata or {}
        )
    
    def handle_error(self, error: Exception, service: str, 
                    user_id: str = None, session_id: str = None,
                    metadata: Dict[str, Any] = None) -> ErrorInfo:
        """Handle error with logging and categorization."""
        
        error_info = self.create_error_info(error, service, user_id, session_id, metadata)
        
        # Log error
        self._log_error(error_info)
        
        # Update statistics
        self._update_error_stats(error_info)
        
        # Store in error log
        self.error_log.append(error_info)
        
        return error_info
    
    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level."""
        
        log_message = f"[{error_info.error_id}] {error_info.service}: {error_info.message}"
        
        if error_info.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)
    
    def _update_error_stats(self, error_info: ErrorInfo):
        """Update error statistics."""
        self.error_stats["total_errors"] += 1
        
        # Update category stats
        category = error_info.category.value
        self.error_stats["errors_by_category"][category] = \
            self.error_stats["errors_by_category"].get(category, 0) + 1
        
        # Update severity stats
        severity = error_info.severity.value
        self.error_stats["errors_by_severity"][severity] = \
            self.error_stats["errors_by_severity"].get(severity, 0) + 1
    
    def retry_with_backoff(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with retry logic and exponential backoff."""
        
        error_info = None
        last_error = None
        
        for attempt in range(3):  # Default max retries
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                error_info = self.handle_error(e, "retry_function")
                
                if attempt < 2:  # Not the last attempt
                    delay = min(2 ** attempt, 10)  # Exponential backoff, max 10s
                    time.sleep(delay)
                    print(f"🔄 Retry attempt {attempt + 2} after {delay}s delay...")
                else:
                    print(f"❌ All retry attempts failed")
        
        # All retries failed
        if error_info:
            error_info.retry_count = 3
        
        raise last_error
    
    def get_user_friendly_message(self, error_info: ErrorInfo) -> str:
        """Get user-friendly error message."""
        
        messages = {
            ErrorCategory.API_ERROR: "The AI service is temporarily unavailable. Please try again in a moment.",
            ErrorCategory.NETWORK_ERROR: "There's a connection issue. Please check your internet connection and try again.",
            ErrorCategory.AUTHENTICATION_ERROR: "There's an authentication issue. Please contact support.",
            ErrorCategory.RATE_LIMIT_ERROR: "Too many requests. Please wait a moment before trying again.",
            ErrorCategory.CONFIGURATION_ERROR: "There's a configuration issue. Please contact support.",
            ErrorCategory.PROCESSING_ERROR: "There was an issue processing your request. Please try again.",
            ErrorCategory.CACHE_ERROR: "There's a temporary storage issue. Your request will be processed normally.",
            ErrorCategory.UNKNOWN_ERROR: "An unexpected error occurred. Please try again."
        }
        
        return messages.get(error_info.category, messages[ErrorCategory.UNKNOWN_ERROR])
    
    def get_error_report(self) -> Dict[str, Any]:
        """Get comprehensive error report."""
        return {
            "error_statistics": self.error_stats,
            "recent_errors": [
                {
                    "error_id": err.error_id,
                    "category": err.category.value,
                    "severity": err.severity.value,
                    "service": err.service,
                    "timestamp": err.timestamp,
                    "message": err.message[:100] + "..." if len(err.message) > 100 else err.message
                }
                for err in self.error_log[-10:]  # Last 10 errors
            ],
            "error_trends": self._calculate_error_trends(),
            "recommendations": self._get_error_recommendations()
        }
    
    def _calculate_error_trends(self) -> Dict[str, Any]:
        """Calculate error trends and patterns."""
        if not self.error_log:
            return {"trend": "stable", "pattern": "no_errors"}
        
        # Simple trend analysis
        recent_errors = [err for err in self.error_log if time.time() - err.timestamp < 3600]  # Last hour
        older_errors = [err for err in self.error_log if time.time() - err.timestamp >= 3600]
        
        recent_count = len(recent_errors)
        older_count = len(older_errors)
        
        if recent_count > older_count * 1.5:
            trend = "increasing"
        elif recent_count < older_count * 0.5:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {"trend": trend, "recent_errors": recent_count, "older_errors": older_count}
    
    def _get_error_recommendations(self) -> list:
        """Get recommendations based on error patterns."""
        recommendations = []
        
        # Check for high error rates
        if self.error_stats["total_errors"] > 50:
            recommendations.append("High error rate detected. Consider checking service health.")
        
        # Check for specific error patterns
        api_errors = self.error_stats["errors_by_category"].get("api_error", 0)
        if api_errors > 10:
            recommendations.append("Multiple API errors. Check API key and quota.")
        
        network_errors = self.error_stats["errors_by_category"].get("network_error", 0)
        if network_errors > 5:
            recommendations.append("Network issues detected. Check connectivity.")
        
        return recommendations


# Global error handler instance
error_handler = ErrorHandler()


def handle_service_error(func):
    """Decorator for automatic error handling in service functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            # Extract service name from function name or module
            service_name = func.__name__.split('_')[0] if '_' in func.__name__ else "unknown"
            
            error_info = error_handler.handle_error(e, service_name)
            user_message = error_handler.get_user_friendly_message(error_info)
            
            # Return user-friendly error instead of raising
            return {
                "success": False,
                "error": user_message,
                "error_id": error_info.error_id,
                "details": error_info.message if error_info.severity == ErrorSeverity.LOW else None
            }
    
    return wrapper


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """Decorator for retry logic with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        time.sleep(delay * (2 ** attempt))  # Exponential backoff
                        print(f"🔄 Retry attempt {attempt + 2}/{max_retries}")
            
            # All retries failed
            raise last_error
        return wrapper
    return decorator


if __name__ == "__main__":
    # Test error handler
    print("🧪 Testing Error Handler")
    print("=" * 50)
    
    # Test error categorization
    test_errors = [
        Exception("OpenAI API key invalid"),
        Exception("Connection timeout"),
        Exception("Rate limit exceeded"),
        Exception("Configuration file missing"),
        Exception("Unknown error")
    ]
    
    for error in test_errors:
        category = error_handler.categorize_error(error)
        severity = error_handler.determine_severity(category, error)
        print(f"Error: {error}")
        print(f"  Category: {category.value}")
        print(f"  Severity: {severity.value}")
        print()
    
    # Test error handling
    try:
        error_info = error_handler.handle_error(
            Exception("Test API error"), 
            "test_service",
            user_id="test_user"
        )
        print(f"✅ Error handled: {error_info.error_id}")
        
        # Get user-friendly message
        user_message = error_handler.get_user_friendly_message(error_info)
        print(f"User message: {user_message}")
        
    except Exception as e:
        print(f"❌ Error handling failed: {e}")
    
    # Get error report
    report = error_handler.get_error_report()
    print(f"\n📊 Error Report:")
    print(f"   Total Errors: {report['error_statistics']['total_errors']}")
    print(f"   Recent Errors: {len(report['recent_errors'])}")
    print(f"   Recommendations: {len(report['recommendations'])}")
    
    print("\n✅ Error Handler test complete!")
