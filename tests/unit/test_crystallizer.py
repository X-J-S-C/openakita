import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock
from src.openakita.evolution.crystallizer import SuccessCrystallizer

@pytest.fixture
def mock_brain():
    brain = MagicMock()
    brain.think = AsyncMock()
    return brain

@pytest.mark.asyncio
async def test_preprocess_trace():
    crystallizer = SuccessCrystallizer(brain=MagicMock())

    trace = [
        {
            "iteration": 1,
            "tool_calls": [
                {"id": "call_1", "name": "read_file", "input": {"path": "test.txt"}}
            ],
            "tool_results": [
                {"tool_use_id": "call_1", "result_content": "file content", "is_error": False}
            ]
        },
        {
            "iteration": 2,
            "tool_calls": [
                {"id": "call_2", "name": "error_tool", "input": {}}
            ],
            "tool_results": [
                {"tool_use_id": "call_2", "result_content": "error msg", "is_error": True}
            ]
        }
    ]

    processed = crystallizer._preprocess_trace(trace)

    assert len(processed) == 1
    assert processed[0]["tools"][0]["name"] == "read_file"
    assert "error_tool" not in [t["name"] for t in processed[0]["tools"]]

@pytest.mark.asyncio
async def test_crystallize_success(mock_brain, tmp_path):
    crystallizer = SuccessCrystallizer(brain=mock_brain, skills_dir=tmp_path)

    # 模拟 LLM 返回
    mock_brain.think.return_value.content = json.dumps({
        "name": "test-skill",
        "display_name": "测试技能",
        "description": "用于测试的技能",
        "content": "# Test Skill\nInstructions here."
    })

    trace = [{
        "iteration": 1,
        "tool_calls": [{"id": "c1", "name": "tool1", "input": {}}],
        "tool_results": [{"tool_use_id": "c1", "result_content": "ok", "is_error": False}]
    }]

    result = await crystallizer.crystallize("test task", trace)

    assert result.success is True
    assert result.skill_name == "test-skill"
    # 由于默认不开启 auto_approve，应该存入 pending 目录
    assert (crystallizer.pending_dir / "test-skill" / "SKILL.md").exists()
    assert "# Test Skill" in (crystallizer.pending_dir / "test-skill" / "SKILL.md").read_text()
