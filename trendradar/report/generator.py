# coding=utf-8
"""
报告生成模块

提供报告数据准备和 HTML 生成功能：
- prepare_report_data: 准备报告数据
- generate_html_report: 生成 HTML 报告
"""

from pathlib import Path
from typing import Dict, List, Optional, Callable
import os
import logging

# 导入AI处理器
try:
    from ..ai.processor import AIProcessor
except ImportError:
    AIProcessor = None

logger = logging.getLogger(__name__)


def prepare_report_data(
    stats: List[Dict],
    failed_ids: Optional[List] = None,
    new_titles: Optional[Dict] = None,
    id_to_name: Optional[Dict] = None,
    mode: str = "daily",
    rank_threshold: int = 3,
    matches_word_groups_func: Optional[Callable] = None,
    load_frequency_words_func: Optional[Callable] = None,
    ai_config: Optional[Dict] = None,
) -> Dict:
    """
    准备报告数据

    Args:
        stats: 统计结果列表
        failed_ids: 失败的 ID 列表
        new_titles: 新增标题
        id_to_name: ID 到名称的映射
        mode: 报告模式 (daily/incremental/current)
        rank_threshold: 排名阈值
        matches_word_groups_func: 词组匹配函数
        load_frequency_words_func: 加载频率词函数
        ai_config: AI处理配置

    Returns:
        Dict: 准备好的报告数据
    """
    # 初始化AI处理器
    ai_processor = None
    print(f"🔍 调试信息: ai_config = {ai_config}")
    print(f"🔍 调试信息: AIProcessor = {AIProcessor}")
    
    if ai_config and AIProcessor:
        try:
            print("🔍 开始初始化AI处理器...")
            ai_processor = AIProcessor(ai_config)
            print(f"🔍 AI处理器创建完成，enabled = {ai_processor.enabled}")
            if ai_processor.enabled:
                print("✅ AI智能处理已启用")
                logger.info("AI智能处理已启用")
            else:
                print("❌ AI智能处理未启用")
        except Exception as e:
            print(f"❌ 初始化AI处理器失败: {e}")
            logger.error(f"初始化AI处理器失败: {e}")
    else:
        print(f"❌ AI配置或处理器不可用: ai_config={bool(ai_config)}, AIProcessor={bool(AIProcessor)}")
    
    processed_new_titles = []

    # 在增量模式下隐藏新增新闻区域
    hide_new_section = mode == "incremental"

    # 只有在非隐藏模式下才处理新增新闻部分
    if not hide_new_section:
        filtered_new_titles = {}
        if new_titles and id_to_name:
            # 如果提供了匹配函数，使用它过滤
            if matches_word_groups_func and load_frequency_words_func:
                word_groups, filter_words, global_filters = load_frequency_words_func()
                for source_id, titles_data in new_titles.items():
                    filtered_titles = {}
                    for title, title_data in titles_data.items():
                        if matches_word_groups_func(title, word_groups, filter_words, global_filters):
                            filtered_titles[title] = title_data
                    if filtered_titles:
                        filtered_new_titles[source_id] = filtered_titles
            else:
                # 没有匹配函数时，使用全部
                filtered_new_titles = new_titles

            # 打印过滤后的新增热点数（与推送显示一致）
            original_new_count = sum(len(titles) for titles in new_titles.values()) if new_titles else 0
            filtered_new_count = sum(len(titles) for titles in filtered_new_titles.values()) if filtered_new_titles else 0
            if original_new_count > 0:
                print(f"频率词过滤后：{filtered_new_count} 条新增热点匹配（原始 {original_new_count} 条）")

        if filtered_new_titles and id_to_name:
            for source_id, titles_data in filtered_new_titles.items():
                source_name = id_to_name.get(source_id, source_id)
                source_titles = []

                for title, title_data in titles_data.items():
                    url = title_data.get("url", "")
                    mobile_url = title_data.get("mobileUrl", "")
                    ranks = title_data.get("ranks", [])

                    processed_title = {
                        "title": title,
                        "source_name": source_name,
                        "time_display": "",
                        "count": 1,
                        "ranks": ranks,
                        "rank_threshold": rank_threshold,
                        "url": url,
                        "mobile_url": mobile_url,
                        "is_new": True,
                    }
                    source_titles.append(processed_title)

                if source_titles:
                    processed_new_titles.append(
                        {
                            "source_id": source_id,
                            "source_name": source_name,
                            "titles": source_titles,
                        }
                    )

    processed_stats = []
    for stat in stats:
        if stat["count"] <= 0:
            continue

        processed_titles = []
        for title_data in stat["titles"]:
            processed_title = {
                "title": title_data["title"],
                "source_name": title_data["source_name"],
                "time_display": title_data["time_display"],
                "count": title_data["count"],
                "ranks": title_data["ranks"],
                "rank_threshold": title_data["rank_threshold"],
                "url": title_data.get("url", ""),
                "mobile_url": title_data.get("mobileUrl", ""),
                "is_new": title_data.get("is_new", False),
            }
            processed_titles.append(processed_title)

        processed_stats.append(
            {
                "word": stat["word"],
                "count": stat["count"],
                "percentage": stat.get("percentage", 0),
                "titles": processed_titles,
            }
        )

    # AI智能处理
    if ai_processor and ai_processor.enabled:
        logger.info("开始AI智能处理...")
        
        # 收集所有新闻数据进行AI处理
        all_news_items = []
        
        # 处理统计数据中的新闻
        for stat in processed_stats:
            for title_data in stat["titles"]:
                news_item = {
                    "title": title_data["title"],
                    "content": title_data.get("content", ""),
                    "url": title_data.get("url", ""),
                    "source": title_data.get("source_name", ""),
                    "keyword": stat["word"]
                }
                all_news_items.append(news_item)
        
        # 处理新增新闻
        for source in processed_new_titles:
            for title_data in source["titles"]:
                news_item = {
                    "title": title_data["title"],
                    "content": title_data.get("content", ""),
                    "url": title_data.get("url", ""),
                    "source": title_data.get("source_name", ""),
                    "keyword": "新增热点"
                }
                all_news_items.append(news_item)
        
        # 执行AI处理
        if all_news_items:
            processed_news = ai_processor.process_news_list(all_news_items)
            categorized_news = ai_processor.categorize_news(processed_news)
            
            # 如果启用视频格式，生成格式化内容
            if ai_processor.video_format:
                formatted_content = ai_processor.format_for_video(categorized_news)
                logger.info("AI处理完成，生成视频友好格式")
                
                # 将AI处理结果添加到返回数据中
                return {
                    "stats": processed_stats,
                    "new_titles": processed_new_titles,
                    "failed_ids": failed_ids or [],
                    "total_new_count": sum(
                        len(source["titles"]) for source in processed_new_titles
                    ),
                    "ai_processed": True,
                    "ai_content": formatted_content,
                    "ai_categories": categorized_news,
                }

    return {
        "stats": processed_stats,
        "new_titles": processed_new_titles,
        "failed_ids": failed_ids or [],
        "total_new_count": sum(
            len(source["titles"]) for source in processed_new_titles
        ),
    }


def generate_html_report(
    stats: List[Dict],
    total_titles: int,
    failed_ids: Optional[List] = None,
    new_titles: Optional[Dict] = None,
    id_to_name: Optional[Dict] = None,
    mode: str = "daily",
    is_daily_summary: bool = False,
    update_info: Optional[Dict] = None,
    rank_threshold: int = 3,
    output_dir: str = "output",
    date_folder: str = "",
    time_filename: str = "",
    render_html_func: Optional[Callable] = None,
    matches_word_groups_func: Optional[Callable] = None,
    load_frequency_words_func: Optional[Callable] = None,
    enable_index_copy: bool = True,
    ai_config: Optional[Dict] = None,
) -> str:
    """
    生成 HTML 报告

    Args:
        stats: 统计结果列表
        total_titles: 总标题数
        failed_ids: 失败的 ID 列表
        new_titles: 新增标题
        id_to_name: ID 到名称的映射
        mode: 报告模式 (daily/incremental/current)
        is_daily_summary: 是否是每日汇总
        update_info: 更新信息
        rank_threshold: 排名阈值
        output_dir: 输出目录
        date_folder: 日期文件夹名称
        time_filename: 时间文件名
        render_html_func: HTML 渲染函数
        matches_word_groups_func: 词组匹配函数
        load_frequency_words_func: 加载频率词函数
        enable_index_copy: 是否复制到 index.html

    Returns:
        str: 生成的 HTML 文件路径
    """
    if is_daily_summary:
        if mode == "current":
            filename = "当前榜单汇总.html"
        elif mode == "incremental":
            filename = "当日增量.html"
        else:
            filename = "当日汇总.html"
    else:
        filename = f"{time_filename}.html"

    # 构建输出路径
    output_path = Path(output_dir) / date_folder / "html"
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = str(output_path / filename)

    # 准备报告数据
    report_data = prepare_report_data(
        stats,
        failed_ids,
        new_titles,
        id_to_name,
        mode,
        rank_threshold,
        matches_word_groups_func,
        load_frequency_words_func,
        ai_config,
    )

    # 渲染 HTML 内容
    if render_html_func:
        html_content = render_html_func(
            report_data, total_titles, is_daily_summary, mode, update_info
        )
    else:
        # 默认简单 HTML
        html_content = f"<html><body><h1>Report</h1><pre>{report_data}</pre></body></html>"

    # 写入文件
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    # 如果是每日汇总且启用 index 复制
    if is_daily_summary and enable_index_copy:
        # 生成到根目录（供 GitHub Pages 访问）
        root_index_path = Path("index.html")
        with open(root_index_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        # 同时生成到 output 目录（供 Docker Volume 挂载访问）
        output_index_path = Path(output_dir) / "index.html"
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        with open(output_index_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    return file_path
