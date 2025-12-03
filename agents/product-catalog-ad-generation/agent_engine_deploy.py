# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Deployment script for the BigQuery Agent."""

import os
import vertexai
from absl import app, flags
from dotenv import load_dotenv

# --- Step 1: Import your BigQuery agent ---
from content_gen_agent.agent import root_agent

from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP Cloud Storage bucket for staging.")
flags.DEFINE_string("resource_id", None, "ReasoningEngine resource ID for deletion.")

flags.DEFINE_bool("list", False, "List all deployed agent engines.")
flags.DEFINE_bool("create", False, "Creates a new agent engine.")
flags.DEFINE_bool("delete", False, "Deletes an existing agent engine.")
flags.mark_bool_flags_as_mutual_exclusive(["create", "delete", "list"])


# --- Step 2: Define environment variables for the deployed agent ---
load_dotenv()

env_vars = {
    "GOOGLE_CLOUD_PROJECT_ID": os.getenv("GOOGLE_CLOUD_PROJECT_ID"),
    "GCS_BUCKET": os.getenv("GCS_BUCKET"),
    "GCP_PROJECT": os.getenv("GCP_PROJECT"), 
    "GOOGLE_CLOUD_LOCATION_REGION": os.getenv("GOOGLE_CLOUD_LOCATION_REGION"),
    "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY")
    #"GOOGLE_GENAI_USE_VERTEXAI": "true",
}


def create() -> None:
    """Creates and deploys an agent engine for the BigQuery Agent."""
    print("Creating AdkApp wrapper for the agent...")
    adk_app = AdkApp(agent=root_agent, enable_tracing=True)

    # --- Step 3: Define Python package requirements ---
    requirements = [
    "absolufy-imports==0.3.1",
    "aiohappyeyeballs==2.6.1",
    "aiohttp==3.12.15",
    "aiosignal==1.4.0",
    "alembic==1.16.5",
    "annotated-types==0.7.0",
    "anyio==4.10.0",
    "asttokens==3.0.0",
    "attrs==25.3.0",
    "Authlib==1.6.3",
    "cachetools==5.5.2",
    "certifi==2025.8.3",
    "cffi==1.17.1",
    "charset-normalizer==3.4.3",
    "click==8.2.1",
    "cloudpickle==3.1.1",
    "cryptography==45.0.7",
    "db-dtypes==1.4.3",
    "decorator==5.2.1",
    "Deprecated==1.2.18",
    "docstring_parser==0.17.0",
    "executing==2.2.1",
    "fastapi==0.116.1",
    "frozenlist==1.7.0",
    "google-adk==1.13.0",
    "google-api-core==2.25.1",
    "google-api-python-client==2.181.0",
    "google-auth==2.40.3",
    "google-auth-httplib2==0.2.0",
    "google-cloud-aiplatform==1.111.0",
    "google-cloud-appengine-logging==1.6.2",
    "google-cloud-audit-log==0.3.2",
    "google-cloud-bigquery==3.36.0",
    "google-cloud-bigtable==2.32.0",
    "google-cloud-core==2.4.3",
    "google-cloud-discoveryengine==0.13.11",
    "google-cloud-logging==3.12.1",
    "google-cloud-resource-manager==1.14.2",
    "google-cloud-secret-manager==2.24.0",
    "google-cloud-spanner==3.57.0",
    "google-cloud-speech==2.33.0",
    "google-cloud-storage==2.19.0",
    "google-cloud-trace==1.16.2",
    "google-crc32c==1.7.1",
    "google-genai==1.33.0",
    "google-resumable-media==2.7.2",
    "googleapis-common-protos==1.70.0",
    "graphviz==0.21",
    "greenlet==3.2.4",
    "grpc-google-iam-v1==0.14.2",
    "grpc-interceptor==0.15.4",
    "grpcio==1.74.0",
    "grpcio-status==1.74.0",
    "h11==0.16.0",
    "httpcore==1.0.9",
    "httplib2==0.30.0",
    "httpx==0.28.1",
    "httpx-sse==0.4.1",
    "idna==3.10",
    "imageio==2.37.0",
    "imageio-ffmpeg==0.6.0",
    "importlib_metadata==8.7.0",
    "ipython==9.5.0",
    "ipython_pygments_lexers==1.1.1",
    "jedi==0.19.2",
    "jsonpatch==1.33",
    "jsonpointer==3.0.0",
    "jsonschema==4.25.1",
    "jsonschema-specifications==2025.4.1",
    "langchain==0.3.27",
    "langchain-core==0.3.75",
    "langchain-text-splitters==0.3.11",
    "langsmith==0.4.23",
    "Mako==1.3.10",
    "MarkupSafe==3.0.2",
    "matplotlib-inline==0.1.7",
    "mcp==1.13.1",
    "moviepy==2.2.1",
    "multidict==6.6.4",
    "numpy==2.3.2",
    "opentelemetry-api==1.36.0",
    "opentelemetry-exporter-gcp-trace==1.9.0",
    "opentelemetry-resourcedetector-gcp==1.9.0a0",
    "opentelemetry-sdk==1.36.0",
    "opentelemetry-semantic-conventions==0.57b0",
    "orjson==3.11.3",
    "packaging==25.0",
    "pandas==2.3.2",
    "parso==0.8.5",
    "pexpect==4.9.0",
    "pillow==11.3.0",
    "proglog==0.1.12",
    "prompt_toolkit==3.0.52",
    "propcache==0.3.2",
    "proto-plus==1.26.1",
    "protobuf==6.32.0",
    "ptyprocess==0.7.0",
    "pure_eval==0.2.3",
    "pyarrow==21.0.0",
    "pyasn1==0.6.1",
    "pyasn1_modules==0.4.2",
    "pycparser==2.22",
    "pydantic==2.11.7",
    "pydantic-settings==2.10.1",
    "pydantic_core==2.33.2",
    "Pygments==2.19.2",
    "pyparsing==3.2.3",
    "python-dateutil==2.9.0.post0",
    "python-dotenv==1.1.1",
    "python-multipart==0.0.20",
    "pytz==2025.2",
    "PyYAML==6.0.2",
    "referencing==0.36.2",
    "requests==2.32.5",
    "requests-toolbelt==1.0.0",
    "rpds-py==0.27.1",
    "rsa==4.9.1",
    "shapely==2.1.1",
    "six==1.17.0",
    "sniffio==1.3.1",
    "SQLAlchemy==2.0.43",
    "sqlalchemy-spanner==1.16.0",
    "sqlparse==0.5.3",
    "sse-starlette==3.0.2",
    "stack-data==0.6.3",
    "starlette==0.47.3",
    "tenacity==8.5.0",
    "toolbox-core==0.5.0",
    "tqdm==4.67.1",
    "traitlets==5.14.3",
    "typing-inspection==0.4.1",
    "typing_extensions==4.15.0",
    "tzdata==2025.2",
    "tzlocal==5.3.1",
    "uritemplate==4.2.0",
    "urllib3==2.5.0",
    "uvicorn==0.35.0",
    "watchdog==6.0.0",
    "wcwidth==0.2.13",
    "websockets==15.0.1",
    "wrapt==1.17.3",
    "yarl==1.20.1",
    "zipp==3.23.0",
    "zstandard==0.24.0",
    "pytest",
    "pytest-asyncio",
    "pluggy",
    "iniconfig"
    ]

    print(f"Deploying agent with display name: {root_agent.name}")
    remote_agent = agent_engines.create(
        adk_app,
        display_name=root_agent.name,
        requirements=requirements,
        extra_packages=["content_gen_agent"],
        description="An agent that creates short form video based on generated product images.",
        env_vars=env_vars,
    )
    print(f"Successfully created remote agent: {remote_agent.resource_name}")
    print("You can now interact with this agent via its resource name in your applications.")


def delete(resource_id: str) -> None:
    """Deletes an existing agent engine."""
    print(f"Attempting to delete agent: {resource_id}")
    remote_agent = agent_engines.get(resource_id)
    remote_agent.delete(force=True)
    print(f"Successfully deleted remote agent: {resource_id}")


def list_agents() -> None:
    """Lists all deployed agent engines in the project and location."""
    print("Listing all deployed agents...")
    remote_agents = agent_engines.list()
    if not remote_agents:
        print("No agents found.")
        return

    template_lines = [
        '{agent.name} ("{agent.display_name}")',
        '- Create time: {agent.create_time}',
        '- Update time: {agent.update_time}',
        '- Description: {agent.description}',
    ]
    template = "\n".join(template_lines)

    remote_agents_string = "\n\n".join(
        template.format(agent=agent) for agent in remote_agents
    )
    print(f"\nAll remote agents:\n{remote_agents_string}")


def main(argv: list[str]) -> None:
    del argv  # unused

    project_id = (
        FLAGS.project_id
        if FLAGS.project_id
        else os.getenv("GOOGLE_CLOUD_PROJECT_ID")
    )
    # --- THIS LINE IS THE FIX ---
    # Corrected the typo from GOOGLE_CLOUD_LOCATION_REGION_REGION to GOOGLE_CLOUD_LOCATION_REGION
    location = (
        FLAGS.location if FLAGS.location else os.getenv("GOOGLE_CLOUD_LOCATION_REGION")
    )
    bucket = (
        FLAGS.bucket
        if FLAGS.bucket
        else os.getenv("GOOGLE_CLOUD_STORAGE_BUCKET")
    )

    print(f"Using Project ID: {project_id}")
    print(f"Using Location:   {location}")
    print(f"Using Staging Bucket: gs://{bucket}")

    if not all([project_id, location, bucket]):
        print(
            "Error: Missing required configuration. Please set GOOGLE_CLOUD_PROJECT_ID, "
            "GOOGLE_CLOUD_LOCATION_REGION, and GOOGLE_CLOUD_STORAGE_BUCKET environment "
            "variables (in your .env file) or pass them as flags (--project_id, --location, --bucket)."
        )
        return

    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=f"gs://{bucket}",
    )

    if FLAGS.list:
        list_agents()
    elif FLAGS.create:
        create()
    elif FLAGS.delete:
        if not FLAGS.resource_id:
            print("Error: --resource_id is required for the delete operation.")
            return
        delete(FLAGS.resource_id)
    else:
        print("No command specified. Use --create, --delete, or --list.")


if __name__ == "__main__":
    app.run(main)

