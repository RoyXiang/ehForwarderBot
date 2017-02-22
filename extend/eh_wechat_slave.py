import itchat
import logging
import mimetypes
import os
import xmltodict

from channel import EFBMsg, MsgType
from channelExceptions import EFBMessageError
from functools import lru_cache
from moviepy.editor import VideoFileClip
from plugins.eh_wechat_slave import WeChatChannel, wechat_msg_meta
from pydub import AudioSegment


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
        # filter messages from massive platform only
        if not self.itchat.search_mps(userName=msg['FromUserName']):
            super().wechat_link_msg(msg)
            return
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
            appmsg.get('url', None)
        ]
        self.wechat_raw_link_msg(msg, *base_data)

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
        elif msg.type == MsgType.Image and msg.mime == 'image/gif':
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
        elif msg.type == MsgType.Audio:
            filename = msg.filename or os.path.basename(msg.path)
            path = os.path.splitext(os.path.join('storage', self.channel_id, filename))[0] + '.mp3'
            if msg.mime.startswith('video/'):
                clip = VideoFileClip(msg.path)
                clip.audio.write_audio_file(path)
            else:
                sound = AudioSegment.from_file(msg.path)
                sound.export(path, format='mp3')
            os.remove(msg.path)
            # update message properties
            msg.type = MsgType.File
            msg.mime = 'audio/mpeg'
            msg.path = path
            msg.filename = os.path.basename(path)
        elif msg.type == MsgType.File:
            filename = msg.filename or os.path.basename(msg.path)
            path = os.path.join('storage', self.channel_id, filename)
            os.rename(msg.path, path)
            # update message properties
            msg.path = path
            if (msg.mime in self.supported_image_types
                    and os.path.getsize(msg.path) <= self.max_image_size):
                msg.type = MsgType.Image
        super().send_message(msg)

    def _itchat_send_file(self, fileDir, toUserName=None, filename=None):
        try:
            return self.itchat.send_file(fileDir, toUserName=toUserName)
        except Exception as e:
            raise EFBMessageError(repr(e))
