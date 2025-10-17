"""
Service Manager: Centralized service orchestration and configuration
Provides unified interface for all AI Math Tutor services
"""

import os
import time
from typing import Dict, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

# Service status tracking
class ServiceStatus(Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEGRADED = "degraded"
    ERROR = "error"

@dataclass
class ServiceInfo:
    name: str
    status: ServiceStatus
    last_check: float
    error_count: int = 0
    response_time: float = 0.0
    metadata: Dict[str, Any] = None

class ServiceManager:
    """
    Centralized service manager for AI Math Tutor.
    
    Features:
    - Service health monitoring
    - Automatic fallback handling
    - Performance tracking
    - Configuration management
    """
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.service_configs = {}
        self.fallback_chains = {}
        self.performance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_response_time": 0.0
        }
        
        # Initialize service configurations
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize all service configurations."""
        
        # LLM Service Configuration
        self.service_configs["llm"] = {
            "primary": "openai",
            "fallbacks": ["mock"],
            "timeout": 30,
            "retry_attempts": 3,
            "cache_ttl": 3600  # 1 hour
        }
        
        # TTS Service Configuration
        self.service_configs["tts"] = {
            "primary": "gtts",
            "fallbacks": ["pyttsx3", "piper", "fallback"],
            "timeout": 15,
            "retry_attempts": 2,
            "cache_ttl": 1800  # 30 minutes
        }
        
        # STT Service Configuration
        self.service_configs["stt"] = {
            "primary": "google",
            "fallbacks": ["vosk", "mock"],
            "timeout": 10,
            "retry_attempts": 2,
            "cache_ttl": 0  # No caching for STT
        }
        
        # Image Service Configuration
        self.service_configs["image"] = {
            "primary": "openai_vision",
            "fallbacks": ["mathpix", "tesseract"],
            "timeout": 20,
            "retry_attempts": 2,
            "cache_ttl": 7200  # 2 hours
        }
        
        # Initialize service statuses
        for service_name in self.service_configs:
            self.services[service_name] = ServiceInfo(
                name=service_name,
                status=ServiceStatus.UNAVAILABLE,
                last_check=0.0,
                metadata={}
            )
    
    def register_service(self, name: str, service_instance: Any, 
                        health_check_func: callable = None):
        """
        Register a service with the manager.
        
        Args:
            name: Service name
            service_instance: Service instance
            health_check_func: Optional health check function
        """
        self.services[name] = ServiceInfo(
            name=name,
            status=ServiceStatus.AVAILABLE,
            last_check=time.time(),
            metadata={"instance": service_instance, "health_check": health_check_func}
        )
    
    def check_service_health(self, service_name: str) -> ServiceStatus:
        """Check health of a specific service."""
        if service_name not in self.services:
            return ServiceStatus.UNAVAILABLE
        
        service = self.services[service_name]
        
        try:
            # Run health check if available
            if service.metadata and service.metadata.get("health_check"):
                health_check = service.metadata["health_check"]
                is_healthy = health_check()
                
                if is_healthy:
                    service.status = ServiceStatus.AVAILABLE
                    service.error_count = 0
                else:
                    service.status = ServiceStatus.DEGRADED
                    service.error_count += 1
            else:
                # Default health check - assume available if registered
                service.status = ServiceStatus.AVAILABLE
            
            service.last_check = time.time()
            
        except Exception as e:
            service.status = ServiceStatus.ERROR
            service.error_count += 1
            print(f"❌ Health check failed for {service_name}: {e}")
        
        return service.status
    
    def get_available_service(self, service_type: str) -> Optional[str]:
        """
        Get the best available service for a given type.
        
        Args:
            service_type: Type of service (llm, tts, stt, image)
            
        Returns:
            Name of available service or None
        """
        if service_type not in self.service_configs:
            return None
        
        config = self.service_configs[service_type]
        services_to_try = [config["primary"]] + config["fallbacks"]
        
        for service_name in services_to_try:
            if service_name in self.services:
                status = self.check_service_health(service_name)
                if status in [ServiceStatus.AVAILABLE, ServiceStatus.DEGRADED]:
                    return service_name
        
        return None
    
    def execute_with_fallback(self, service_type: str, operation: str, 
                             *args, **kwargs) -> Tuple[Any, str]:
        """
        Execute operation with automatic fallback handling.
        
        Args:
            service_type: Type of service
            operation: Operation to perform
            *args, **kwargs: Arguments for the operation
            
        Returns:
            Tuple of (result, service_used)
        """
        config = self.service_configs.get(service_type, {})
        services_to_try = [config.get("primary")] + config.get("fallbacks", [])
        
        last_error = None
        
        for service_name in services_to_try:
            if service_name not in self.services:
                continue
            
            try:
                service = self.services[service_name]
                service_instance = service.metadata.get("instance")
                
                if not service_instance:
                    continue
                
                # Execute the operation
                start_time = time.time()
                result = getattr(service_instance, operation)(*args, **kwargs)
                response_time = time.time() - start_time
                
                # Update performance stats
                self._update_performance_stats(True, response_time)
                service.response_time = response_time
                
                return result, service_name
                
            except Exception as e:
                last_error = e
                print(f"❌ Service {service_name} failed: {e}")
                self._update_performance_stats(False, 0)
                continue
        
        # All services failed
        raise Exception(f"All {service_type} services failed. Last error: {last_error}")
    
    def _update_performance_stats(self, success: bool, response_time: float):
        """Update performance statistics."""
        self.performance_stats["total_requests"] += 1
        
        if success:
            self.performance_stats["successful_requests"] += 1
            
            # Update average response time
            current_avg = self.performance_stats["avg_response_time"]
            total_successful = self.performance_stats["successful_requests"]
            self.performance_stats["avg_response_time"] = (
                (current_avg * (total_successful - 1) + response_time) / total_successful
            )
        else:
            self.performance_stats["failed_requests"] += 1
    
    def get_service_status(self, service_name: str) -> Optional[ServiceInfo]:
        """Get status information for a service."""
        return self.services.get(service_name)
    
    def get_all_service_status(self) -> Dict[str, ServiceInfo]:
        """Get status of all services."""
        return self.services.copy()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics."""
        stats = self.performance_stats.copy()
        
        if stats["total_requests"] > 0:
            stats["success_rate"] = stats["successful_requests"] / stats["total_requests"]
        else:
            stats["success_rate"] = 0.0
        
        return stats
    
    def reset_service_errors(self, service_name: str):
        """Reset error count for a service."""
        if service_name in self.services:
            self.services[service_name].error_count = 0
            self.services[service_name].status = ServiceStatus.AVAILABLE
    
    def get_service_recommendations(self) -> Dict[str, str]:
        """Get recommendations for service optimization."""
        recommendations = {}
        
        for service_name, service in self.services.items():
            if service.error_count > 5:
                recommendations[service_name] = f"High error count ({service.error_count}). Consider checking configuration."
            elif service.response_time > 10.0:
                recommendations[service_name] = f"Slow response time ({service.response_time:.2f}s). Consider optimization."
            elif service.status == ServiceStatus.DEGRADED:
                recommendations[service_name] = "Service is degraded. Check dependencies."
        
        return recommendations


# Global service manager instance
service_manager = ServiceManager()


def register_llm_service(service_instance, health_check_func=None):
    """Register LLM service with the manager."""
    service_manager.register_service("openai", service_instance, health_check_func)


def register_tts_service(service_instance, health_check_func=None):
    """Register TTS service with the manager."""
    service_manager.register_service("gtts", service_instance, health_check_func)


def register_stt_service(service_instance, health_check_func=None):
    """Register STT service with the manager."""
    service_manager.register_service("google", service_instance, health_check_func)


def register_image_service(service_instance, health_check_func=None):
    """Register image service with the manager."""
    service_manager.register_service("openai_vision", service_instance, health_check_func)


def get_service_health_report() -> Dict[str, Any]:
    """Get comprehensive service health report."""
    all_status = service_manager.get_all_service_status()
    performance = service_manager.get_performance_stats()
    recommendations = service_manager.get_service_recommendations()
    
    return {
        "services": {name: {
            "status": service.status.value,
            "error_count": service.error_count,
            "response_time": service.response_time,
            "last_check": service.last_check
        } for name, service in all_status.items()},
        "performance": performance,
        "recommendations": recommendations,
        "timestamp": time.time()
    }


if __name__ == "__main__":
    # Test service manager
    print("🧪 Testing Service Manager")
    print("=" * 50)
    
    # Initialize with mock services
    class MockLLMService:
        def generate_response(self, text):
            return f"Mock response to: {text}"
        
        def health_check(self):
            return True
    
    class MockTTSService:
        def generate_audio(self, text):
            return f"mock_audio_{hash(text)}.wav"
        
        def health_check(self):
            return True
    
    # Register services
    register_llm_service(MockLLMService())
    register_tts_service(MockTTSService())
    
    # Test service discovery
    llm_service = service_manager.get_available_service("llm")
    print(f"Available LLM service: {llm_service}")
    
    # Test execution with fallback
    try:
        result, service_used = service_manager.execute_with_fallback(
            "llm", "generate_response", "Test question"
        )
        print(f"✅ Operation successful using {service_used}: {result}")
    except Exception as e:
        print(f"❌ Operation failed: {e}")
    
    # Get health report
    health_report = get_service_health_report()
    print(f"\n📊 Health Report:")
    print(f"   Services: {len(health_report['services'])}")
    print(f"   Success Rate: {health_report['performance']['success_rate']:.2%}")
    print(f"   Recommendations: {len(health_report['recommendations'])}")
    
    print("\n✅ Service Manager test complete!")
