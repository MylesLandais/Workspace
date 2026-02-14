"""
Debug and Logging Infrastructure for ComfyUI Agent

Provides structured logging, timing metrics, and event tracing for development
and production monitoring.

Usage:
    # Enable debug mode
    export COMFY_DEBUG=1
    
    # In code
    from agents.comfy.debug import get_logger, Timer, trace_agent_step
    
    logger = get_logger(__name__)
    logger.debug("Starting prompt enhancement")
    
    with Timer("prompt_enhancement") as timer:
        # ... code ...
        pass
    logger.info(f"Completed in {timer.elapsed:.2f}s")
"""

import os
import time
import logging
import functools
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager
from datetime import datetime


# Global debug flag from environment
DEBUG_ENABLED = os.getenv("COMFY_DEBUG", "0") == "1"


class ColoredFormatter(logging.Formatter):
    """Colored formatter for terminal output."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
        return super().format(record)


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for the ComfyUI agent.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(f"comfy.{name}")
    
    # Only configure if not already configured
    if not logger.handlers:
        level = logging.DEBUG if DEBUG_ENABLED else logging.INFO
        logger.setLevel(level)
        
        # Console handler with colors
        handler = logging.StreamHandler()
        handler.setLevel(level)
        
        formatter = ColoredFormatter(
            fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Prevent propagation to avoid duplicate logs
        logger.propagate = False
    
    return logger


class Timer:
    """
    Context manager for timing code execution.
    
    Usage:
        with Timer("operation_name") as timer:
            # ... code to time ...
            pass
        print(f"Elapsed: {timer.elapsed:.2f}s")
    """
    
    def __init__(self, name: str, logger: Optional[logging.Logger] = None):
        self.name = name
        self.logger = logger or get_logger("timer")
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed: float = 0.0
    
    def __enter__(self):
        self.start_time = time.time()
        if DEBUG_ENABLED:
            self.logger.debug(f"Starting: {self.name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time
        
        if exc_type is None:
            if DEBUG_ENABLED:
                self.logger.debug(f"Completed: {self.name} ({self.elapsed:.2f}s)")
        else:
            self.logger.error(f"Failed: {self.name} ({self.elapsed:.2f}s) - {exc_val}")
        
        return False  # Don't suppress exceptions


class StepTracer:
    """
    Tracks agent workflow steps for debugging.
    
    Usage:
        tracer = StepTracer()
        tracer.step("prompt_enhancement", "Enhancing user prompt")
        tracer.step("workflow_selection", "Selecting ComfyUI workflow")
        tracer.summary()
    """
    
    def __init__(self):
        self.steps: list[Dict[str, Any]] = []
        self.logger = get_logger("tracer")
        self.start_time = time.time()
    
    def step(self, step_name: str, description: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Record a workflow step.
        
        Args:
            step_name: Short identifier for the step
            description: Human-readable description
            metadata: Optional additional data
        """
        step_data = {
            "name": step_name,
            "description": description,
            "timestamp": datetime.now().isoformat(),
            "elapsed": time.time() - self.start_time,
            "metadata": metadata or {}
        }
        self.steps.append(step_data)
        
        if DEBUG_ENABLED:
            self.logger.debug(f"[{step_name}] {description}")
            if metadata:
                self.logger.debug(f"  Metadata: {metadata}")
    
    def summary(self) -> Dict[str, Any]:
        """
        Get a summary of all steps.
        
        Returns:
            Dictionary with step timeline and total elapsed time
        """
        total_elapsed = time.time() - self.start_time
        
        summary = {
            "total_steps": len(self.steps),
            "total_elapsed": total_elapsed,
            "steps": self.steps
        }
        
        if DEBUG_ENABLED:
            self.logger.debug(f"\n{'='*60}")
            self.logger.debug(f"Workflow Summary:")
            self.logger.debug(f"  Total Steps: {len(self.steps)}")
            self.logger.debug(f"  Total Time: {total_elapsed:.2f}s")
            for i, step in enumerate(self.steps, 1):
                self.logger.debug(f"  {i}. [{step['elapsed']:.2f}s] {step['name']}: {step['description']}")
            self.logger.debug(f"{'='*60}\n")
        
        return summary


def trace_agent_step(step_name: str):
    """
    Decorator to trace agent method execution.
    
    Usage:
        @trace_agent_step("prompt_enhancement")
        def enhance_prompt(prompt: str) -> str:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            with Timer(step_name, logger):
                result = func(*args, **kwargs)
            
            return result
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            
            start_time = time.time()
            if DEBUG_ENABLED:
                logger.debug(f"Starting: {step_name}")
            
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                if DEBUG_ENABLED:
                    logger.debug(f"Completed: {step_name} ({elapsed:.2f}s)")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Failed: {step_name} ({elapsed:.2f}s) - {e}")
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


# Module-level logger for this file
_logger = get_logger(__name__)

# Log initialization
if DEBUG_ENABLED:
    _logger.info("Debug mode enabled (COMFY_DEBUG=1)")
else:
    _logger.debug("Running in production mode (set COMFY_DEBUG=1 for verbose output)")


__all__ = [
    "get_logger",
    "Timer",
    "StepTracer",
    "trace_agent_step",
    "DEBUG_ENABLED"
]

