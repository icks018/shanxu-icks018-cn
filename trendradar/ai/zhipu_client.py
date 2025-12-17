"""智谱AI客户端"""

import os
import logging
from typing import Optional, Dict, Any
from zhipuai import ZhipuAI

logger = logging.getLogger(__name__)


class ZhipuClient:
    """智谱AI客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化智谱AI客户端
        
        Args:
            api_key: API密钥，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.getenv("ZHIPU_API_KEY")
        if not self.api_key:
            raise ValueError("智谱AI API Key未配置")
        
        self.client = ZhipuAI(api_key=self.api_key)
    
    def generate_summary(self, content: str, title: str, max_length: int = 100) -> str:
        """生成新闻摘要
        
        Args:
            content: 新闻内容
            title: 新闻标题
            max_length: 摘要最大长度
            
        Returns:
            生成的摘要
        """
        try:
            prompt = f"""
请为以下新闻生成一个{max_length}字以内的精华摘要，要求：
1. 提取核心信息和关键要点
2. 语言简洁明了，适合视频文案
3. 突出新闻价值和影响
4. 不要包含"据报道"、"消息称"等冗余表述

标题：{title}
内容：{content[:1000]}

摘要："""

            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )
            
            summary = response.choices[0].message.content.strip()
            
            # 确保摘要长度不超过限制
            if len(summary) > max_length:
                summary = summary[:max_length-3] + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"生成摘要失败: {e}")
            # 降级处理：返回截断的原内容
            return content[:max_length-3] + "..." if len(content) > max_length else content
    
    def generate_title(self, content: str, original_title: str, max_length: int = 30) -> str:
        """生成优化标题
        
        Args:
            content: 新闻内容
            original_title: 原始标题
            max_length: 标题最大长度
            
        Returns:
            优化后的标题
        """
        try:
            prompt = f"""
请为以下新闻生成一个{max_length}字以内的吸引人标题，要求：
1. 突出核心关键词和亮点
2. 简洁有力，适合视频标题
3. 保留重要信息，去除冗余词汇
4. 符合中文表达习惯

原标题：{original_title}
内容概要：{content[:500]}

优化标题："""

            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=100,
                temperature=0.8
            )
            
            title = response.choices[0].message.content.strip()
            
            # 确保标题长度不超过限制
            if len(title) > max_length:
                title = title[:max_length-3] + "..."
            
            return title
            
        except Exception as e:
            logger.error(f"生成标题失败: {e}")
            # 降级处理：返回截断的原标题
            return original_title[:max_length-3] + "..." if len(original_title) > max_length else original_title
    
    def generate_tag(self, content: str, title: str) -> str:
        """生成话题标签
        
        Args:
            content: 新闻内容
            title: 新闻标题
            
        Returns:
            生成的标签（不含#号）
        """
        try:
            prompt = f"""
请为以下新闻生成1个最相关的话题标签，要求：
1. 3-8个字，简洁明了
2. 突出核心主题或关键词
3. 适合社交媒体传播
4. 只返回标签文字，不要#号

标题：{title}
内容：{content[:300]}

标签："""

            response = self.client.chat.completions.create(
                model="glm-4-flash",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.6
            )
            
            tag = response.choices[0].message.content.strip()
            
            # 清理标签格式
            tag = tag.replace("#", "").strip()
            
            return tag
            
        except Exception as e:
            logger.error(f"生成标签失败: {e}")
            # 降级处理：从标题提取关键词
            return self._extract_keyword_from_title(title)
    
    def _extract_keyword_from_title(self, title: str) -> str:
        """从标题提取关键词作为降级标签"""
        # 简单的关键词提取逻辑
        keywords = ["AI", "人工智能", "芯片", "GPU", "CPU", "手机", "游戏", "科技", "创业", "投资"]
        for keyword in keywords:
            if keyword in title:
                return keyword
        
        # 如果没有匹配的关键词，返回前几个字
        return title[:6] if len(title) >= 6 else title
