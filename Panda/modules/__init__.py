from Panda import LOGS


def __list_all_modules():
    import glob
    from os.path import basename, dirname, isfile

    mod_paths = glob.glob(dirname(__file__) + "/*.py")
    all_modules = [
        basename(f)[:-3]
        for f in mod_paths
        if isfile(f) and f.endswith(".py") and not f.endswith("__init__.py")
    ]
    return all_modules


ALL_MODULES = sorted(__list_all_modules())
LOGS.info("Modules to load: %s", str(ALL_MODULES))
__all__ = ALL_MODULES + ["ALL_MODULES"]

import math
import os
import re
import time

import heroku3
import lottie
import requests
import spamwatch as spam_watch
from validators.url import url

from .. import *
from ..Config import Config
from ..core.logger import logging
from ..core.managers import edit_delete, edit_or_reply
from ..core.session import PandaBot
from ..helpers import *
from ..helpers.utils import _format, _pandatools, _pandautils, install_pip, reply_id

# =================== CONSTANT ===================
bot = PandaBot
pandaub = PandaBot
LOGS = logging.getLogger(__name__)
USERID = pandaub.uid if Config.OWNER_ID == 0 else Config.OWNER_ID
ALIVE_NAME = Config.ALIVE_NAME
AUTONAME = Config.AUTONAME
DEFAULT_BIO = Config.DEFAULT_BIO


Heroku = heroku3.from_key(Config.HEROKU_API_KEY)
heroku_api = "https://api.heroku.com"
HEROKU_APP_NAME = Config.HEROKU_APP_NAME
HEROKU_API_KEY = Config.HEROKU_API_KEY

thumb_image_path = os.path.join(Config.TMP_DOWNLOAD_DIRECTORY, "thumb_image.jpg")

USERID = pandaub.uid if Config.OWNER_ID == 0 else Config.OWNER_ID

# mention user
mention = f"[{Config.ALIVE_NAME}](tg://user?id={USERID})"
hmention = f"<a href = tg://user?id={USERID}>{Config.ALIVE_NAME}</a>"

PM_START = []
PMMESSAGE_CACHE = {}
PMMENU = "pmpermit_menu" not in Config.NO_LOAD

# Gdrive
G_DRIVE_CLIENT_ID = Config.G_DRIVE_CLIENT_ID
G_DRIVE_CLIENT_SECRET = Config.G_DRIVE_CLIENT_SECRET
G_DRIVE_DATA = Config.G_DRIVE_DATA
G_DRIVE_FOLDER_ID = Config.G_DRIVE_FOLDER_ID
TMP_DOWNLOAD_DIRECTORY = Config.TMP_DOWNLOAD_DIRECTORY

# spamwatch support
if Config.SPAMWATCH_API:
    token = Config.SPAMWATCH_API
    spamwatch = spam_watch.Client(token)
else:
    spamwatch = None


# ================================================

if not os.path.isdir(Config.TMP_DOWNLOAD_DIRECTORY):
    os.makedirs(Config.TMP_DOWNLOAD_DIRECTORY)


# thumb image
if Config.THUMB_IMAGE is not None:
    check = url(Config.THUMB_IMAGE)
    if check:
        try:
            with open(thumb_image_path, "wb") as f:
                f.write(requests.get(Config.THUMB_IMAGE).content)
        except Exception as e:
            LOGS.info(str(e))


def set_key(dictionary, key, value):
    if key not in dictionary:
        dictionary[key] = value
    elif isinstance(dictionary[key], list):
        if value in dictionary[key]:
            return
        dictionary[key].append(value)
    else:
        dictionary[key] = [dictionary[key], value]


async def make_gif(event, reply, quality=None, fps=None):
    fps = fps or 1
    quality = quality or 256
    result_p = os.path.join("temp", "animation.gif")
    animation = lottie.parsers.tgs.parse_tgs(reply)
    with open(result_p, "wb") as result:
        await _pandautils.run_sync(
            lottie.exporters.gif.export_gif, animation, result, quality, fps
        )
    return result_p


# Copyright (C) 2021 TeamUltroid <https://github.com/TeamUltroid/Ultroid>
# Recode by @diemmmmmmmmmm
# FROM Panda-Userbot <https://github.com/ilhammansiz/PandaX_Userbot>

# Version sql
#Panda Userbot




import asyncio
import os
import re
import traceback
from time import time
from traceback import format_exc


from pytgcalls import GroupCallFactory
from pytgcalls.exceptions import GroupCallNotFoundError
from telethon.errors.rpcerrorlist import ParticipantJoinMissingError
from telethon import events
from telethon.tl import functions, types
from telethon.utils import get_display_name
from youtube_dl import YoutubeDL
from youtubesearchpython import Playlist, ResultMode, Video, VideosSearch
from Panda import LOGS, PandaBot
from Panda.utils.tools import (
    bash,
    downloader,
    get_user_id,
    get_videos_link,
    inline_mention,
    mediainfo,
    time_formatter,
)

from Panda.utils.owner import admin_check, in_pattern

from Panda.sql_helper.globals import check_vcauth, gvarstatus
from Panda.sql_helper.globals import get_chats as get_vc
from Panda.utils.vceor import eor, eod
from PandaXBahasa import get_string
from Panda.Config import Config
from Panda.core.data import _sudousers_list

HNDLR = Config.COMMAND_HAND_LER
asst = PandaBot.tgbot
UltVer = "VcPanda" 
asstUserName = Config.TG_BOT_USERNAME
LOG_CHANNEL = int(Config.PRIVATE_GROUP_BOT_API_ID)
ACTIVE_CALLS, VC_QUEUE = [], {}
MSGID_CACHE, VIDEO_ON = {}, {}
CLIENTS = {}
vcClient = PandaBot.tgbot

def sudoers():
    return _sudousers_list()

def owner_and_sudos():
    return [str(PandaBot.uid), *sudoers()]


def html_mention(event, sender_id=None, full_name=None):
    if not full_name:
        full_name = get_display_name(event.sender)
    if not sender_id:
        sender_id = event.sender_id
    return "<a href={}>{}</a>".format(f"tg://user?id={sender_id}", full_name)


def VC_AUTHS():
    _vcsudos = gvarstatus("VC_SUDOS").split() if gvarstatus("VC_SUDOS") else ""
    return [int(a) for a in [*owner_and_sudos(), *_vcsudos]]


class Player:
    def __init__(self, chat, event=None, video=False):
        self._chat = chat
        self._current_chat = event.chat_id if event else LOG_CHANNEL
        self._video = video
        if CLIENTS.get(chat):
            self.group_call = CLIENTS[chat]
        else:
            _client = GroupCallFactory(
                vcClient, GroupCallFactory.MTPROTO_CLIENT_TYPE.TELETHON
            )
            self.group_call = _client.get_group_call()
            CLIENTS.update({chat: self.group_call})

    async def make_vc_active(self):
        try:
            await vcClient(CreateGroupCallRequest(
                    self._chat, title="🎧 PandaX Music 🎶"
                )
            )
        except Exception as e:
            return False, e
        return True, None

    async def startCall(self):
        if VIDEO_ON:
            for chats in VIDEO_ON:
                await VIDEO_ON[chats].stop()
            VIDEO_ON.clear()
            await asyncio.sleep(3)
        if self._video:
            for chats in list(CLIENTS):
                if chats != self._chat:
                    await CLIENTS[chats].stop()
                    del CLIENTS[chats]
            VIDEO_ON.update({self._chat: self.group_call})
        if self._chat not in ACTIVE_CALLS:
            try:
                self.group_call.on_network_status_changed(self.on_network_changed)
                self.group_call.on_playout_ended(self.playout_ended_handler)
                await self.group_call.join(self._chat)
            except GroupCallNotFoundError:
                dn, err = await self.make_vc_active()
                if err:
                    return False, err
            except Exception as e:
                return False, e
        return True, None

    async def on_network_changed(self, call, is_connected):
        chat = self._chat
        if is_connected:
            if chat not in ACTIVE_CALLS:
                ACTIVE_CALLS.append(chat)
        elif chat in ACTIVE_CALLS:
            ACTIVE_CALLS.remove(chat)

    async def playout_ended_handler(self, call, source, mtype):
        if os.path.exists(source):
            os.remove(source)
        await self.play_from_queue()

    async def play_from_queue(self):
        chat_id = self._chat
        if chat_id in VIDEO_ON:
            await self.group_call.stop_video()
            VIDEO_ON.pop(chat_id)
        try:
            song, title, link, thumb, from_user, pos, dur = await get_from_queue(
                chat_id
            )
            try:
                await self.group_call.start_audio(song)
            except ParticipantJoinMissingError:
                await self.vc_joiner()
                await self.group_call.start_audio(song)
            if MSGID_CACHE.get(chat_id):
                await MSGID_CACHE[chat_id].delete()
                del MSGID_CACHE[chat_id]
            xx = await PandaBot.send_message(
                self._current_chat,
                "<strong>🎧 Now playing #{}: <a href={}>{}</a>\n⏰ Duration:</strong> <code>{}</code>\n👤 <strong>Requested by:</strong> {}".format(
                    pos, link, title, dur, from_user
                ),
                file=thumb,
                link_preview=False,
                parse_mode="html",
            )
            MSGID_CACHE.update({chat_id: xx})
            VC_QUEUE[chat_id].pop(pos)
            if not VC_QUEUE[chat_id]:
                VC_QUEUE.pop(chat_id)

        except (IndexError, KeyError):
            await self.group_call.stop()
            del CLIENTS[self._chat]
            await PandaBot.send_message(
                self._current_chat,
                f"• Successfully Left Vc : <code>{chat_id}</code> •",
                parse_mode="html",
            )
        except Exception:
            await PandaBot.send_message(
                self._current_chat,
                f"<strong>ERROR:</strong> <code>{format_exc()}</code>",
                parse_mode="html",
            )

    async def vc_joiner(self):
        chat_id = self._chat
        done, err = await self.startCall()

        if done:
            await vcClient.send_message(
                self._current_chat,
                "• Joined VC in <code>{}</code>".format(chat_id),
                parse_mode="html",
            )
            return True
        await vcClient.send_message(
            self._current_chat,
            f"<strong>ERROR while Joining Vc -</strong> <code>{chat_id}</code> :\n<code>{err}</code>",
            parse_mode="html",
        )
        return False







def PandaVc_cmd(dec, **kwargs):
    def ult(func):
        kwargs["func"] = lambda e: not e.is_private and not e.via_bot_id and not e.fwd_from
        handler = HNDLR or "/"
        kwargs["pattern"] = re.compile(f"\\{handler}" + dec)
        from_users = VC_AUTHS()
        kwargs["from_users"] = from_users
        vc_auth = kwargs.get("vc_auth", True)

        if "vc_auth" in kwargs:
            del kwargs["vc_auth"]

        async def vc_handler(e):
            VCAUTH = list(get_vc().keys())
            if not (
                (e.out)
                or (e.sender_id in from_users)
                or (vc_auth and e.chat_id in VCAUTH)
            ):
                return
            if vc_auth:
                cha, adm = check_vcauth(e.chat_id)
                if adm and not (await admin_check(e)):
                    return
            try:
                await func(e)
            except Exception:
                LOGS.exception(Exception)
                await asst.send_message(
                    LOG_CHANNEL,
                    f"VC Error - <code>{UltVer}</code>\n\n<code>{e.text}</code>\n\n<code>{format_exc()}</code>",
                    parse_mode="html",
                )

        vcClient.add_event_handler(
            vc_handler,
            events.NewMessage(**kwargs),
        )

    return ult


def add_to_queue(chat_id, song, song_name, link, thumb, from_user, duration):
    try:
        n = sorted(list(VC_QUEUE[chat_id].keys()))
        play_at = n[-1] + 1
    except BaseException:
        play_at = 1
    stuff = {
        play_at: {
            "song": song,
            "title": song_name,
            "link": link,
            "thumb": thumb,
            "from_user": from_user,
            "duration": duration,
        }
    }
    if VC_QUEUE.get(chat_id):
        VC_QUEUE[int(chat_id)].update(stuff)
    else:
        VC_QUEUE.update({chat_id: stuff})
    return VC_QUEUE[chat_id]


def list_queue(chat):
    if VC_QUEUE.get(chat):
        txt, n = "", 0
        for x in list(VC_QUEUE[chat].keys())[:18]:
            n += 1
            data = VC_QUEUE[chat][x]
            txt += f'<strong>{n}. <a href={data["link"]}>{data["title"]}</a> :</strong> <i>By: {data["from_user"]}</i>\n'
        txt += "\n\n....."
        return txt


async def get_from_queue(chat_id):
    play_this = list(VC_QUEUE[int(chat_id)].keys())[0]
    info = VC_QUEUE[int(chat_id)][play_this]
    song = info.get("song")
    title = info["title"]
    link = info["link"]
    thumb = info["thumb"]
    from_user = info["from_user"]
    duration = info["duration"]
    if not song:
        song = await get_stream_link(link)
    return song, title, link, thumb, from_user, play_this, duration


# --------------------------------------------------


async def download(query):
    search = VideosSearch(query, limit=1).result()
    data = search["result"][0]
    link = data["link"]
    dl = await get_stream_link(link)
    title = data["title"]
    duration = data["duration"]
    thumb = f"https://i.ytimg.com/vi/{data['id']}/hqdefault.jpg"
    return dl, thumb, title, link, duration


async def get_stream_link(ytlink):
    """
    info = YoutubeDL({}).extract_info(url=ytlink, download=False)
    k = ""
    for x in info["formats"]:
        h, w = ([x["height"], x["width"]])
        if h and w:
            if h <= 720 and w <= 1280:
                k = x["url"]
    return k
    """
    stream = await bash(f'youtube-dl -g -f "best[height<=?720][width<=?1280]" {ytlink}')
    return stream[0]


async def vid_download(query):
    search = VideosSearch(query, limit=1).result()
    data = search["result"][0]
    link = data["link"]
    video = await get_stream_link(link)
    title = data["title"]
    thumb = f"https://i.ytimg.com/vi/{data['id']}/hqdefault.jpg"
    duration = data.get("duration") or "♾"
    return video, thumb, title, link, duration


async def dl_playlist(chat, from_user, link):
    # untill issue get fix
    # https://github.com/alexmercerind/youtube-search-python/issues/107
    """
    vids = Playlist.getVideos(link)
    try:
        vid1 = vids["videos"][0]
        duration = vid1["duration"] or "♾"
        title = vid1["title"]
        song = await get_stream_link(vid1['link'])
        thumb = f"https://i.ytimg.com/vi/{vid1['id']}/hqdefault.jpg"
        return song[0], thumb, title, vid1["link"], duration
    finally:
        vids = vids["videos"][1:]
        for z in vids:
            duration = z["duration"] or "♾"
            title = z["title"]
            thumb = f"https://i.ytimg.com/vi/{z['id']}/hqdefault.jpg"
            add_to_queue(chat, None, title, z["link"], thumb, from_user, duration)
    """
    links = await get_videos_link(link)
    try:
        search = VideosSearch(links[0], limit=1).result()
        vid1 = search["result"][0]
        duration = vid1.get("duration") or "♾"
        title = vid1["title"]
        song = await get_stream_link(vid1["link"])
        thumb = f"https://i.ytimg.com/vi/{vid1['id']}/hqdefault.jpg"
        return song, thumb, title, vid1["link"], duration
    finally:
        for z in links[1:]:
            search = VideosSearch(z, limit=1).result()
            vid = search["result"][0]
            duration = vid.get("duration") or "♾"
            title = vid["title"]
            thumb = f"https://i.ytimg.com/vi/{vid['id']}/hqdefault.jpg"
            add_to_queue(chat, None, title, vid["link"], thumb, from_user, duration)


async def file_download(event, reply, fast_download=True):
    thumb = "https://telegra.ph/file/241b753a0e7acdc7f5a80.mp4"
    title = reply.file.title or reply.file.name or str(time()) + ".mp4"
    if fast_download:
        dl = await downloader(
            "Panda/core/downloads/" + reply.file.name,
            reply.media.document,
            event,
            time(),
            "Downloading " + title + "...",
        )
        dl = dl.name
    else:
        dl = await reply.download_media()
    duration = time_formatter(reply.file.duration * 1000) if reply.file.duration else "🤷‍♂️"
    if reply.document.thumbs:
        thumb = await reply.download_media("Panda/core/downloads/", thumb=-1)
    return dl, thumb, title, reply.message_link, duration


