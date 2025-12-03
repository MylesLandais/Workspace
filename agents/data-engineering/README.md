# Data Engineering Agent

A comprehensive data engineering agent.

## Features

-   **Dataform Pipeline Development**

    -   Build and modify Dataform pipelines
    -   Create and update SQLx files
    -   Handle UDFs and stored procedures integration
    -   Manage table schemas and data types

-   **Dataform Troubleshooting**

    -   Diagnose pipeline issues
    -   Analyze execution logs
    -   Fix compilation errors
    -   Optimize pipeline performance

-   **Data Engineering**

    -   Design and implement data transformations
    -   Handle complex SQL queries
    -   Manage data dependencies
    -   Ensure data quality

## Installation


## Setup and Installation

1.  **Prerequisites**

    *   Python 3.11+
    *   Poetry
        *   For dependency management and packaging. Please follow the
            instructions on the official
            [Poetry website](https://python-poetry.org/docs/) for installation.

        ```bash
        pip install poetry
        ```

    * A project on Google Cloud Platform
    * Google Cloud CLI
        *   For installation, please follow the instruction on the official
            [Google Cloud website](https://cloud.google.com/sdk/docs/install).

2.  **Installation**

    ```bash
    # Clone this repository.
    git clone https://github.com/google/adk-samples.git
    cd adk-samples/python/agents/data-engineering

    # Install the package and dependencies.
    poetry install
    ```

3.  **Configuration** 

   Create a `.env` file in the project root directory: `cp .env.example
    .env`

   Edit the `.env` file with your configuration:

```
    GOOGLE_CLOUD_PROJECT=your-project-id
    GOOGLE_CLOUD_LOCATION=us-central1

    # Used for Vertex AI, Dataform, and BigQuery GOOGLE_GENAI_USE_VERTEXAI=1
    # Model Configuration

    ROOT_AGENT_MODEL=gemini-2.5-pro

    # Dataform Configuration

    DATAFORM_REPOSITORY_NAME=your-repository-name

    DATAFORM_WORKSPACE_NAME=your-workspace-name
```

### Environment Variables

-   `GOOGLE_CLOUD_PROJECT`: Your Google Cloud Project ID (preferred) or use
    `GCP_PROJECT_ID`
-   `GOOGLE_CLOUD_LOCATION`: Location for Vertex AI, Dataform, and BigQuery
    (default: us-central1)
-   `GOOGLE_GENAI_USE_VERTEXAI`: Set to 1 to use Vertex AI (default: 0)
-   `ROOT_AGENT_MODEL`: Model to use for the root agent (default:
    gemini-2.5-pro)
-   `DATAFORM_REPOSITORY_NAME`: Your Dataform repository name
-   `DATAFORM_WORKSPACE_NAME`: Your Dataform workspace name

### Running the Agent
   Run ADK from the upper folder: `cd .. adk web` or
   `adk run`

### Example
    # Prompt
    Enrich the `new_york_taxi_trips.tlc_green_trips_2022` table by generating date and time features from the `pickup_datetime` column. Use `new_york_taxi_trips` dataset for the enriched table.

    # Agent Response
    Of course. I will enrich the tlc_green_trips_2022 table by creating a new table with additional date and time features from the pickup_datetime column.

    First, I need to get information about the existing table to ensure I have the correct column names and data types.

    I have created a new table named enriched_trips in the new_york_taxi_trips dataset. This table includes the original data from tlc_green_trips_2022 plus the following new columns:

    pickup_date: The date of the pickup.
    pickup_day_of_week: The day of the week of the pickup (e.g., Sunday, Monday).
    pickup_hour_of_day: The hour of the day of the pickup.
    I have also added the declaration file for the source table.

    I will now compile the project to view the DAG.

    I have successfully compiled the Dataform project. The compilation was successful, and I have the pipeline's DAG.

## Running Tests

For running tests and evaluation, install the extra dependencies:

```bash
poetry install --with dev
```

Then the tests and evaluation can be run from the `financial-advisor` directory using
the `pytest` module:

```bash
python3 -m pytest tests
python3 -m pytest eval
```

`tests` runs the agent on a sample request, and makes sure that every component
is functional. `eval` is a demonstration of how to evaluate the agent, using the
`AgentEvaluator` in ADK. It sends a couple requests to the agent and expects
that the agent's responses match a pre-defined response reasonably well.

## Deployment

The Financial Advisor can be deployed to Vertex AI Agent Engine using the following
commands:

```bash
poetry install --with deployment
python3 deployment/deploy.py --create
```

When the deployment finishes, it will print a line like this:

```
Created remote agent: projects/<PROJECT_NUMBER>/locations/<PROJECT_LOCATION>/reasoningEngines/<AGENT_ENGINE_ID>
```

If you forgot the AGENT_ENGINE_ID, you can list existing agents using:

```bash
python3 deployment/deploy.py --list
```

The output will be like:

```
All remote agents:

123456789 ("data_engineering_agent")
- Create time: 2025-08-05 12:35:34.245431+00:00
- Update time: 2025-08-05 12:36:01.421432+00:00
```

You may interact with the deployed agent using the `test_deployment.py` script
```bash
$ export USER_ID=<any string>
$ python3 deployment/test_deployment.py --resource_id=${AGENT_ENGINE_ID} --user_id=${USER_ID}
Found agent with resource ID: ...
Created session for user ID: ...
Type 'quit' to exit.
Input: Hello, what can you do for me?
Response: 
```

To delete the deployed agent, you may run the following command:

```bash
python3 deployment/deploy.py --delete --resource_id=${AGENT_ENGINE_ID}
```

# License
   Copyright 2025 Google LLC

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
