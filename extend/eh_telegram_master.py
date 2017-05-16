import config

from channel import TargetType
from functools import lru_cache
from operator import itemgetter
from plugins.eh_telegram_master import TelegramChannel


class TelegramExChannel(TelegramChannel):
    @lru_cache(maxsize=4)
    def get_chat(self, chat_id):
        return self.bot.bot.get_chat(chat_id)

    def process_msg(self, msg):
        if msg.target and msg.target['type'] == TargetType.Member:
            try:
                uid, idx = itemgetter(0, 1)(msg.target['target']['uid'].split('.'))
                assert(uid == 'admin')
                chat = self.get_chat(self.admins[int(idx)])
                assert(chat)
                msg.text = msg.text.replace(msg.target['target']['name'], chat.username)
            except:
                pass
        super().process_msg(msg)
        self.timeout_count = 0

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
