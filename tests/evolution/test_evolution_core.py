import pytest
from pathlib import Path
import os
import shutil
from src.openakita.core.shadow.enhanced import EnhancedShadowWorkspace

@pytest.fixture
def temp_workspace(tmp_path):
    workspace = tmp_path / "main_ws"
    workspace.mkdir()
    (workspace / "existing.txt").write_text("initial content")
    return workspace

@pytest.mark.asyncio
async def test_shadow_workspace_redirection(temp_workspace):
    """
    TDD Test 1: 验证文件写操作被重定向到影子路径，主工作区不受影响。
    """
    ws = EnhancedShadowWorkspace(base_path=temp_workspace, task_id="test_task")
    async with ws:
        shadow_file = ws.resolve_path("new_file.txt")
        shadow_file.parent.mkdir(parents=True, exist_ok=True)
        shadow_file.write_text("shadow content")

        assert shadow_file.exists()
        assert not (temp_workspace / "new_file.txt").exists()

@pytest.mark.asyncio
async def test_shadow_workspace_history_tracking(temp_workspace):
    """
    TDD Test 2: 验证能够记录文件操作历史。
    """
    ws = EnhancedShadowWorkspace(base_path=temp_workspace, task_id="test_task_2")
    async with ws:
        # 模拟工具调用记录
        ws.record_operation("write_file", "a.txt", content="v1")
        ws.record_operation("write_file", "a.txt", content="v2")

        history = ws.get_history()
        assert len(history) == 2
        assert history[0]["op"] == "write_file"
        assert history[1]["params"]["content"] == "v2"

@pytest.mark.asyncio
async def test_shadow_workspace_commit(temp_workspace):
    """
    TDD Test 3: 验证 commit 能将影子环境变更同步回主环境。
    """
    ws = EnhancedShadowWorkspace(base_path=temp_workspace, task_id="test_commit")
    async with ws:
        shadow_file = ws.resolve_path("b.txt")
        shadow_file.write_text("permanent content")
        await ws.commit()

    assert (temp_workspace / "b.txt").exists()
    assert (temp_workspace / "b.txt").read_text() == "permanent content"
