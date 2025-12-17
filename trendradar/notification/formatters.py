# coding=utf-8
"""
通知内容格式转换模块

提供不同推送平台间的格式转换功能
"""

import re


def format_ai_content_for_platform(ai_content: str, platform: str) -> str:
    """
    将AI生成的内容格式化为特定平台格式
    
    Args:
        ai_content: AI生成的格式化内容
        platform: 目标平台 (feishu/dingtalk/wework/telegram/etc.)
        
    Returns:
        适配平台的格式化内容
    """
    if not ai_content:
        return ""
    
    # 不同平台的格式适配
    if platform in ["feishu", "dingtalk"]:
        # 飞书和钉钉支持markdown格式，保持原样
        return ai_content
    elif platform == "wework":
        # 企业微信根据消息类型决定
        return ai_content
    elif platform == "telegram":
        # Telegram支持markdown，保持原样
        return ai_content
    elif platform in ["bark", "ntfy"]:
        # 移动推送平台，简化格式
        return strip_markdown(ai_content)
    else:
        # 默认保持原格式
        return ai_content


def strip_markdown(text: str) -> str:
    """去除文本中的 markdown 语法格式，用于个人微信推送

    Args:
        text: 包含 markdown 格式的文本

    Returns:
        纯文本内容
    """
    # 去除粗体 **text** 或 __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)

    # 去除斜体 *text* 或 _text_
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)

    # 去除删除线 ~~text~~
    text = re.sub(r'~~(.+?)~~', r'\1', text)

    # 转换链接 [text](url) -> text url（保留 URL）
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1 \2', text)

    # 去除图片 ![alt](url) -> alt
    text = re.sub(r'!\[(.+?)\]\(.+?\)', r'\1', text)

    # 去除行内代码 `code`
    text = re.sub(r'`(.+?)`', r'\1', text)

    # 去除引用符号 >
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)

    # 去除标题符号 # ## ### 等
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)

    # 去除水平分割线 --- 或 ***
    text = re.sub(r'^[\-\*]{3,}\s*$', '', text, flags=re.MULTILINE)

    # 去除 HTML 标签 <font color='xxx'>text</font> -> text
    text = re.sub(r'<font[^>]*>(.+?)</font>', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)

    # 清理多余的空行（保留最多两个连续空行）
    text = re.sub(r'\n{3,}', '\n\n', text)

    return text.strip()


def convert_markdown_to_mrkdwn(content: str) -> str:
    """
    将标准 Markdown 转换为 Slack 的 mrkdwn 格式

    转换规则：
    - **粗体** → *粗体*
    - [文本](url) → <url|文本>
    - 保留其他格式（代码块、列表等）

    Args:
        content: Markdown 格式的内容

    Returns:
        Slack mrkdwn 格式的内容
    """
    # 1. 转换链接格式: [文本](url) → <url|文本>
    content = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<\2|\1>', content)

    # 2. 转换粗体: **文本** → *文本*
    content = re.sub(r'\*\*([^*]+)\*\*', r'*\1*', content)

    return content
