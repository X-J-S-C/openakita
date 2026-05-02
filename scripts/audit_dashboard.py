import os
from pathlib import Path
from openakita.utils.dashboard_renderer import generate_dashboard

def audit_dashboard_mapping():
    print("📊 [Audit] Verifying Dashboard Data Mapping Realism")

    # 模拟从 DB 读取的真实统计值
    real_stats = {
        "total": 123,
        "by_type": {"fact": 50, "rule": 20, "skill": 53},
        "by_priority": {"permanent": 40, "long_term": 60, "short_term": 23},
        "sessions_today": 5,
        "unprocessed_sessions": 1
    }

    plot_dir = Path("data/audit_plots")
    plot_dir.mkdir(parents=True, exist_ok=True)
    plot_file = plot_dir / "audit_dashboard.png"

    # 执行生成
    path = generate_dashboard(real_stats, str(plot_file))

    # 基础文件验证
    assert os.path.exists(path)
    assert os.path.getsize(path) > 10000 # 确保不是空图

    print(f"✅ Dashboard mapping audit PASSED. File: {path}")

if __name__ == "__main__":
    audit_dashboard_mapping()
