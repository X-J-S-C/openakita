import asyncio
import os
import shutil
import json
from pathlib import Path
from datetime import datetime
from openakita.core.agent import Agent
from openakita.config import settings
from openakita.core.shadow.enhanced import EnhancedShadowWorkspace

async def deep_validation():
    print(f"🚀 [Deep Validation] Starting Akita-Evo Stress Test | {datetime.now()}")

    # Setup test workspace
    test_root = Path("./data/deep_test_ws")
    if test_root.exists():
        shutil.rmtree(test_root)
    test_root.mkdir(parents=True, exist_ok=True)

    # 1. Shadow Workspace Integrity Test
    print("\n--- [Step 1] Shadow Workspace Integrity ---")
    task_id = "stress-test-001"
    ws = EnhancedShadowWorkspace(base_path=test_root, task_id=task_id)
    async with ws:
        # Simulate complex file operations
        for i in range(10):
            p = ws.resolve_path(f"dir_{i}/file_{i}.txt")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"content {i}")
            ws.record_operation("write_file", f"dir_{i}/file_{i}.txt", size=len(p.read_text()))

        # Verify isolation
        assert not (test_root / "dir_0").exists(), "Isolation leak: shadow file found in main workspace before commit"
        print("✅ Isolation confirmed.")

        # Verify trace tree
        tree = ws.generate_visual_tree()
        print(f"Visual Trace Tree:\n{tree}")
        assert "WRITE_FILE" in tree
        print("✅ Trace tree visualization generated.")

    # 2. Kernel & Agent Initialization
    print("\n--- [Step 2] Kernel Initialization ---")
    # Mocking brain for speed and cost, focusing on logic flow
    from unittest.mock import MagicMock, AsyncMock
    mock_brain = MagicMock()
    mock_brain.think = AsyncMock(return_value=MagicMock(content='{"name": "test-skill", "content": "instructions: do something"}'))

    agent = Agent() # This might need proper config in real env, but we check if it follows SPI
    from openakita.core.kernel.base import BaseKernel
    assert isinstance(agent, BaseKernel), "Agent does not implement BaseKernel SPI"
    print("✅ SPI Compliance verified.")

    # 3. Crystallizer Closed-Loop Test
    print("\n--- [Step 3] Crystallizer Self-Healing Logic ---")
    from openakita.evolution.crystallizer import SuccessCrystallizer
    crystallizer = SuccessCrystallizer(brain=mock_brain)

    # Simulate a "failure-then-success" scenario
    crystallizer.verify_skill = AsyncMock(side_effect=[False, True])
    mock_brain.think.side_effect = [
        AsyncMock(content='{"name": "broken-skill", "content": "bad"}'),
        AsyncMock(content='{"name": "fixed-skill", "content": "good"}')
    ]

    result = await crystallizer.crystallize("Fix the system", [{"tool_calls": [{"name": "mock", "id": "1"}]}])
    assert result.success, "Crystallizer failed to heal"
    assert mock_brain.think.call_count >= 2, "Crystallizer did not trigger healing loop"
    print("✅ Self-healing loop executed successfully.")

    # 4. Dashboard Accuracy Verification
    print("\n--- [Step 4] Dashboard Data Mapping ---")
    from openakita.utils.dashboard_renderer import generate_dashboard
    test_stats = {
        "total": 500,
        "by_type": {"fact": 200, "preference": 100, "skill": 100, "error": 50, "rule": 50},
        "by_priority": {"permanent": 100, "long_term": 300, "short_term": 100},
        "sessions_today": 15,
        "unprocessed_sessions": 2
    }
    plot_path = "data/plots/deep_validation_dashboard.png"
    Path("data/plots").mkdir(parents=True, exist_ok=True)
    generate_dashboard(test_stats, plot_path)
    assert Path(plot_path).exists(), "Dashboard PNG was not generated"
    print(f"✅ Dashboard generated at {plot_path}")

    print("\n--- [Summary] ---")
    print("🎉 Akita-Evo Deep Validation PASSED.")

if __name__ == "__main__":
    asyncio.run(deep_validation())
