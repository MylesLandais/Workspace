"""Tests for lib.otel module."""

import os
from unittest.mock import patch, MagicMock
import pytest

from lib.otel.tracing import get_tracer, setup_tracing
from lib.otel.metrics import get_meter, setup_metrics
from lib.otel.spans import traced


class TestTracing:
    """Test tracing setup and tracer factory."""

    def setup_method(self):
        import lib.otel.tracing as mod
        mod._initialized = False

    @patch("lib.otel.tracing.TracerProvider")
    @patch("lib.otel.tracing.trace")
    def test_setup_tracing_creates_provider(self, mock_trace, mock_provider_cls):
        mock_provider = MagicMock()
        mock_provider_cls.return_value = mock_provider

        setup_tracing(service_name="test-svc")

        mock_provider_cls.assert_called_once()
        mock_trace.set_tracer_provider.assert_called_once_with(mock_provider)

    @patch.dict(os.environ, {"OTEL_SERVICE_NAME": "my-service"}, clear=False)
    @patch("lib.otel.tracing.TracerProvider")
    @patch("lib.otel.tracing.trace")
    def test_setup_tracing_uses_env_service_name(self, mock_trace, mock_provider_cls):
        setup_tracing()
        mock_provider_cls.assert_called_once()

    @patch("lib.otel.tracing.trace")
    def test_get_tracer_returns_tracer(self, mock_trace):
        mock_tracer = MagicMock()
        mock_trace.get_tracer.return_value = mock_tracer

        tracer = get_tracer("test-module")

        mock_trace.get_tracer.assert_called_once_with("test-module")
        assert tracer is mock_tracer

    @patch("lib.otel.tracing.trace")
    def test_get_tracer_default_name(self, mock_trace):
        get_tracer()
        mock_trace.get_tracer.assert_called_once_with("jupyter")


class TestMetrics:
    """Test metrics setup and meter factory."""

    def setup_method(self):
        import lib.otel.metrics as mod
        mod._initialized = False

    @patch("lib.otel.metrics.metrics_api")
    @patch("lib.otel.metrics.MeterProvider")
    def test_setup_metrics_creates_provider(self, mock_provider_cls, mock_metrics_api):
        mock_provider = MagicMock()
        mock_provider_cls.return_value = mock_provider

        # Patch the prometheus import inside setup_metrics to avoid real SDK call
        with patch.dict("sys.modules", {
            "opentelemetry.exporter.prometheus": MagicMock()
        }):
            setup_metrics()

        mock_provider_cls.assert_called_once()
        mock_metrics_api.set_meter_provider.assert_called_once_with(mock_provider)

    @patch("lib.otel.metrics.metrics_api")
    def test_get_meter_returns_meter(self, mock_metrics_api):
        mock_meter = MagicMock()
        mock_metrics_api.get_meter.return_value = mock_meter

        meter = get_meter("test-meter")

        mock_metrics_api.get_meter.assert_called_once_with("test-meter")
        assert meter is mock_meter

    @patch("lib.otel.metrics.metrics_api")
    def test_get_meter_default_name(self, mock_metrics_api):
        get_meter()
        mock_metrics_api.get_meter.assert_called_once_with("jupyter")


class TestTracedDecorator:
    """Test the @traced decorator."""

    def test_traced_preserves_function_name(self):
        @traced("test-span")
        def my_func():
            return 42

        assert my_func.__name__ == "my_func"

    @patch("lib.otel.spans.trace")
    def test_traced_creates_span(self, mock_trace):
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_trace.get_tracer.return_value = mock_tracer

        @traced("my-span")
        def my_func():
            return 42

        result = my_func()

        assert result == 42
        mock_tracer.start_as_current_span.assert_called_once_with("my-span")

    @patch("lib.otel.spans.trace")
    def test_traced_uses_function_name_as_default_span(self, mock_trace):
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_trace.get_tracer.return_value = mock_tracer

        @traced()
        def another_func():
            return "ok"

        result = another_func()

        assert result == "ok"
        mock_tracer.start_as_current_span.assert_called_once_with("another_func")

    @patch("lib.otel.spans.trace")
    def test_traced_propagates_exception(self, mock_trace):
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_trace.get_tracer.return_value = mock_tracer

        @traced("failing-span")
        def bad_func():
            raise ValueError("boom")

        with pytest.raises(ValueError, match="boom"):
            bad_func()

    @patch("lib.otel.spans.trace")
    def test_traced_async_function(self, mock_trace):
        mock_tracer = MagicMock()
        mock_span = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(
            return_value=mock_span
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_trace.get_tracer.return_value = mock_tracer

        @traced("async-span")
        async def async_func():
            return "async-ok"

        import asyncio
        result = asyncio.get_event_loop().run_until_complete(async_func())
        assert result == "async-ok"
