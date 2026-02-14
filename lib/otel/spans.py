"""Span helpers: @traced decorator and context managers."""

import asyncio
import functools
from typing import Optional, Callable

from opentelemetry import trace


def traced(span_name: Optional[str] = None) -> Callable:
    """Decorator that wraps a function in an OTel span.

    Usage:
        @traced("my-operation")
        def do_work(): ...

        @traced()
        async def do_async_work(): ...
    """

    def decorator(func: Callable) -> Callable:
        name = span_name or func.__name__

        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                tracer = trace.get_tracer(func.__module__ or "jupyter")
                with tracer.start_as_current_span(name):
                    return await func(*args, **kwargs)

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                tracer = trace.get_tracer(func.__module__ or "jupyter")
                with tracer.start_as_current_span(name):
                    return func(*args, **kwargs)

            return sync_wrapper

    return decorator
