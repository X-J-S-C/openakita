"""
SimpHTML - 基于视觉显著性的 HTML 简化工具。
移植自 GenericAgent，用于极致压缩网页 Token 消耗。
"""

import logging
import re
from bs4 import BeautifulSoup, NavigableString

logger = logging.getLogger(__name__)

# JavaScript 核心逻辑：用于在浏览器端预处理 DOM，识别视觉显著性
JS_OPT_HTML = r'''
function optHTML(text_only=false) {
    function createEnhancedDOMCopy() {
      const nodeInfo = new WeakMap();
      const ignoreTags = ['SCRIPT', 'STYLE', 'NOSCRIPT', 'META', 'LINK', 'COLGROUP', 'COL', 'TEMPLATE', 'PARAM', 'SOURCE'];
      const ignoreIds = ['ljq-ind'];
      function cloneNode(sourceNode, keep=false) {
        if (sourceNode.nodeType === 8 ||
            (sourceNode.nodeType === 1 && (
              ignoreTags.includes(sourceNode.tagName) ||
              (sourceNode.id && ignoreIds.includes(sourceNode.id))
            ))) {
          return null;
        }
        if (sourceNode.nodeType === 3) return sourceNode.cloneNode(false);
        const clone = sourceNode.cloneNode(false);
        if ((sourceNode.tagName === 'INPUT' || sourceNode.tagName === 'TEXTAREA') && sourceNode.value) clone.setAttribute('value', sourceNode.value);
        if (sourceNode.tagName === 'INPUT' && (sourceNode.type === 'radio' || sourceNode.type === 'checkbox') && sourceNode.checked) clone.setAttribute('checked', '');
        else if (sourceNode.tagName === 'SELECT' && sourceNode.value) clone.setAttribute('data-selected', sourceNode.value);

        const isDropdown = sourceNode.classList?.contains('dropdown-menu') ||
                 /dropdown|menu/i.test(sourceNode.className) || sourceNode.getAttribute('role') === 'menu';
        const _ddItems = isDropdown ? sourceNode.querySelectorAll('a, button, [role="menuitem"], li').length : 0;
        const isSmallDropdown = _ddItems > 0 && _ddItems <= 7 && sourceNode.textContent.length < 500;

        const childNodes = [];
        for (const child of sourceNode.childNodes) {
          const childClone = cloneNode(child, keep || isSmallDropdown);
          if (childClone) childNodes.push(childClone);
        }

        // Shadow DOM 处理
        if (sourceNode.shadowRoot) {
          for (const shadowChild of sourceNode.shadowRoot.childNodes) {
            const shadowClone = cloneNode(shadowChild, keep);
            if (shadowClone) childNodes.push(shadowClone);
          }
        }

        const rect = sourceNode.getBoundingClientRect();
        const style = window.getComputedStyle(sourceNode);
        const area = (style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity) <= 0)?0:rect.width * rect.height;
        const isVisible = (rect.width > 1 && rect.height > 1 &&
                      style.display !== 'none' && style.visibility !== 'hidden' &&
                      parseFloat(style.opacity) > 0 &&
                      Math.abs(rect.left) < 5000 && Math.abs(rect.top) < 5000)
                      || isSmallDropdown;

        let info = { rect, area, isVisible, isSmallDropdown };

        const nonTextChildren = childNodes.filter(child => child.nodeType !== 3);
        const hasValidChildren = nonTextChildren.length > 0;
        nodeInfo.set(clone, info);

        if (info.isVisible || hasValidChildren || keep) {
          childNodes.forEach(child => clone.appendChild(child));
          return clone;
        }
        return null;
      }
      return { domCopy: cloneNode(document.body), getNodeInfo: node => nodeInfo.get(node) };
    }

    const { domCopy } = createEnhancedDOMCopy();
    if (text_only) return domCopy.textContent;
    return domCopy.outerHTML;
}
return optHTML();
'''

def optimize_html_for_tokens(html_content: str, max_chars: int = 30000) -> str:
    """
    对 HTML 进行深度清洗和截断，确保 Token 消耗在可控范围内。
    """
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, 'html.parser')

    # 1. 移除 SVG 和注释
    for svg in soup.find_all('svg'):
        svg.decompose()

    # 2. 移除所有 style 属性
    for tag in soup.find_all(True):
        tag.attrs.pop('style', None)
        # 简化长 URL 和 Data URI
        for attr in ['src', 'href', 'action']:
            if tag.has_attr(attr):
                val = str(tag[attr])
                if val.startswith('data:'):
                    tag[attr] = '__data_uri__'
                elif len(val) > 100:
                    tag[attr] = val[:50] + '...' + val[-10:]

        # 移除数据埋点等非必要属性
        for attr in list(tag.attrs.keys()):
            if attr.startswith('data-v-') or attr.startswith('data-track'):
                tag.attrs.pop(attr)

    # 3. 递归截断
    return str(smart_truncate(soup, max_chars))

def smart_truncate(soup, budget: int):
    """
    智能截断逻辑：优先保留结构，按比例分摊配额给子元素。
    """
    total = len(str(soup))
    if total <= budget:
        return soup

    kids = [c for c in soup.children if hasattr(c, 'name')]
    if not kids:
        return soup

    # 如果只有一个子元素，穿透
    if len(kids) == 1:
        return smart_truncate(kids[0], budget)

    # 简单策略：如果超出预算，保留前 70% 的子元素，并在末尾添加标记
    current_len = 0
    kept_kids = []
    for kid in kids:
        kid_str = str(kid)
        if current_len + len(kid_str) > budget * 0.9:
            break
        kept_kids.append(kid)
        current_len += len(kid_str)

    soup.clear()
    for k in kept_kids:
        soup.append(k)

    if len(kept_kids) < len(kids):
        marker = soup.new_tag("div")
        marker.string = f"... [TRUNCATED {len(kids) - len(kept_kids)} items for token efficiency]"
        soup.append(marker)

    return soup
