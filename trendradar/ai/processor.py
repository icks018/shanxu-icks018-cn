"""AI处理器"""

import logging
from typing import Dict, List, Any, Optional
from .zhipu_client import ZhipuClient

logger = logging.getLogger(__name__)


class AIProcessor:
    """AI智能处理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化AI处理器
        
        Args:
            config: AI配置字典
        """
        self.config = config
        self.enabled = config.get("enabled", False)
        self.provider = config.get("provider", "zhipu")
        self.summary_length = config.get("summary_length", 100)
        self.title_length = config.get("title_length", 30)
        self.tags_count = config.get("tags_count", 1)
        self.video_format = config.get("video_format", True)
        
        # 初始化AI客户端
        self.client = None
        if self.enabled:
            try:
                if self.provider == "zhipu":
                    self.client = ZhipuClient()
                else:
                    logger.warning(f"不支持的AI提供商: {self.provider}")
                    self.enabled = False
            except Exception as e:
                logger.error(f"初始化AI客户端失败: {e}")
                self.enabled = False
    
    def process_news_item(self, news_item: Dict[str, Any]) -> Dict[str, Any]:
        """处理单条新闻
        
        Args:
            news_item: 新闻项字典
            
        Returns:
            处理后的新闻项
        """
        if not self.enabled or not self.client:
            return news_item
        
        try:
            title = news_item.get("title", "")
            content = news_item.get("content", "") or news_item.get("description", "")
            
            # 生成AI处理后的内容
            ai_title = self.client.generate_title(content, title, self.title_length)
            ai_summary = self.client.generate_summary(content, title, self.summary_length)
            ai_tag = self.client.generate_tag(content, title)
            
            # 更新新闻项
            processed_item = news_item.copy()
            processed_item.update({
                "ai_title": ai_title,
                "ai_summary": ai_summary,
                "ai_tag": ai_tag,
                "original_title": title
            })
            
            return processed_item
            
        except Exception as e:
            logger.error(f"处理新闻项失败: {e}")
            return news_item
    
    def process_news_list(self, news_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量处理新闻列表
        
        Args:
            news_list: 新闻列表
            
        Returns:
            处理后的新闻列表
        """
        if not self.enabled:
            return news_list
        
        processed_list = []
        for i, news_item in enumerate(news_list):
            try:
                processed_item = self.process_news_item(news_item)
                processed_list.append(processed_item)
                
                # 添加进度日志
                if (i + 1) % 10 == 0:
                    logger.info(f"AI处理进度: {i + 1}/{len(news_list)}")
                    
            except Exception as e:
                logger.error(f"处理第{i+1}条新闻失败: {e}")
                processed_list.append(news_item)
        
        logger.info(f"AI处理完成，共处理 {len(processed_list)} 条新闻")
        return processed_list
    
    def categorize_news(self, news_list: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """将新闻按类别分组
        
        Args:
            news_list: 新闻列表
            
        Returns:
            按类别分组的新闻字典
        """
        categories = {
            "科技AI": [],
            "游戏娱乐": [],
            "硬件数码": []
        }
        
        # 定义分类关键词
        tech_keywords = ["AI", "人工智能", "机器学习", "大模型", "科技", "创业", "投资", "开源", "程序员", "算法"]
        game_keywords = ["游戏", "电竞", "Steam", "直播", "娱乐", "DOTA", "LOL", "王者", "原神", "米哈游"]
        hardware_keywords = ["芯片", "GPU", "CPU", "手机", "iPhone", "华为", "小米", "硬件", "数码", "平板"]
        
        for news_item in news_list:
            title = news_item.get("ai_title") or news_item.get("title", "")
            content = news_item.get("ai_summary") or news_item.get("content", "")
            text = title + " " + content
            
            # 分类逻辑
            if any(keyword in text for keyword in tech_keywords):
                categories["科技AI"].append(news_item)
            elif any(keyword in text for keyword in game_keywords):
                categories["游戏娱乐"].append(news_item)
            elif any(keyword in text for keyword in hardware_keywords):
                categories["硬件数码"].append(news_item)
            else:
                # 默认分到科技AI类
                categories["科技AI"].append(news_item)
        
        return categories
    
    def format_for_video(self, categorized_news: Dict[str, List[Dict[str, Any]]]) -> str:
        """格式化为视频友好格式
        
        Args:
            categorized_news: 按类别分组的新闻
            
        Returns:
            格式化后的文本
        """
        if not self.video_format:
            return self._format_traditional(categorized_news)
        
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        
        output_lines = []
        
        # 添加标题
        output_lines.append(f"📱 流沙聚·闪讯 | {today}")
        output_lines.append("━━━━━━━━━━━━━━━━━━━━")
        output_lines.append("")
        
        # 分类图标映射
        category_icons = {
            "科技AI": "🤖",
            "游戏娱乐": "🎮", 
            "硬件数码": "💻"
        }
        
        for category, news_list in categorized_news.items():
            if not news_list:
                continue
                
            icon = category_icons.get(category, "📰")
            output_lines.append(f"{icon} {category} ({len(news_list)}条)")
            output_lines.append("─" * 20)
            
            for news_item in news_list:
                # 使用AI处理后的内容
                title = news_item.get("ai_title") or news_item.get("title", "")
                summary = news_item.get("ai_summary") or news_item.get("content", "")[:100]
                tag = news_item.get("ai_tag") or "热点"
                url = news_item.get("url", "")
                source = news_item.get("source", "")
                
                output_lines.append(f"📱 {title}")
                output_lines.append(summary)
                output_lines.append(f"🔗 [{source}]({url})")
                output_lines.append(f"#{tag}")
                output_lines.append("")
            
            output_lines.append("")
        
        return "\n".join(output_lines)
    
    def _format_traditional(self, categorized_news: Dict[str, List[Dict[str, Any]]]) -> str:
        """传统格式化方式"""
        output_lines = []
        
        for category, news_list in categorized_news.items():
            if not news_list:
                continue
                
            output_lines.append(f"## {category}")
            
            for news_item in news_list:
                title = news_item.get("title", "")
                url = news_item.get("url", "")
                source = news_item.get("source", "")
                
                output_lines.append(f"- [{title}]({url}) - {source}")
            
            output_lines.append("")
        
        return "\n".join(output_lines)
