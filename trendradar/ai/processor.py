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
        print(f"🔍 AIProcessor初始化，config = {config}")
        self.config = config
        self.enabled = config.get("enabled", False)
        self.provider = config.get("provider", "zhipu")
        self.summary_length = config.get("summary_length", 150)
        self.title_length = config.get("title_length", 30)
        self.tags_count = config.get("tags_count", 1)
        self.video_format = config.get("video_format", True)
        self.generate_script = config.get("generate_script", True)
        self.generate_storyboard = config.get("generate_storyboard", True)
        
        print(f"🔍 AI配置: enabled={self.enabled}, provider={self.provider}")
        
        # 初始化AI客户端
        self.client = None
        if self.enabled:
            try:
                print(f"🔍 尝试初始化{self.provider}客户端...")
                if self.provider == "zhipu":
                    self.client = ZhipuClient()
                    print("✅ ZhipuClient初始化成功")
                else:
                    print(f"❌ 不支持的AI提供商: {self.provider}")
                    logger.warning(f"不支持的AI提供商: {self.provider}")
                    self.enabled = False
            except Exception as e:
                print(f"❌ 初始化AI客户端失败: {e}")
                logger.error(f"初始化AI客户端失败: {e}")
                self.enabled = False
        else:
            print("❌ AI处理未启用")
    
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
    
    def format_for_video(self, categorized_news: Dict[str, List[Dict]]) -> str:
        """将分类新闻格式化为视频友好的文本
        
        Args:
            categorized_news: 分类后的新闻数据
            
        Returns:
            格式化后的视频文本
        """
        if not categorized_news:
            return "暂无新闻内容"
        
        result = {}
        
        # 生成基础格式化内容
        formatted_text = self._generate_basic_format(categorized_news)
        result["basic_format"] = formatted_text
        
        # 生成完整视频稿子
        if self.generate_script:
            video_script = self._generate_video_script(categorized_news)
            result["video_script"] = video_script
        
        # 生成分镜脚本
        if self.generate_storyboard:
            storyboard = self._generate_storyboard(categorized_news)
            result["storyboard"] = storyboard
        
        # 返回组合内容
        return self._combine_all_formats(result)
    
    def _generate_basic_format(self, categorized_news: Dict[str, List[Dict]]) -> str:
        """生成基础格式化内容"""
        formatted_text = "📺 今日科技热点播报\n\n"
        
        # 按分类顺序处理
        category_order = ["科技AI类", "游戏娱乐类", "硬件数码类"]
        
        for category in category_order:
            if category in categorized_news and categorized_news[category]:
                formatted_text += f"🔸 {category}\n"
                
                for i, news in enumerate(categorized_news[category], 1):
                    title = news.get("ai_title", news.get("title", ""))
                    summary = news.get("ai_summary", "")
                    tag = news.get("ai_tag", "")
                    url = news.get("url", "")
                    
                    formatted_text += f"{i}. {title}\n"
                    if summary:
                        formatted_text += f"   {summary}\n"
                    if tag:
                        formatted_text += f"   标签: {tag}\n"
                    if url:
                        formatted_text += f"   链接: {url}\n"
                    formatted_text += "\n"
                
                formatted_text += "\n"
        
        return formatted_text
    
    def _generate_video_script(self, categorized_news: Dict[str, List[Dict]]) -> str:
        """生成完整视频播报稿"""
        script = "🎬 视频播报稿\n\n"
        script += "大家好，欢迎收看今日科技热点播报。我是您的AI主播，为您带来最新的科技资讯。\n\n"
        
        category_order = ["科技AI类", "游戏娱乐类", "硬件数码类"]
        category_intros = {
            "科技AI类": "首先，让我们关注人工智能和科技创新领域的最新动态。",
            "游戏娱乐类": "接下来，我们来看看游戏娱乐行业的热门资讯。", 
            "硬件数码类": "最后，让我们了解一下硬件数码市场的最新消息。"
        }
        
        for category in category_order:
            if category in categorized_news and categorized_news[category]:
                script += f"【{category}】\n"
                script += f"{category_intros[category]}\n\n"
                
                for i, news in enumerate(categorized_news[category], 1):
                    title = news.get("ai_title", news.get("title", ""))
                    summary = news.get("ai_summary", "")
                    
                    script += f"第{i}条新闻：{title}\n"
                    if summary:
                        script += f"{summary}\n"
                    script += "\n"
                
                script += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        script += "以上就是今日的科技热点播报，感谢您的收看，我们明天同一时间再见！\n"
        
        return script
    
    def _generate_storyboard(self, categorized_news: Dict[str, List[Dict]]) -> str:
        """生成分镜脚本"""
        storyboard = "🎥 分镜脚本\n\n"
        
        # 开场
        storyboard += "【镜头1】开场 (0:00-0:05)\n"
        storyboard += "画面：主播正面特写，背景为科技感十足的虚拟演播室\n"
        storyboard += "文案：大家好，欢迎收看今日科技热点播报\n"
        storyboard += "转场：淡入淡出\n\n"
        
        category_order = ["科技AI类", "游戏娱乐类", "硬件数码类"]
        category_visuals = {
            "科技AI类": "AI芯片、机器人、代码界面等科技元素",
            "游戏娱乐类": "游戏画面、手柄、电竞场景等娱乐元素",
            "硬件数码类": "手机、电脑、芯片等硬件产品"
        }
        
        time_offset = 5  # 开场5秒后开始
        
        for category_idx, category in enumerate(category_order, 2):
            if category in categorized_news and categorized_news[category]:
                news_count = len(categorized_news[category])
                segment_duration = min(30, news_count * 8)  # 每条新闻约8秒，最多30秒
                
                start_time = time_offset
                end_time = time_offset + segment_duration
                
                storyboard += f"【镜头{category_idx}】{category} ({start_time//60}:{start_time%60:02d}-{end_time//60}:{end_time%60:02d})\n"
                storyboard += f"画面：{category_visuals[category]}\n"
                storyboard += f"内容：播报{news_count}条{category}新闻\n"
                storyboard += "转场：滑动切换\n\n"
                
                time_offset = end_time
        
        # 结尾
        end_start = time_offset
        end_end = time_offset + 5
        storyboard += f"【镜头{len(category_order)+2}】结尾 ({end_start//60}:{end_start%60:02d}-{end_end//60}:{end_end%60:02d})\n"
        storyboard += "画面：主播挥手告别，显示订阅提醒\n"
        storyboard += "文案：感谢收看，明天同一时间再见\n"
        storyboard += "转场：淡出\n\n"
        
        storyboard += f"总时长：约{end_end//60}分{end_end%60:02d}秒\n"
        
        return storyboard
    
    def _combine_all_formats(self, result: Dict[str, str]) -> str:
        """组合所有格式化内容"""
        combined = ""
        
        if "basic_format" in result:
            combined += result["basic_format"] + "\n"
        
        if "video_script" in result:
            combined += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            combined += result["video_script"] + "\n"
        
        if "storyboard" in result:
            combined += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            combined += result["storyboard"]
        
        return combined
    
    def _format_traditional(self, categorized_news: Dict[str, List[Dict]]) -> str:
        """传统格式化方法（兼容性保留）"""
        
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
