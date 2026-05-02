import pytest
from unittest.mock import MagicMock, AsyncMock
from src.openakita.evolution.crystallizer import SuccessCrystallizer

@pytest.fixture
def mock_brain():
    brain = MagicMock()
    brain.think = AsyncMock()
    return brain

@pytest.mark.asyncio
async def test_crystallizer_self_healing_flow(mock_brain):
    """
    TDD: 验证结晶器的自愈闭环。
    1. 模拟一个执行失败的场景。
    2. 验证 Crystallizer 是否会调用 LLM 进行修复。
    """
    crystallizer = SuccessCrystallizer(brain=mock_brain)

    # 模拟第一次生成了有问题的 SOP，第二次生成了修复后的 SOP
    mock_brain.think.side_effect = [
        AsyncMock(content='{"name": "test-skill", "content": "broken instruction"}'),
        AsyncMock(content='{"name": "test-skill", "content": "fixed instruction"}')
    ]

    # 我们需要模拟一个验证失败，然后触发自愈的过程
    # 这里我们通过 mock 一个 verify_skill 方法来实现（或者在实现中包含此逻辑）
    crystallizer.verify_skill = AsyncMock(side_effect=[False, True])

    result = await crystallizer.crystallize("test task", [{"tool_calls": [{"name": "test", "id": "1"}]}])

    assert result.success
    assert mock_brain.think.call_count >= 2
    assert crystallizer.verify_skill.call_count == 2
