import itchat
import logging
import mimetypes
import os
import xmltodict

from channel import EFBMsg, MsgType
from channelExceptions import EFBMessageError
from functools import lru_cache
from PIL import Image
from plugins.eh_wechat_slave import WeChatChannel, wechat_msg_meta


class WechatExChannel(WeChatChannel):
    def __init__(self, queue, mutex):
        super(WeChatChannel, self).__init__(queue, mutex)
        self.itchat = itchat.new_instance()
        itchat.set_logging(loggingLevel=logging.getLogger().level, showOnCmd=False)
        self.itchat_msg_register()
        mimetypes.init()
        self.logger.info("EWS Inited!!!\n---")

    def poll(self):
        self.reauth()
        super().poll()

    def itchat_msg_register(self):
        self.itchat.msg_register(['Text'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_text_msg)
        self.itchat.msg_register(['Sharing'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_link_msg)
        self.itchat.msg_register(['Picture'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_picture_msg)
        self.itchat.msg_register(['Attachment'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_file_msg)
        self.itchat.msg_register(['Recording'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_voice_msg)
        self.itchat.msg_register(['Map'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_location_msg)
        self.itchat.msg_register(['Video'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_video_msg)
        self.itchat.msg_register(['Card'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_card_msg)
        self.itchat.msg_register(['Friends'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_friend_msg)
        self.itchat.msg_register(['Useless', 'Note'], isFriendChat=True, isMpChat=False, isGroupChat=True)(self.wechat_system_msg)
        self.itchat.msg_register(['Sharing'], isFriendChat=False, isMpChat=True, isGroupChat=False)(self.wechat_mp_msg)

        @self.itchat.msg_register(["System"], isFriendChat=True, isMpChat=False, isGroupChat=True)
        def wc_msg_system_log(msg):
            self.logger.debug("WeChat \"System\" message:\n%s", repr(msg))

    @wechat_msg_meta
    def wechat_mp_msg(self, msg):
        # parse XML
        itchat.utils.emoji_formatter(msg, 'Content')
        xml_data = msg['Content']
        data = xmltodict.parse(xml_data)
        # filter message with images or extra links
        appmsg = data.get('msg', {}).get('appmsg', {})
        extra_links = appmsg.get('mmreader', {}).get('category', {}).get('item', [])
        if appmsg.get('thumburl', None) or (isinstance(extra_links, list) and len(extra_links) > 0):
            return
        # send message
        base_data = [
            appmsg.get('title', None),
            appmsg.get('des', None),
            appmsg.get('thumburl', None),
            appmsg.get('url', None),
            True
        ]
        self.wechat_raw_link_msg(msg, *base_data)

    @wechat_msg_meta
    def wechat_raw_link_msg(self, msg, title, description, image, url, disable_web_page_preview=False):
        mobj = EFBMsg(self)
        if url:
            mobj.type = MsgType.Link
            mobj.attributes = {
                'title': title,
                'description': description,
                'image': image,
                'url': url,
                'disable_web_page_preview': disable_web_page_preview
            }
        else:
            mobj.type = MsgType.Text
            mobj.text = "%s\n%s" % (title, description)
            if image:
                mobj.text += "\n\n%s" % image
        return mobj

    @lru_cache(maxsize=128)
    def search_user(self, UserName=None, uid=None, uin=None, name=None, ActualUserName=None, refresh=False):
        if refresh:
            self.search_user.cache_clear()
        return super().search_user(UserName, uid, uin, name, ActualUserName, refresh)

    def reauth(self, command=False):
        self.search_user.cache_clear()
        return super().reauth(command)

    def send_message(self, msg):
        if msg.type == MsgType.Image and msg.mime == 'image/gif':
            if os.path.isfile(msg.path) and os.path.getsize(msg.path) <= self.max_image_size:
                super().send_message(msg)
                return
            mp4 = msg.path.rsplit('.', 1)[0]
            if os.path.isfile(mp4):
                try:
                    os.remove(msg.path)
                except FileNotFoundError:
                    pass
                msg.type = MsgType.Video
                msg.mime = 'video/mp4'
                msg.path = mp4
            else:
                raise EFBMessageError('Image sent is too large. (IS01)')
        elif msg.type == MsgType.Image and msg.mime not in self.supported_image_types:
            msg.type = MsgType.File
        elif msg.type == MsgType.Sticker and msg.mime != 'image/gif':
            img = Image.open(msg.path)
            try:
                alpha = img.split()[3]
            except IndexError:
                alpha = None
            filename = os.path.basename(msg.path)
            path = os.path.splitext(os.path.join('storage', self.channel_id, filename))[0] + '.gif'
            if alpha:
                mask = Image.eval(alpha, lambda a: 255 if a <= 128 else 0)
                img = img.convert('RGB').convert('P', palette=Image.ADAPTIVE, colors=255)
                img.paste(255, mask)
                img.save(path, transparency=255)
            else:
                img.save(path)
            os.remove(msg.path)
            # update message properties
            msg.mime = 'image/gif'
            msg.path = path
        super().send_message(msg)
