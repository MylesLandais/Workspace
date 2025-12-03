import pytest
from google.adk.evaluation.agent_evaluator import AgentEvaluator
import os

@pytest.mark.asyncio
async def test_blogger_agent_evaluation():
    """
    Runs the agent evaluation.
    """
    eval_results = await AgentEvaluator.evaluate(
        agent_module="blogger_agent.agent",
        eval_dataset_file_path_or_dir=os.path.join(os.path.dirname(__file__), "data", "blog_eval.test.json")
    )

    if eval_results:
        for result in eval_results:
            assert result.passed, f"Evaluation failed for {result.eval_set_path} with score {result.overall_score}"
