"""Main agent definitions for RPG Graph VTT."""

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
from .tools import (
    query_character_info,
    query_available_spells,
    query_class_features,
    query_multiclass_prerequisites,
    query_party_characters,
    validate_character_build,
)
from .prompt import GAME_MASTER_AGENT_PROMPT, CHARACTER_ASSISTANT_AGENT_PROMPT


def create_gm_agent(model_name: str = "gemini-2.0-flash-exp") -> LlmAgent:
    """
    Create a Game Master (GM) agent for querying D&D 5e rules.
    
    The GM agent acts as a rules arbitrator, answering questions about D&D 5e
    mechanics by querying the Neo4j graph database.
    
    Args:
        model_name: LLM model to use
    
    Returns:
        Configured LlmAgent instance
    """
    tools = [
        FunctionTool(
            query_character_info,
            name="query_character_info",
            description="Query character information by name from the Neo4j database"
        ),
        FunctionTool(
            query_available_spells,
            name="query_available_spells",
            description="Query spells available to a class at a given level"
        ),
        FunctionTool(
            query_class_features,
            name="query_class_features",
            description="Query features available to a class at a given level"
        ),
        FunctionTool(
            query_multiclass_prerequisites,
            name="query_multiclass_prerequisites",
            description="Query multiclass prerequisites for a class"
        ),
        FunctionTool(
            query_party_characters,
            name="query_party_characters",
            description="Query all characters in a party"
        ),
    ]
    
    agent = LlmAgent(
        model=model_name,
        tools=tools,
        instructions=GAME_MASTER_AGENT_PROMPT
    )
    
    return agent


# Alias for backward compatibility
create_rules_lookup_agent = create_gm_agent


def create_character_assistant_agent(model_name: str = "gemini-2.0-flash-exp") -> LlmAgent:
    """
    Create a Character Assistant Agent for helping with character creation.
    
    Args:
        model_name: LLM model to use
    
    Returns:
        Configured LlmAgent instance
    """
    tools = [
        FunctionTool(
            query_character_info,
            name="query_character_info",
            description="Query character information by name"
        ),
        FunctionTool(
            query_available_spells,
            name="query_available_spells",
            description="Query spells available to a class at a given level"
        ),
        FunctionTool(
            query_class_features,
            name="query_class_features",
            description="Query features available to a class at a given level"
        ),
        FunctionTool(
            query_multiclass_prerequisites,
            name="query_multiclass_prerequisites",
            description="Query multiclass prerequisites for a class"
        ),
        FunctionTool(
            validate_character_build,
            name="validate_character_build",
            description="Validate a character build against D&D 5e rules"
        ),
    ]
    
    agent = LlmAgent(
        model=model_name,
        tools=tools,
        instructions=CHARACTER_ASSISTANT_AGENT_PROMPT
    )
    
    return agent

