"""
DevOps Event Callbacks for ComfyUI Agent

Provides hooks for monitoring agent execution, tool calls, and errors.
Designed for integration with logging systems, metrics collectors, and monitoring dashboards.

Usage:
    from agents.comfy.callbacks import LoggingCallback, MetricsCallback
    from agents.comfy.debug import get_logger
    
    # Add callbacks to agent
    logger = get_logger(__name__)
    logging_callback = LoggingCallback(logger)
    metrics_callback = MetricsCallback()
    
    # Callbacks are triggered automatically during agent execution
"""

import json
import time
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from .debug import get_logger


class AgentEventCallback(ABC):
    """
    Base class for agent event callbacks.
    
    Subclass this to create custom monitoring integrations.
    """
    
    @abstractmethod
    def on_agent_start(self, agent_name: str, user_query: str, metadata: Optional[Dict[str, Any]] = None):
        """Called when agent starts processing a request."""
        pass
    
    @abstractmethod
    def on_agent_complete(self, agent_name: str, response: str, elapsed: float, metadata: Optional[Dict[str, Any]] = None):
        """Called when agent completes successfully."""
        pass
    
    @abstractmethod
    def on_agent_error(self, agent_name: str, error: Exception, elapsed: float, metadata: Optional[Dict[str, Any]] = None):
        """Called when agent encounters an error."""
        pass
    
    @abstractmethod
    def on_tool_call(self, tool_name: str, arguments: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Called when a tool is invoked."""
        pass
    
    @abstractmethod
    def on_tool_result(self, tool_name: str, result: Any, elapsed: float, metadata: Optional[Dict[str, Any]] = None):
        """Called when a tool returns a result."""
        pass
    
    @abstractmethod
    def on_sub_agent_delegate(self, parent_agent: str, sub_agent: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Called when delegating to a sub-agent."""
        pass


class LoggingCallback(AgentEventCallback):
    """
    Callback that logs all events to a structured logger.
    
    Logs are emitted in JSON format for easy parsing by log aggregation systems.
    """
    
    def __init__(self, logger=None, json_format: bool = False):
        """
        Args:
            logger: Logger instance (uses default if None)
            json_format: If True, emit JSON-formatted logs
        """
        self.logger = logger or get_logger("callbacks")
        self.json_format = json_format
        self.session_id = f"session_{int(time.time())}"
    
    def _log(self, event_type: str, data: Dict[str, Any], level: str = "info"):
        """Internal logging helper."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": event_type,
            **data
        }
        
        if self.json_format:
            log_message = json.dumps(event)
        else:
            log_message = f"[{event_type}] {data}"
        
        if level == "info":
            self.logger.info(log_message)
        elif level == "warning":
            self.logger.warning(log_message)
        elif level == "error":
            self.logger.error(log_message)
        elif level == "debug":
            self.logger.debug(log_message)
    
    def on_agent_start(self, agent_name: str, user_query: str, metadata: Optional[Dict[str, Any]] = None):
        self._log("agent_start", {
            "agent": agent_name,
            "query": user_query[:100] + "..." if len(user_query) > 100 else user_query,
            "metadata": metadata or {}
        })
    
    def on_agent_complete(self, agent_name: str, response: str, elapsed: float, metadata: Optional[Dict[str, Any]] = None):
        self._log("agent_complete", {
            "agent": agent_name,
            "response_length": len(response),
            "elapsed_seconds": elapsed,
            "metadata": metadata or {}
        })
    
    def on_agent_error(self, agent_name: str, error: Exception, elapsed: float, metadata: Optional[Dict[str, Any]] = None):
        self._log("agent_error", {
            "agent": agent_name,
            "error": str(error),
            "error_type": type(error).__name__,
            "elapsed_seconds": elapsed,
            "metadata": metadata or {}
        }, level="error")
    
    def on_tool_call(self, tool_name: str, arguments: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        self._log("tool_call", {
            "tool": tool_name,
            "arguments": arguments,
            "metadata": metadata or {}
        }, level="debug")
    
    def on_tool_result(self, tool_name: str, result: Any, elapsed: float, metadata: Optional[Dict[str, Any]] = None):
        # Truncate large results to avoid log spam
        result_summary = str(result)[:200] if result else "None"
        
        self._log("tool_result", {
            "tool": tool_name,
            "result_summary": result_summary,
            "elapsed_seconds": elapsed,
            "metadata": metadata or {}
        }, level="debug")
    
    def on_sub_agent_delegate(self, parent_agent: str, sub_agent: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        self._log("sub_agent_delegate", {
            "parent": parent_agent,
            "sub_agent": sub_agent,
            "message": message[:100] + "..." if len(message) > 100 else message,
            "metadata": metadata or {}
        })


class MetricsCallback(AgentEventCallback):
    """
    Callback stub for metrics collection.
    
    This is a placeholder for future integration with metrics systems like:
    - Prometheus
    - StatsD
    - CloudWatch
    - Datadog
    
    Currently stores metrics in memory for inspection.
    """
    
    def __init__(self):
        self.logger = get_logger("metrics")
        self.metrics: List[Dict[str, Any]] = []
        self._counters: Dict[str, int] = {}
        self._timers: Dict[str, List[float]] = {}
    
    def _increment(self, metric_name: str, value: int = 1):
        """Increment a counter metric."""
        self._counters[metric_name] = self._counters.get(metric_name, 0) + value
    
    def _record_timing(self, metric_name: str, elapsed: float):
        """Record a timing metric."""
        if metric_name not in self._timers:
            self._timers[metric_name] = []
        self._timers[metric_name].append(elapsed)
    
    def on_agent_start(self, agent_name: str, user_query: str, metadata: Optional[Dict[str, Any]] = None):
        self._increment(f"agent.{agent_name}.starts")
        self.logger.debug(f"Metric: agent.{agent_name}.starts += 1")
    
    def on_agent_complete(self, agent_name: str, response: str, elapsed: float, metadata: Optional[Dict[str, Any]] = None):
        self._increment(f"agent.{agent_name}.completions")
        self._record_timing(f"agent.{agent_name}.duration", elapsed)
        self.logger.debug(f"Metric: agent.{agent_name}.duration = {elapsed:.2f}s")
    
    def on_agent_error(self, agent_name: str, error: Exception, elapsed: float, metadata: Optional[Dict[str, Any]] = None):
        self._increment(f"agent.{agent_name}.errors")
        self._increment(f"agent.{agent_name}.errors.{type(error).__name__}")
        self.logger.debug(f"Metric: agent.{agent_name}.errors += 1")
    
    def on_tool_call(self, tool_name: str, arguments: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        self._increment(f"tool.{tool_name}.calls")
        self.logger.debug(f"Metric: tool.{tool_name}.calls += 1")
    
    def on_tool_result(self, tool_name: str, result: Any, elapsed: float, metadata: Optional[Dict[str, Any]] = None):
        self._record_timing(f"tool.{tool_name}.duration", elapsed)
        
        # Track success/failure based on result structure
        if isinstance(result, dict) and result.get("status") == "error":
            self._increment(f"tool.{tool_name}.errors")
        else:
            self._increment(f"tool.{tool_name}.successes")
        
        self.logger.debug(f"Metric: tool.{tool_name}.duration = {elapsed:.2f}s")
    
    def on_sub_agent_delegate(self, parent_agent: str, sub_agent: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        self._increment(f"delegation.{parent_agent}_to_{sub_agent}")
        self.logger.debug(f"Metric: delegation.{parent_agent}_to_{sub_agent} += 1")
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of collected metrics.
        
        Returns:
            Dictionary with counters and timing statistics
        """
        timing_stats = {}
        for metric_name, timings in self._timers.items():
            if timings:
                timing_stats[metric_name] = {
                    "count": len(timings),
                    "min": min(timings),
                    "max": max(timings),
                    "avg": sum(timings) / len(timings),
                    "total": sum(timings)
                }
        
        return {
            "counters": self._counters,
            "timings": timing_stats
        }
    
    def export_prometheus_format(self) -> str:
        """
        Export metrics in Prometheus text format.
        
        Returns:
            String formatted for Prometheus scraping
        """
        lines = []
        
        # Export counters
        for metric_name, value in self._counters.items():
            safe_name = metric_name.replace(".", "_")
            lines.append(f"# TYPE comfy_{safe_name} counter")
            lines.append(f"comfy_{safe_name} {value}")
        
        # Export timing summaries
        for metric_name, timings in self._timers.items():
            if timings:
                safe_name = metric_name.replace(".", "_")
                lines.append(f"# TYPE comfy_{safe_name}_seconds summary")
                lines.append(f"comfy_{safe_name}_seconds_sum {sum(timings)}")
                lines.append(f"comfy_{safe_name}_seconds_count {len(timings)}")
        
        return "\n".join(lines)


class FileLoggingCallback(AgentEventCallback):
    """
    Callback that appends events to a file.
    
    Useful for audit trails and post-mortem debugging.
    """
    
    def __init__(self, log_file: Path):
        """
        Args:
            log_file: Path to log file
        """
        self.log_file = log_file
        self.logger = get_logger("file_callback")
        
        # Ensure parent directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def _write_event(self, event: Dict[str, Any]):
        """Write event to log file as JSON line."""
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write to log file: {e}")
    
    def on_agent_start(self, agent_name: str, user_query: str, metadata: Optional[Dict[str, Any]] = None):
        self._write_event({
            "timestamp": datetime.now().isoformat(),
            "event": "agent_start",
            "agent": agent_name,
            "query": user_query,
            "metadata": metadata
        })
    
    def on_agent_complete(self, agent_name: str, response: str, elapsed: float, metadata: Optional[Dict[str, Any]] = None):
        self._write_event({
            "timestamp": datetime.now().isoformat(),
            "event": "agent_complete",
            "agent": agent_name,
            "response_length": len(response),
            "elapsed": elapsed,
            "metadata": metadata
        })
    
    def on_agent_error(self, agent_name: str, error: Exception, elapsed: float, metadata: Optional[Dict[str, Any]] = None):
        self._write_event({
            "timestamp": datetime.now().isoformat(),
            "event": "agent_error",
            "agent": agent_name,
            "error": str(error),
            "error_type": type(error).__name__,
            "elapsed": elapsed,
            "metadata": metadata
        })
    
    def on_tool_call(self, tool_name: str, arguments: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        self._write_event({
            "timestamp": datetime.now().isoformat(),
            "event": "tool_call",
            "tool": tool_name,
            "arguments": arguments,
            "metadata": metadata
        })
    
    def on_tool_result(self, tool_name: str, result: Any, elapsed: float, metadata: Optional[Dict[str, Any]] = None):
        self._write_event({
            "timestamp": datetime.now().isoformat(),
            "event": "tool_result",
            "tool": tool_name,
            "elapsed": elapsed,
            "metadata": metadata
        })
    
    def on_sub_agent_delegate(self, parent_agent: str, sub_agent: str, message: str, metadata: Optional[Dict[str, Any]] = None):
        self._write_event({
            "timestamp": datetime.now().isoformat(),
            "event": "sub_agent_delegate",
            "parent": parent_agent,
            "sub_agent": sub_agent,
            "message": message,
            "metadata": metadata
        })


__all__ = [
    "AgentEventCallback",
    "LoggingCallback",
    "MetricsCallback",
    "FileLoggingCallback"
]



