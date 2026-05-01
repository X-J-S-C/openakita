"""
安全申诉工具定义
"""

from .base import build_detail

SAFETY_TOOLS = [
    {
        "name": "submit_safety_appeal",
        "category": "System",
        "description": "Submit a structured safety appeal when an operation is blocked by AuditorNode. Use this to explain WHY the blocked action is necessary and how you will ensure safety.",
        "detail": build_detail(
            summary="提交安全申诉。当操作被审计节点拦截，但该操作对完成任务至关重要时使用。",
            scenarios=[
                "被 L0 规则拦截但确有必要的操作",
                "需要修改受保护目录下的非关键文件",
                "执行包含敏感词但逻辑正常的 shell 指令",
            ],
            params_desc={
                "target_action": "被拦截的原始操作（工具名及参数摘要）",
                "necessity_reasoning": "为什么该操作是完成任务所必须的？",
                "mitigation_measures": "你采取了哪些额外的安全措施（如：已在影子目录验证、仅修改特定行等）？",
            },
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "target_action": {"type": "string", "description": "被拦截的操作描述"},
                "necessity_reasoning": {"type": "string", "description": "必要性理由"},
                "mitigation_measures": {"type": "string", "description": "安全缓解措施"},
            },
            "required": ["target_action", "necessity_reasoning", "mitigation_measures"],
        },
    },
    {
        "name": "check_safety_policy",
        "category": "System",
        "description": "Simulate an operation (tool call or path access) to check if it would be blocked by AuditorNode or L0 rules. Useful for debugging safety boundaries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "要模拟的工具名"},
                "tool_input": {"type": "object", "description": "要模拟的输入参数"},
            },
            "required": ["tool_name", "tool_input"],
        },
    }
]
