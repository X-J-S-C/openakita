import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import networkx as nx
import numpy as np
from pathlib import Path
from datetime import datetime

def generate_dashboard(stats: dict, output_path: str):
    """
    根据记忆统计数据生成 PNG 仪表盘。
    """
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(16, 10))
    fig.patch.set_facecolor('#0f172a')

    gs = gridspec.GridSpec(2, 3, figure=fig)

    # 1. 记忆类型分布 (Pie Chart)
    ax1 = fig.add_subplot(gs[0, 0])
    labels = list(stats['by_type'].keys())
    values = list(stats['by_type'].values())
    colors = ['#3b82f6', '#ec4899', '#f59e0b', '#10b981', '#8b5cf6', '#ef4444']
    ax1.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=140, textprops={'color':"w"})
    ax1.set_title("Memory Distribution", fontsize=14, pad=20)

    # 2. 优先级分布 (Bar Chart)
    ax2 = fig.add_subplot(gs[0, 1])
    p_labels = list(stats['by_priority'].keys())
    p_values = list(stats['by_priority'].values())
    ax2.bar(p_labels, p_values, color='#3b82f6', alpha=0.8)
    ax2.set_title("Priority Distribution", fontsize=14)
    ax2.grid(axis='y', alpha=0.3)

    # 3. 总览数据 (Text)
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.axis('off')
    summary_text = (
        f"OpenAkita System Status\n\n"
        f"Total Memories: {stats['total']}\n"
        f"Sessions Today: {stats['sessions_today']}\n"
        f"Unprocessed: {stats['unprocessed_sessions']}\n"
        f"Crystallized SOPs: {stats.get('sops_count', 0)}\n"
        f"Generation Time: {datetime.now().strftime('%H:%M:%S')}"
    )
    ax3.text(0.1, 0.5, summary_text, fontsize=16, color='white', fontweight='bold', va='center')

    # 4. 关系网络预览 (Graph)
    ax4 = fig.add_subplot(gs[1, :2])
    G = nx.fast_gnp_random_graph(20, 0.15) # 模拟真实图数据
    pos = nx.spring_layout(G)
    nx.draw(G, pos, ax=ax4, node_size=100, node_color='#818cf8', edge_color='#334155', with_labels=False)
    ax4.set_title("Knowledge Graph Network", fontsize=14)

    # 5. 活动时间线 (Timeline simulation)
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.axis('off')
    ax5.set_title("Recent Activity", fontsize=14)
    activities = stats.get('recent_activities', ["Task A completed", "SOP B crystallized", "User preference learned", "Memory consolidated"])
    for i, act in enumerate(activities[:5]):
        ax5.text(0.05, 0.8 - i*0.15, f"• {act}", fontsize=12, color='#94a3b8')

    plt.tight_layout(pad=3.0)
    plt.savefig(output_path, dpi=120, facecolor='#0f172a')
    plt.close()
    return output_path

if __name__ == "__main__":
    # Test call
    test_stats = {
        "total": 309,
        "by_type": {"fact": 143, "preference": 51, "rule": 28, "skill": 25, "experience": 25, "error": 10},
        "by_priority": {"permanent": 72, "long_term": 171, "short_term": 66},
        "sessions_today": 8,
        "unprocessed_sessions": 0,
        "sops_count": 12
    }
    generate_dashboard(test_stats, "data/memory_graph_test.png")
