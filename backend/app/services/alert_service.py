# app/services/alert_service.py

import smtplib
import asyncio
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from datetime import datetime

from app.core.config import settings
from app.core.logging import logger

class AlertService:
    def __init__(self):
        # 提供默認值，避免設置文件缺失時的錯誤
        self.email_config = {
            'smtp_server': getattr(settings, 'SMTP_SERVER', 'localhost'),
            'smtp_port': getattr(settings, 'SMTP_PORT', 587),
            'username': getattr(settings, 'SMTP_USERNAME', ''),
            'password': getattr(settings, 'SMTP_PASSWORD', ''),
            'from_email': getattr(settings, 'ALERT_FROM_EMAIL', 'alerts@localhost')
        }
        self.slack_webhook = getattr(settings, 'SLACK_WEBHOOK_URL', None)
        self.alert_recipients = getattr(settings, 'ALERT_RECIPIENTS', [])

    async def send_alert(self, 
                        title: str, 
                        message: str, 
                        severity: str = 'info',
                        notify_methods: Optional[List[str]] = None) -> None:
        """發送告警通知"""
        try:
            if notify_methods is None:
                notify_methods = ['log']  # 默認只記錄日誌
            
            # 始終記錄到日誌
            log_level = getattr(logger, severity.lower(), logger.info)
            log_level(f"{title}: {message}")
            
            tasks = []
            
            if 'email' in notify_methods and self.email_config['username']:
                tasks.append(self.send_email_alert(title, message, severity))
                
            if 'slack' in notify_methods and self.slack_webhook:
                tasks.append(self.send_slack_alert(title, message, severity))
            
            if tasks:
                await asyncio.gather(*tasks)
            
        except Exception as e:
            logger.error(f"Error sending alert: {e}")
    
    async def send_email_alert(self, title: str, message: str, severity: str) -> None:
        """發送郵件告警"""
        try:
            if not self.email_config['username']:
                return
                
            msg = MIMEMultipart()
            msg['From'] = self.email_config['from_email']
            msg['To'] = ', '.join(self.alert_recipients)
            msg['Subject'] = f"[{severity.upper()}] {title}"
            
            body = f"""
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            Severity: {severity.upper()}
            
            {message}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._send_email,
                msg
            )
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
    
    def _send_email(self, msg: MIMEMultipart) -> None:
        """同步發送郵件"""
        with smtplib.SMTP(self.email_config['smtp_server'], 
                         self.email_config['smtp_port']) as server:
            if self.email_config['username']:
                server.starttls()
                server.login(
                    self.email_config['username'],
                    self.email_config['password']
                )
            server.send_message(msg)
    
    async def send_slack_alert(self, title: str, message: str, severity: str) -> None:
        """發送Slack告警"""
        if not self.slack_webhook:
            return
            
        try:
            color_map = {
                'info': '#36a64f',
                'warning': '#ffcc00',
                'error': '#ff0000',
                'critical': '#7b0000'
            }
            
            payload = {
                "attachments": [{
                    "title": title,
                    "text": message,
                    "color": color_map.get(severity.lower(), '#36a64f'),
                    "fields": [
                        {
                            "title": "Severity",
                            "value": severity.upper(),
                            "short": True
                        },
                        {
                            "title": "Time",
                            "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "short": True
                        }
                    ]
                }]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.slack_webhook, 
                                      json=payload) as response:
                    if response.status not in (200, 201, 204):
                        raise ValueError(
                            f"Error sending Slack alert: {response.status}"
                        )
            
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")

    async def test_alert_config(self) -> dict:
        """測試告警配置"""
        results = {
            'email': False,
            'slack': False,
            'log': True
        }
        
        try:
            await self.send_alert(
                "Test Alert",
                "This is a test alert message",
                severity="info",
                notify_methods=['email', 'slack']
            )
            
            if self.email_config['username']:
                results['email'] = True
            if self.slack_webhook:
                results['slack'] = True
                
        except Exception as e:
            logger.error(f"Error testing alert config: {e}")
            
        return results