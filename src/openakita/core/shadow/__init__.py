from .enhanced import EnhancedShadowWorkspace
from .legacy import is_shadow_eligible

# 为了向后兼容，将 EnhancedShadowWorkspace 导出为 ShadowWorkspace
ShadowWorkspace = EnhancedShadowWorkspace

__all__ = ["ShadowWorkspace", "EnhancedShadowWorkspace", "is_shadow_eligible"]
