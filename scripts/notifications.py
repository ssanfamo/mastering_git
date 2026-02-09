# notifications.py
import json
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class SlackNotifier:
    """Send notifications to Slack"""
    
    def __init__(self, token: str, channel: str):
        """
        Initialize Slack notifier
        
        Args:
            token: Slack bot token (starts with 'xoxb-')
            channel: Channel to send to (e.g., '#alerts' or '@username')
        """
        self.token = token
        self.channel = channel
        self._client = None
        
    def _get_client(self):
        """Lazy load Slack client"""
        if self._client is None:
            try:
                from slack_sdk import WebClient
                self._client = WebClient(token=self.token)
            except ImportError:
                logger.error("slack_sdk not installed. Run: pip install slack-sdk")
                raise
        return self._client
    
    def send_alert(self, message: str, title: str = "System Alert", 
                   color: str = "danger") -> bool:
        """
        Send alert to Slack
        
        Args:
            message: Alert message
            title: Alert title
            color: 'good' (green), 'warning' (yellow), 'danger' (red)
            
        Returns:
            bool: True if successful
        """
        try:
            client = self._get_client()
            
            # Create formatted message
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": title,
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                },
                {
                    "type": "divider"
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Source:* System Monitor"
                        }
                    ]
                }
            ]
            
            response = client.chat_postMessage(
                channel=self.channel,
                text=f"{title}: {message}",  # Fallback text
                blocks=blocks,
                username="System Monitor Bot",
                icon_emoji=":warning:"
            )
            
            if response["ok"]:
                logger.info(f"Slack alert sent to {self.channel}")
                return True
            else:
                logger.error(f"Slack error: {response.get('error', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False


class TeamsNotifier:
    """Send notifications to Microsoft Teams"""
    
    def __init__(self, webhook_url: str):
        """
        Initialize Teams notifier
        
        Args:
            webhook_url: Teams incoming webhook URL
        """
        self.webhook_url = webhook_url
        
    def send_alert(self, message: str, title: str = "System Alert",
                   theme_color: str = "0076D7") -> bool:
        """
        Send alert to Microsoft Teams
        
        Args:
            message: Alert message
            title: Alert title
            theme_color: Hex color code (without #)
            
        Returns:
            bool: True if successful
        """
        try:
            import pymsteams
            
            teams_message = pymsteams.connectorcard(self.webhook_url)
            teams_message.title(title)
            teams_message.text(message)
            teams_message.color(theme_color)
            
            # Add timestamp
            from datetime import datetime
            teams_message.addFact("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # Add potential actions
            # teams_message.addPotentialAction({
            #     "@type": "OpenUri",
            #     "name": "View Dashboard",
            #     "targets": [{"os": "default", "uri": "http://localhost:5001"}]
            # })
            
            teams_message.send()
            logger.info("Teams alert sent successfully")
            return True
            
        except ImportError:
            # Fallback to requests if pymsteams not available
            try:
                import requests
                from datetime import datetime
                
                payload = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "summary": title,
                    "themeColor": theme_color,
                    "title": title,
                    "text": message,
                    "sections": [{
                        "facts": [{
                            "name": "Timestamp",
                            "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }]
                    }]
                }
                
                response = requests.post(
                    self.webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response.status_code == 200:
                    logger.info("Teams alert sent (via requests)")
                    return True
                else:
                    logger.error(f"Teams error: {response.status_code} - {response.text}")
                    return False
                    
            except Exception as e:
                logger.error(f"Failed to send Teams alert: {e}")
                return False


class NotificationManager:
    """Manage multiple notification channels"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.notifiers = []
        self._setup_notifiers()
        
    def _setup_notifiers(self):
        """Initialize all configured notifiers"""
        # Slack
        slack_config = self.config.get('slack', {})
        if slack_config.get('enabled', False):
            token = slack_config.get('token')
            channel = slack_config.get('channel')
            if token and channel:
                self.notifiers.append(SlackNotifier(token, channel))
                logger.info("Slack notifier configured")
        
        # Teams
        teams_config = self_config.get('teams', {})
        if teams_config.get('enabled', False):
            webhook = teams_config.get('webhook')
            if webhook:
                self.notifiers.append(TeamsNotifier(webhook))
                logger.info("Teams notifier configured")
                
        if not self.notifiers:
            logger.warning("No notification channels configured")
    
    def send_to_all(self, message: str, title: str = "System Alert", 
                    alert_type: str = "info") -> Dict[str, bool]:
        """
        Send alert through all configured channels
        
        Args:
            message: Alert message
            title: Alert title
            alert_type: 'info', 'warning', 'critical'
            
        Returns:
            Dict with channel: success pairs
        """
        results = {}
        
        # Map alert type to colors
        color_map = {
            'info': ('#3498db', 'good'),
            'warning': ('#f39c12', 'warning'),
            'critical': ('#e74c3c', 'danger')
        }
        color, slack_color = color_map.get(alert_type, ('#3498db', 'good'))
        
        for notifier in self.notifiers:
            if isinstance(notifier, SlackNotifier):
                success = notifier.send_alert(message, title, slack_color)
                results['slack'] = success
            elif isinstance(notifier, TeamsNotifier):
                success = notifier.send_alert(message, title, color.lstrip('#'))
                results['teams'] = success
                
        return results


# Test function
def test_notifications():
    """Test notification systems"""
    import os
    from dotenv import load_dotenv
    
    # Load from .env file or environment variables
    load_dotenv()
    
    config = {
        'slack': {
            'enabled': True,
            'token': os.getenv('SLACK_TOKEN', 'xoxb-your-token-here'),
            'channel': os.getenv('SLACK_CHANNEL', '#alerts')
        },
        'teams': {
            'enabled': True,
            'webhook': os.getenv('TEAMS_WEBHOOK', 'https://your-webhook-url')
        }
    }
    
    manager = NotificationManager(config)
    
    # Test messages
    test_cases = [
        ("System is running normally", "Info Test", "info"),
        ("CPU usage above 80%", "Warning Test", "warning"),
        ("Critical service stopped", "Critical Test", "critical")
    ]
    
    for message, title, alert_type in test_cases:
        print(f"\nTesting: {title}")
        results = manager.send_to_all(message, title, alert_type)
        print(f"Results: {results}")
        
        # Wait between tests
        import time
        time.sleep(2)


if __name__ == "__main__":
    print("Notification module test")
    # For testing, create a .env file with your tokens
    test_notifications()