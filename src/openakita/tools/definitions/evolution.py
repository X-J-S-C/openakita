"""
自进化工具定义
"""

from .base import build_detail

EVOLUTION_TOOLS = [
    {
        "name": "list_pending_skills",
        "category": "Evolution",
        "description": "List all crystallized skills that are currently awaiting user approval.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "approve_crystallized_skill",
        "category": "Evolution",
        "description": "Approve a pending skill and move it to the official skill library.",
        "detail": build_detail(
            summary="审核通过一个结晶出的新技能。",
            params_desc={"skill_name": "待审批的技能 ID (kebab-case)"},
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "skill_name": {"type": "string", "description": "技能 ID"},
            },
            "required": ["skill_name"],
        },
    },
    {
        "name": "reject_crystallized_skill",
        "category": "Evolution",
        "description": "Reject a pending skill and delete its data.",
        "input_schema": {
            "type": "object",
            "properties": {
                "skill_name": {"type": "string", "description": "技能 ID"},
            },
            "required": ["skill_name"],
        },
    }
]
