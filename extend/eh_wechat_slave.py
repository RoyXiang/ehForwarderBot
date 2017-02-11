import itchat
import logging
import mimetypes

from plugins.eh_wechat_slave import WeChatChannel


class WechatExChannel(WeChatChannel):
    def __init__(self, queue, mutex):
        super(WeChatChannel, self).__init__(queue, mutex)
        self.itchat = itchat.new_instance()
        itchat.set_logging(loggingLevel=logging.getLogger().level, showOnCmd=False)
        self.itchat_msg_register()
        mimetypes.init(files=["mimetypes"])
        self.logger.info("EWS Inited!!!\n---")

    def poll(self):
        self.reauth()
        super().poll()
