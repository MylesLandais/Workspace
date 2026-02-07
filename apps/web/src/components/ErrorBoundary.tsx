"use client";

/**
 * Error Boundary Component
 *
 * Catches React errors with detailed logging and provides user-friendly error display.
 * In development, shows full error details. In production, shows generic error message.
 */

import React, { Component, ErrorInfo, ReactNode } from "react";
import { createLogger } from "@/lib/debug/logger";

const log = createLogger("error-boundary");

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    log.error("React error caught by boundary", error, {
      componentStack: errorInfo.componentStack,
    });

    this.setState({
      error,
      errorInfo,
    });
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      const isDev = process.env.NODE_ENV === "development";

      return (
        <div className="min-h-screen bg-[#0a0a0a] flex items-center justify-center p-4">
          <div className="max-w-2xl w-full space-y-6">
            <div className="text-center space-y-4">
              <h1 className="text-6xl font-bold text-red-500">Error</h1>
              <p className="text-zinc-400 text-lg">
                {isDev
                  ? "An error occurred while rendering this component"
                  : "Something went wrong. Please refresh the page."}
              </p>
            </div>

            {isDev && this.state.error && (
              <div className="bg-zinc-900 border border-red-500/20 rounded-lg p-6 space-y-4">
                <div>
                  <h2 className="text-red-400 font-semibold mb-2">
                    Error Message:
                  </h2>
                  <pre className="text-sm text-zinc-300 bg-black/50 p-3 rounded overflow-x-auto">
                    {this.state.error.message}
                  </pre>
                </div>

                {this.state.error.stack && (
                  <div>
                    <h2 className="text-red-400 font-semibold mb-2">
                      Stack Trace:
                    </h2>
                    <pre className="text-xs text-zinc-400 bg-black/50 p-3 rounded overflow-x-auto max-h-64 overflow-y-auto">
                      {this.state.error.stack}
                    </pre>
                  </div>
                )}

                {this.state.errorInfo && (
                  <div>
                    <h2 className="text-red-400 font-semibold mb-2">
                      Component Stack:
                    </h2>
                    <pre className="text-xs text-zinc-400 bg-black/50 p-3 rounded overflow-x-auto max-h-64 overflow-y-auto">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  </div>
                )}
              </div>
            )}

            <div className="flex justify-center gap-4">
              <button
                onClick={() => window.location.reload()}
                className="px-6 py-3 bg-white text-black rounded-lg hover:bg-zinc-200 transition-colors"
              >
                Reload Page
              </button>
              <button
                onClick={() =>
                  this.setState({
                    hasError: false,
                    error: null,
                    errorInfo: null,
                  })
                }
                className="px-6 py-3 bg-zinc-800 text-white rounded-lg hover:bg-zinc-700 transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
