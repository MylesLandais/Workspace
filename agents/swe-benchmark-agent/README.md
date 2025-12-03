# SWE Benchmark Agent

## Overview

This agent is designed to show the basic principles for tackling software engineering problems from two prominent benchmarks: SWE-bench and TerminalBench. It is not meant to be a production ready implementation.

## Agent Details

| Feature | Description |
| --- | --- |
| **Interaction Type** | Autonomous |
| **Complexity**  | Advanced |
| **Agent Type**  | Single Agent |
| **Components**  | Tools: Shell |
| **Vertical**  | Software Engineering |

### Agent architecture:

The SWE Benchmark Agent uses a sophisticated orchestrator pattern:
- **Orchestrator**: Manages the agent lifecycle and coordinates tool execution
- **Environment**: Docker-based isolated execution environment (SWEBenchEnvironment or TerminalBenchEnvironment)
- **Tools**: File operations (read, edit, create), shell commands, and submission
- **Agent**: LLM-powered agent (Gemini) with built-in planner and thinking capabilities

The agent operates autonomously within the Docker environment, using shell commands and file operations to solve software engineering tasks.

## Setup and Installation

1.  **Prerequisites**

    *   Python 3.10+
    *   uv
        *   For dependency management and packaging. Please follow the
            instructions on the official
            [uv website](https://docs.astral.sh/uv/) for installation.

        ```bash
        curl -LsSf https://astral.sh/uv/install.sh | sh
        ```

    * A project on Google Cloud Platform
    * Google Cloud CLI
        *   For installation, please follow the instruction on the official
            [Google Cloud website](https://cloud.google.com/sdk/docs/install).

2.  **Installation**

    ```bash
    # Clone this repository.
    git clone https://github.com/google/adk-samples.git
    cd adk-samples/python/agents/swe-benchmark-agent
    # Install the package and dependencies.
    uv sync
    ```

3.  **Configuration**

    *   Set up Google Cloud credentials.

        *   You may set the following environment variables in your shell, or in
            a `.env` file instead.

        ```bash
        export GOOGLE_GENAI_USE_VERTEXAI=true
        export GOOGLE_CLOUD_PROJECT=<your-project-id>
        export GOOGLE_CLOUD_LOCATION=<your-project-location>
        ```


## Running Tests

For running tests and evaluation, install the extra dependencies:

```bash
uv sync --dev
```

Then the tests and evaluation can be run from the `swe-benchmark-agent` directory using
the `pytest` module:

```bash
uv run pytest tests
```

## Running Evaluations

The SWE Agent can be evaluated on both SWE-bench and TerminalBench benchmarks to measure its performance on real-world software engineering tasks.

### SWE-bench Evaluation

To run evaluation on the full SWE-bench Verified dataset:

```bash
uv run python -m swe_benchmark_agent.main --full-dataset --evaluate --max-workers 4
```

To evaluate on a specific number of instances (e.g., the first 10):

```bash
uv run python -m swe_benchmark_agent.main --instance-id-or-count 10 --evaluate
```

To evaluate on a single instance:

```bash
uv run python -m swe_benchmark_agent.main --instance-id-or-count django__django-12345 --evaluate
```

### TerminalBench Evaluation

To run evaluation on the full TerminalBench core dataset:

```bash
uv run python -m swe_benchmark_agent.main --dataset terminalbench --full-dataset --evaluate --max-workers 4
```

To evaluate on a specific number of tasks (e.g., the first 5):

```bash
uv run python -m swe_benchmark_agent.main --dataset terminalbench --instance-id-or-count 5 --evaluate
```

To evaluate on a single task:

```bash
uv run python -m swe_benchmark_agent.main --dataset terminalbench --instance-id-or-count blind-maze-explorer-5x5 --evaluate
```

## Customization

The SWE Agent can be customized to better suit your requirements. For example:

 1. **Use a different model:** You can change the model used by the agent by modifying the `main.py` file.
 2. **Add more tools:** You can add more tools to the agent to give it more capabilities.
 3. **Support more benchmarks:** You can add support for more benchmarks by creating a new environment and updating the `main.py` file.
