import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from openakita.evolution.crystallizer import SuccessCrystallizer

@pytest.mark.asyncio
async def test_crystallize_success():
    # Mock brain
    mock_brain = MagicMock()
    mock_brain.think = AsyncMock()

    # Mock response
    mock_response = MagicMock()
    mock_response.content = json.dumps({
        "name": "test-skill",
        "content": "--- \nname: test-skill\ndescription: A test skill\n---\n\n# Test Skill\n\nInstructions: do something."
    })
    mock_brain.think.return_value = mock_response

    # Temp skills dir
    temp_skills_dir = Path("./temp_test_skills")
    temp_skills_dir.mkdir(exist_ok=True)

    crystallizer = SuccessCrystallizer(brain=mock_brain, skills_dir=temp_skills_dir)

    task_desc = "Testing crystallization"
    trace = [
        {
            "iteration": 1,
            "tool_calls": [{"id": "call_1", "name": "read_file", "input": {"path": "test.txt"}}],
            "tool_results": [{"tool_use_id": "call_1", "result_content": "file content", "is_error": False}]
        }
    ]

    result = await crystallizer.crystallize(task_desc, trace)

    assert result.success is True
    assert result.skill_name == "test-skill"
    assert (temp_skills_dir / "test-skill" / "SKILL.md").exists()

    # Cleanup
    import shutil
    shutil.rmtree(temp_skills_dir)

@pytest.mark.asyncio
async def test_preprocess_trace():
    mock_brain = MagicMock()
    crystallizer = SuccessCrystallizer(brain=mock_brain)

    trace = [
        {
            "iteration": 1,
            "tool_calls": [
                {"id": "call_1", "name": "ls", "input": {"path": "."}},
                {"id": "call_2", "name": "error_tool", "input": {}}
            ],
            "tool_results": [
                {"tool_use_id": "call_1", "result_content": "file1\nfile2", "is_error": False},
                {"tool_use_id": "call_2", "result_content": "error message", "is_error": True}
            ]
        }
    ]

    processed = crystallizer._preprocess_trace(trace)

    assert len(processed) == 1
    assert len(processed[0]["tools"]) == 1
    assert processed[0]["tools"][0]["name"] == "ls"
