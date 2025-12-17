# coding=utf-8
"""
通知调度器模块

提供统一的通知分发接口。
支持所有通知渠道的多账号配置，使用 `;` 分隔多个账号。

使用示例:
    dispatcher = NotificationDispatcher(config, get_time_func, split_content_func)
    results = dispatcher.dispatch_all(report_data, report_type, ...)
"""

from typing import Any, Callable, Dict, List, Optional

from trendradar.core.config import (
    get_account_at_index,
    limit_accounts,
    parse_multi_account_config,
    validate_paired_configs,
)

from .senders import (
    send_to_bark,
    send_to_dingtalk,
    send_to_email,
    send_to_feishu,
    send_to_ntfy,
    send_to_slack,
    send_to_telegram,
    send_to_wework,
)


class NotificationDispatcher:
    """
    统一的多账号通知调度器

    将多账号发送逻辑封装，提供简洁的 dispatch_all 接口。
    内部处理账号解析、数量限制、配对验证等逻辑。
    """

    def __init__(
        self,
        config: Dict[str, Any],
        get_time_func: Callable,
        split_content_func: Callable,
    ):
        """
        初始化通知调度器

        Args:
            config: 完整的配置字典，包含所有通知渠道的配置
            get_time_func: 获取当前时间的函数
            split_content_func: 内容分批函数
        """
        self.config = config
        self.get_time_func = get_time_func
        self.split_content_func = split_content_func
        self.max_accounts = config.get("MAX_ACCOUNTS_PER_CHANNEL", 3)

    def dispatch_all(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict] = None,
        proxy_url: Optional[str] = None,
        mode: str = "daily",
        html_file_path: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        分发通知到所有已配置的渠道

        Args:
            report_data: 报告数据（由 prepare_report_data 生成）
            report_type: 报告类型（如 "当日汇总"、"实时增量"）
            update_info: 版本更新信息（可选）
            proxy_url: 代理 URL（可选）
            mode: 报告模式 (daily/current/incremental)
            html_file_path: HTML 报告文件路径（邮件使用）

        Returns:
            Dict[str, bool]: 每个渠道的发送结果，key 为渠道名，value 为是否成功
        """
        results = {}
        
        # 检查是否有AI处理的内容，优先使用AI格式化内容
        content_to_send = report_data
        if report_data.get("ai_processed") and report_data.get("ai_content"):
            print("🤖 使用AI智能处理后的内容进行推送")
            # 创建一个包含AI内容的新报告数据
            content_to_send = {
                **report_data,
                "ai_formatted_content": report_data["ai_content"]
            }

        # 飞书
        if self.config.get("FEISHU_WEBHOOK_URL"):
            results["feishu"] = self._send_feishu(
                content_to_send, report_type, update_info, proxy_url, mode
            )

        # 钉钉
        if self.config.get("DINGTALK_WEBHOOK_URL"):
            results["dingtalk"] = self._send_dingtalk(
                content_to_send, report_type, update_info, proxy_url, mode
            )

        # 企业微信
        if self.config.get("WEWORK_WEBHOOK_URL"):
            results["wework"] = self._send_wework(
                content_to_send, report_type, update_info, proxy_url, mode
            )

        # Telegram（需要配对验证）
        if self.config.get("TELEGRAM_BOT_TOKEN") and self.config.get("TELEGRAM_CHAT_ID"):
            results["telegram"] = self._send_telegram(
                content_to_send, report_type, update_info, proxy_url, mode
            )

        # ntfy（需要配对验证）
        if self.config.get("NTFY_SERVER_URL") and self.config.get("NTFY_TOPIC"):
            results["ntfy"] = self._send_ntfy(
                content_to_send, report_type, update_info, proxy_url, mode
            )

        # Bark
        if self.config.get("BARK_URL"):
            results["bark"] = self._send_bark(
                content_to_send, report_type, update_info, proxy_url, mode
            )

        # Slack
        if self.config.get("SLACK_WEBHOOK_URL"):
            results["slack"] = self._send_slack(
                content_to_send, report_type, update_info, proxy_url, mode
            )

        # 邮件（保持原有逻辑，已支持多收件人）
        if (
            self.config.get("EMAIL_FROM")
            and self.config.get("EMAIL_PASSWORD")
            and self.config.get("EMAIL_TO")
        ):
            results["email"] = self._send_email(report_type, html_file_path)

        return results

    def _send_to_multi_accounts(
        self,
        channel_name: str,
        config_value: str,
        send_func: Callable[..., bool],
        **kwargs,
    ) -> bool:
        """
        通用多账号发送逻辑

        Args:
            channel_name: 渠道名称（用于日志和账号数量限制提示）
            config_value: 配置值（可能包含多个账号，用 ; 分隔）
            send_func: 发送函数，签名为 (account, account_label=..., **kwargs) -> bool
            **kwargs: 传递给发送函数的其他参数

        Returns:
            bool: 任一账号发送成功则返回 True
        """
        accounts = parse_multi_account_config(config_value)
        if not accounts:
            return False

        accounts = limit_accounts(accounts, self.max_accounts, channel_name)
        results = []

        for i, account in enumerate(accounts):
            if account:
                account_label = f"账号{i+1}" if len(accounts) > 1 else ""
                result = send_func(account, account_label=account_label, **kwargs)
                results.append(result)

        return any(results) if results else False

    def _send_feishu(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
    ) -> bool:
        """发送到飞书（多账号）"""
        return self._send_to_multi_accounts(
            channel_name="飞书",
            config_value=self.config["FEISHU_WEBHOOK_URL"],
            send_func=lambda url, account_label: send_to_feishu(
                webhook_url=url,
                report_data=report_data,
                report_type=report_type,
                update_info=update_info,
                proxy_url=proxy_url,
                mode=mode,
                account_label=account_label,
                batch_size=self.config.get("FEISHU_BATCH_SIZE", 29000),
                batch_interval=self.config.get("BATCH_SEND_INTERVAL", 1.0),
                split_content_func=self.split_content_func,
                get_time_func=self.get_time_func,
            ),
        )

    def _send_dingtalk(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
    ) -> bool:
        """发送到钉钉（多账号）"""
        return self._send_to_multi_accounts(
            channel_name="钉钉",
            config_value=self.config["DINGTALK_WEBHOOK_URL"],
            send_func=lambda url, account_label: send_to_dingtalk(
                webhook_url=url,
                report_data=report_data,
                report_type=report_type,
                update_info=update_info,
                proxy_url=proxy_url,
                mode=mode,
                account_label=account_label,
                batch_size=self.config.get("DINGTALK_BATCH_SIZE", 20000),
                batch_interval=self.config.get("BATCH_SEND_INTERVAL", 1.0),
                split_content_func=self.split_content_func,
            ),
        )

    def _send_wework(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
    ) -> bool:
        """发送到企业微信（多账号）"""
        return self._send_to_multi_accounts(
            channel_name="企业微信",
            config_value=self.config["WEWORK_WEBHOOK_URL"],
            send_func=lambda url, account_label: send_to_wework(
                webhook_url=url,
                report_data=report_data,
                report_type=report_type,
                update_info=update_info,
                proxy_url=proxy_url,
                mode=mode,
                account_label=account_label,
                batch_size=self.config.get("MESSAGE_BATCH_SIZE", 4000),
                batch_interval=self.config.get("BATCH_SEND_INTERVAL", 1.0),
                msg_type=self.config.get("WEWORK_MSG_TYPE", "markdown"),
                split_content_func=self.split_content_func,
            ),
        )

    def _send_telegram(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
    ) -> bool:
        """发送到 Telegram（多账号，需验证 token 和 chat_id 配对）"""
        telegram_tokens = parse_multi_account_config(self.config["TELEGRAM_BOT_TOKEN"])
        telegram_chat_ids = parse_multi_account_config(self.config["TELEGRAM_CHAT_ID"])

        if not telegram_tokens or not telegram_chat_ids:
            return False

        # 验证配对
        valid, count = validate_paired_configs(
            {"bot_token": telegram_tokens, "chat_id": telegram_chat_ids},
            "Telegram",
            required_keys=["bot_token", "chat_id"],
        )
        if not valid or count == 0:
            return False

        # 限制账号数量
        telegram_tokens = limit_accounts(telegram_tokens, self.max_accounts, "Telegram")
        telegram_chat_ids = telegram_chat_ids[: len(telegram_tokens)]

        results = []
        for i in range(len(telegram_tokens)):
            token = telegram_tokens[i]
            chat_id = telegram_chat_ids[i]
            if token and chat_id:
                account_label = f"账号{i+1}" if len(telegram_tokens) > 1 else ""
                result = send_to_telegram(
                    bot_token=token,
                    chat_id=chat_id,
                    report_data=report_data,
                    report_type=report_type,
                    update_info=update_info,
                    proxy_url=proxy_url,
                    mode=mode,
                    account_label=account_label,
                    batch_size=self.config.get("MESSAGE_BATCH_SIZE", 4000),
                    batch_interval=self.config.get("BATCH_SEND_INTERVAL", 1.0),
                    split_content_func=self.split_content_func,
                )
                results.append(result)

        return any(results) if results else False

    def _send_ntfy(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
    ) -> bool:
        """发送到 ntfy（多账号，需验证 topic 和 token 配对）"""
        ntfy_server_url = self.config["NTFY_SERVER_URL"]
        ntfy_topics = parse_multi_account_config(self.config["NTFY_TOPIC"])
        ntfy_tokens = parse_multi_account_config(self.config.get("NTFY_TOKEN", ""))

        if not ntfy_server_url or not ntfy_topics:
            return False

        # 验证 token 和 topic 数量一致（如果配置了 token）
        if ntfy_tokens and len(ntfy_tokens) != len(ntfy_topics):
            print(
                f"❌ ntfy 配置错误：topic 数量({len(ntfy_topics)})与 token 数量({len(ntfy_tokens)})不一致，跳过 ntfy 推送"
            )
            return False

        # 限制账号数量
        ntfy_topics = limit_accounts(ntfy_topics, self.max_accounts, "ntfy")
        if ntfy_tokens:
            ntfy_tokens = ntfy_tokens[: len(ntfy_topics)]

        results = []
        for i, topic in enumerate(ntfy_topics):
            if topic:
                token = get_account_at_index(ntfy_tokens, i, "") if ntfy_tokens else ""
                account_label = f"账号{i+1}" if len(ntfy_topics) > 1 else ""
                result = send_to_ntfy(
                    server_url=ntfy_server_url,
                    topic=topic,
                    token=token,
                    report_data=report_data,
                    report_type=report_type,
                    update_info=update_info,
                    proxy_url=proxy_url,
                    mode=mode,
                    account_label=account_label,
                    batch_size=3800,
                    split_content_func=self.split_content_func,
                )
                results.append(result)

        return any(results) if results else False

    def _send_bark(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
    ) -> bool:
        """发送到 Bark（多账号）"""
        return self._send_to_multi_accounts(
            channel_name="Bark",
            config_value=self.config["BARK_URL"],
            send_func=lambda url, account_label: send_to_bark(
                bark_url=url,
                report_data=report_data,
                report_type=report_type,
                update_info=update_info,
                proxy_url=proxy_url,
                mode=mode,
                account_label=account_label,
                batch_size=self.config.get("BARK_BATCH_SIZE", 3600),
                batch_interval=self.config.get("BATCH_SEND_INTERVAL", 1.0),
                split_content_func=self.split_content_func,
            ),
        )

    def _send_slack(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict],
        proxy_url: Optional[str],
        mode: str,
    ) -> bool:
        """发送到 Slack（多账号）"""
        return self._send_to_multi_accounts(
            channel_name="Slack",
            config_value=self.config["SLACK_WEBHOOK_URL"],
            send_func=lambda url, account_label: send_to_slack(
                webhook_url=url,
                report_data=report_data,
                report_type=report_type,
                update_info=update_info,
                proxy_url=proxy_url,
                mode=mode,
                account_label=account_label,
                batch_size=self.config.get("SLACK_BATCH_SIZE", 4000),
                batch_interval=self.config.get("BATCH_SEND_INTERVAL", 1.0),
                split_content_func=self.split_content_func,
            ),
        )

    def _send_email(
        self,
        report_type: str,
        html_file_path: Optional[str],
    ) -> bool:
        """发送邮件（保持原有逻辑，已支持多收件人）"""
        return send_to_email(
            from_email=self.config["EMAIL_FROM"],
            password=self.config["EMAIL_PASSWORD"],
            to_email=self.config["EMAIL_TO"],
            report_type=report_type,
            html_file_path=html_file_path,
            custom_smtp_server=self.config.get("EMAIL_SMTP_SERVER", ""),
            custom_smtp_port=self.config.get("EMAIL_SMTP_PORT", ""),
            get_time_func=self.get_time_func,
        )
