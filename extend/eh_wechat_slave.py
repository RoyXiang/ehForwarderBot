import itchat
import logging
import mimetypes
import xmltodict

from channel import EFBMsg, MsgType
from functools import lru_cache
from plugins.eh_wechat_slave import WeChatChannel, wechat_msg_meta


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

    def itchat_msg_register(self):
        self.itchat.msg_register(['Text'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_text_msg)
        self.itchat.msg_register(['Sharing'], isFriendChat=True, isMpChat=True, isGroupChat=True)(self.wechat_link_msg)
        self.itchat.msg_register(['Picture'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_picture_msg)
        self.itchat.msg_register(['Attachment'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_file_msg)
        self.itchat.msg_register(['Recording'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_voice_msg)
        self.itchat.msg_register(['Map'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_location_msg)
        self.itchat.msg_register(['Video'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_video_msg)
        self.itchat.msg_register(['Card'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_card_msg)
        self.itchat.msg_register(['Friends'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_friend_msg)
        self.itchat.msg_register(['Useless', 'Note'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_system_msg)

        @self.itchat.msg_register(["System"], isFriendChat=True, isMpChat=False, isGroupChat=True)
        def wc_msg_system_log(msg):
            self.logger.debug("WeChat \"System\" message:\n%s", repr(msg))

    @wechat_msg_meta
    def wechat_link_msg(self, msg):
        # initiate object
        mobj = EFBMsg(self)
        # parse XML
        itchat.utils.emoji_formatter(msg, 'Content')
        xml_data = msg['Content']
        data = xmltodict.parse(xml_data)
        # set attributes
        appmsg = data.get('msg', {}).get('appmsg', {})
        mobj.attributes = {
            "title": appmsg.get('title', None),
            "description": appmsg.get('des', None),
            "image": appmsg.get('thumburl', None),
            "url": appmsg.get('url', None),
        }
        # filter message with images or extra links
        extra_links = appmsg.get('mmreader', {}).get('category', {}).get('item', [])
        if mobj.attributes['image'] or (isinstance(extra_links, list) and len(extra_links) > 0):
            return
        # check message url
        if mobj.attributes['url'] is None:
            txt = mobj.attributes['title'] or ''
            txt += mobj.attributes['description'] or ''
            msg['Text'] = txt
            self.wechat_text_msg(msg)
            return
        # format text
        mobj.text = ""
        mobj.type = MsgType.Link
        return mobj

    @lru_cache(maxsize=128)
    def search_user(self, UserName=None, uid=None, uin=None, name=None, ActualUserName=None, refresh=False):
        if refresh:
            self.search_user.cache_clear()
        return super().search_user(UserName, uid, uin, name, ActualUserName, refresh)

    def send_message(self, msg):
        if msg.type in [MsgType.Text, MsgType.Link] and msg.target:
            UserName = self.get_UserName(msg.destination['uid'])
            if not UserName:
                raise EFBChatNotFound
            if not str(UserName).startswith('@@'):
                msg.target = None
            else:
                msg.target['type'] = TargetType.Member
        super().send_message(msg)
