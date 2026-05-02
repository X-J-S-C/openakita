import asyncio
from unittest.mock import MagicMock, AsyncMock
from openakita.evolution.crystallizer import SuccessCrystallizer

async def test_extreme_healing():
    print("🧠 [Stress] Testing Crystallizer Self-Healing Limits")
    mock_brain = MagicMock()
    mock_brain.think = AsyncMock()

    # Simulate a stubborn failure: fails 2 times, succeeds on 3rd
    mock_brain.think.side_effect = [
        AsyncMock(content='{"name": "fail-1", "content": "error"}'),
        AsyncMock(content='{"name": "fail-2", "content": "still error"}'),
        AsyncMock(content='{"name": "success", "content": "finally fixed"}')
    ]

    crystallizer = SuccessCrystallizer(brain=mock_brain)
    # Verification fails twice
    crystallizer.verify_skill = AsyncMock(side_effect=[False, False, True])

    result = await crystallizer.crystallize("Hard task", [{"tool_calls": []}])

    assert result.success
    assert "success" in result.skill_name
    print(f"✅ Extreme healing PASSED. Attempts taken: {mock_brain.think.call_count}")

if __name__ == "__main__":
    asyncio.run(test_extreme_healing())
