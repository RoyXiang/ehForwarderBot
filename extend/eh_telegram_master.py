import config

from plugins.eh_telegram_master import TelegramChannel


class TelegramExChannel(TelegramChannel):
    def polling_from_tg(self):
        webhook_url = self._flag('webhook_url', '')
        if webhook_url != '':
            token = getattr(config, self.channel_id)['token']
            self.bot.start_webhook('0.0.0.0', 80, token)
            if not webhook_url.endswith('/'):
                webhook_url += '/'
            webhook_url += token
            self.bot.bot.setWebhook(webhook_url=webhook_url)
        else:
            self.bot.start_polling(timeout=10)
