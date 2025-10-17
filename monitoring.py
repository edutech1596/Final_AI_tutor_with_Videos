"""
Monitoring System: Comprehensive monitoring and logging for AI Math Tutor
Provides real-time monitoring, performance tracking, and alerting
"""

import os
import json
import time
import psutil
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

@dataclass
class MetricPoint:
    timestamp: float
    value: float
    tags: Dict[str, str] = None

@dataclass
class Alert:
    alert_id: str
    severity: str
    message: str
    timestamp: float
    service: str
    resolved: bool = False

class PerformanceMonitor:
    """
    Real-time performance monitoring for AI Math Tutor.
    
    Features:
    - System resource monitoring
    - Service performance tracking
    - Custom metrics collection
    - Alert generation
    - Historical data storage
    """
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics = defaultdict(lambda: deque(maxlen=max_history))
        self.alerts = []
        self.service_stats = {}
        self.system_stats = {}
        
        # Setup logging
        self.logger = logging.getLogger("ai_math_tutor_monitor")
        self.logger.setLevel(logging.INFO)
        
        # Initialize monitoring
        self._initialize_monitoring()
    
    def _initialize_monitoring(self):
        """Initialize monitoring systems."""
        
        # System metrics to track
        self.system_metrics = [
            "cpu_percent",
            "memory_percent",
            "disk_usage",
            "network_io"
        ]
        
        # Service metrics to track
        self.service_metrics = [
            "response_time",
            "success_rate",
            "error_rate",
            "throughput"
        ]
        
        # Alert thresholds
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "response_time": 10.0,
            "error_rate": 0.1,  # 10%
            "success_rate": 0.8  # 80%
        }
    
    def collect_system_metrics(self) -> Dict[str, float]:
        """Collect current system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = network.bytes_sent + network.bytes_recv
            
            metrics = {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "network_io": network_io,
                "timestamp": time.time()
            }
            
            # Store metrics
            for key, value in metrics.items():
                if key != "timestamp":
                    self.metrics[key].append(MetricPoint(
                        timestamp=time.time(),
                        value=value,
                        tags={"type": "system"}
                    ))
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Failed to collect system metrics: {e}")
            return {}
    
    def collect_service_metrics(self, service_name: str, 
                               response_time: float, success: bool):
        """Collect service-specific metrics."""
        
        # Update service stats
        if service_name not in self.service_stats:
            self.service_stats[service_name] = {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "total_response_time": 0.0,
                "avg_response_time": 0.0,
                "last_updated": time.time()
            }
        
        stats = self.service_stats[service_name]
        stats["total_requests"] += 1
        stats["total_response_time"] += response_time
        stats["avg_response_time"] = stats["total_response_time"] / stats["total_requests"]
        stats["last_updated"] = time.time()
        
        if success:
            stats["successful_requests"] += 1
        else:
            stats["failed_requests"] += 1
        
        # Calculate rates
        success_rate = stats["successful_requests"] / stats["total_requests"]
        error_rate = stats["failed_requests"] / stats["total_requests"]
        
        # Store metrics
        self.metrics[f"{service_name}_response_time"].append(MetricPoint(
            timestamp=time.time(),
            value=response_time,
            tags={"service": service_name, "type": "performance"}
        ))
        
        self.metrics[f"{service_name}_success_rate"].append(MetricPoint(
            timestamp=time.time(),
            value=success_rate,
            tags={"service": service_name, "type": "reliability"}
        ))
        
        # Check for alerts
        self._check_alerts(service_name, {
            "response_time": response_time,
            "success_rate": success_rate,
            "error_rate": error_rate
        })
    
    def _check_alerts(self, service_name: str, metrics: Dict[str, float]):
        """Check metrics against alert thresholds."""
        
        for metric_name, value in metrics.items():
            threshold = self.alert_thresholds.get(metric_name)
            
            if threshold and value > threshold:
                alert = Alert(
                    alert_id=f"alert_{int(time.time() * 1000)}",
                    severity="warning" if value < threshold * 1.5 else "critical",
                    message=f"{service_name} {metric_name} is {value:.2f} (threshold: {threshold})",
                    timestamp=time.time(),
                    service=service_name
                )
                
                self.alerts.append(alert)
                self.logger.warning(f"ALERT: {alert.message}")
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get current system health status."""
        system_metrics = self.collect_system_metrics()
        
        health_status = "healthy"
        issues = []
        
        # Check CPU
        if system_metrics.get("cpu_percent", 0) > 80:
            health_status = "degraded"
            issues.append("High CPU usage")
        
        # Check Memory
        if system_metrics.get("memory_percent", 0) > 85:
            health_status = "degraded"
            issues.append("High memory usage")
        
        # Check Disk
        if system_metrics.get("disk_percent", 0) > 90:
            health_status = "critical"
            issues.append("Low disk space")
        
        return {
            "status": health_status,
            "issues": issues,
            "metrics": system_metrics,
            "timestamp": time.time()
        }
    
    def get_service_health(self, service_name: str = None) -> Dict[str, Any]:
        """Get service health status."""
        if service_name:
            if service_name not in self.service_stats:
                return {"status": "unknown", "message": "Service not found"}
            
            stats = self.service_stats[service_name]
            success_rate = stats["successful_requests"] / stats["total_requests"] if stats["total_requests"] > 0 else 0
            
            status = "healthy"
            if success_rate < 0.8:
                status = "degraded"
            if success_rate < 0.5:
                status = "critical"
            
            return {
                "status": status,
                "stats": stats,
                "success_rate": success_rate,
                "avg_response_time": stats["avg_response_time"]
            }
        else:
            # Return all services
            return {
                service: self.get_service_health(service)
                for service in self.service_stats.keys()
            }
    
    def get_metrics_summary(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get metrics summary for the last time window."""
        cutoff_time = time.time() - time_window
        
        summary = {}
        
        for metric_name, metric_points in self.metrics.items():
            recent_points = [
                point for point in metric_points
                if point.timestamp >= cutoff_time
            ]
            
            if recent_points:
                values = [point.value for point in recent_points]
                summary[metric_name] = {
                    "count": len(values),
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "latest": values[-1] if values else None
                }
        
        return summary
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get active (unresolved) alerts."""
        active_alerts = [alert for alert in self.alerts if not alert.resolved]
        
        return [
            {
                "alert_id": alert.alert_id,
                "severity": alert.severity,
                "message": alert.message,
                "timestamp": alert.timestamp,
                "service": alert.service,
                "age_minutes": (time.time() - alert.timestamp) / 60
            }
            for alert in active_alerts
        ]
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                return True
        return False
    
    def export_metrics(self, filepath: str = None) -> str:
        """Export metrics to JSON file."""
        if filepath is None:
            filepath = f"metrics_export_{int(time.time())}.json"
        
        export_data = {
            "export_timestamp": time.time(),
            "system_health": self.get_system_health(),
            "service_health": self.get_service_health(),
            "metrics_summary": self.get_metrics_summary(),
            "active_alerts": self.get_active_alerts(),
            "service_stats": self.service_stats
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return filepath
    
    def cleanup_old_data(self, max_age_hours: int = 24):
        """Clean up old metrics and alerts."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        # Clean up old metrics
        for metric_name in list(self.metrics.keys()):
            self.metrics[metric_name] = deque([
                point for point in self.metrics[metric_name]
                if point.timestamp >= cutoff_time
            ], maxlen=self.max_history)
        
        # Clean up old alerts
        self.alerts = [
            alert for alert in self.alerts
            if alert.timestamp >= cutoff_time or not alert.resolved
        ]
        
        self.logger.info(f"Cleaned up data older than {max_age_hours} hours")


# Global monitoring instance
monitor = PerformanceMonitor()


def track_service_call(service_name: str):
    """Decorator to track service calls automatically."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise
            finally:
                response_time = time.time() - start_time
                monitor.collect_service_metrics(service_name, response_time, success)
        
        return wrapper
    return decorator


def get_monitoring_dashboard() -> Dict[str, Any]:
    """Get comprehensive monitoring dashboard data."""
    return {
        "system_health": monitor.get_system_health(),
        "service_health": monitor.get_service_health(),
        "metrics_summary": monitor.get_metrics_summary(),
        "active_alerts": monitor.get_active_alerts(),
        "timestamp": time.time()
    }


if __name__ == "__main__":
    # Test monitoring system
    print("🧪 Testing Monitoring System")
    print("=" * 50)
    
    # Test system metrics
    print("📊 Collecting system metrics...")
    system_metrics = monitor.collect_system_metrics()
    print(f"CPU: {system_metrics.get('cpu_percent', 0):.1f}%")
    print(f"Memory: {system_metrics.get('memory_percent', 0):.1f}%")
    print(f"Disk: {system_metrics.get('disk_percent', 0):.1f}%")
    
    # Test service metrics
    print("\n📈 Testing service metrics...")
    monitor.collect_service_metrics("test_service", 1.5, True)
    monitor.collect_service_metrics("test_service", 0.8, True)
    monitor.collect_service_metrics("test_service", 2.1, False)
    
    # Get health status
    print("\n🏥 System Health:")
    health = monitor.get_system_health()
    print(f"Status: {health['status']}")
    print(f"Issues: {health['issues']}")
    
    # Get service health
    print("\n🔧 Service Health:")
    service_health = monitor.get_service_health("test_service")
    print(f"Status: {service_health['status']}")
    print(f"Success Rate: {service_health['success_rate']:.2%}")
    print(f"Avg Response Time: {service_health['avg_response_time']:.2f}s")
    
    # Get active alerts
    print("\n🚨 Active Alerts:")
    alerts = monitor.get_active_alerts()
    print(f"Count: {len(alerts)}")
    for alert in alerts:
        print(f"  - {alert['severity']}: {alert['message']}")
    
    # Export metrics
    print("\n💾 Exporting metrics...")
    export_file = monitor.export_metrics()
    print(f"Exported to: {export_file}")
    
    print("\n✅ Monitoring system test complete!")
