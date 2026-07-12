import asyncio
import random

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
from astrbot.core.message.components import File, Record
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import (
    AiocqhttpMessageEvent,
)

from .config import PluginConfig
from .downloader import Downloader
from .model import Song
from .platform import BaseMusicPlayer


class MusicSender:
    def __init__(
        self, config: PluginConfig, downloader: Downloader
    ):
        self.cfg = config
        self.downloader = downloader

    @staticmethod
    async def send_msg(event: AiocqhttpMessageEvent, payloads: dict) -> int | None:
        if event.is_private_chat():
            payloads["user_id"] = event.get_sender_id()
            result = await event.bot.api.call_action("send_private_msg", **payloads)
        else:
            payloads["group_id"] = event.get_group_id()
            result = await event.bot.api.call_action("send_group_msg", **payloads)
        return result.get("message_id") if result else None

    async def send_song_selection(
        self, event: AstrMessageEvent, songs: list[Song], title: str | None = None
    ) -> None:
        formatted_songs = [
            f"{index + 1}. {song.name} - {song.artists}"
            for index, song in enumerate(songs)
        ]
        if title:
            formatted_songs.insert(0, title)

        msg = "\n".join(formatted_songs)
        if isinstance(event, AiocqhttpMessageEvent):
            payloads = {"message": [{"type": "text", "data": {"text": msg}}]}
            message_id = await self.send_msg(event, payloads)
            if message_id and self.cfg.timeout_recall:
                await asyncio.sleep(self.cfg.timeout)
                await event.bot.delete_msg(message_id=message_id)
        else:
            await event.send(event.plain_result(msg))

    async def send_comment(
        self, event: AstrMessageEvent, player: BaseMusicPlayer, song: Song
    ) -> bool:
        if not song.comments:
            return False
        try:
            content = random.choice(song.comments).get("content")
            await event.send(event.plain_result(content))
            return True
        except Exception:
            return False

    async def send_record(
        self, event: AstrMessageEvent, player: BaseMusicPlayer, song: Song
    ) -> bool:
        if not song.audio_url:
            song = await player.fetch_extra(song, prefer_high_quality=False)
        if not song.audio_url:
            await event.send(event.plain_result(f"【{song.name}】音频获取失败"))
            return False
        try:
            logger.debug(f"正在发送【{song.name}】音频: {song.audio_url}")
            seg = Record.fromURL(song.audio_url)
            await event.send(event.chain_result([seg]))
            return True
        except Exception as e:
            logger.error(f"【{song.name}】音频发送失败: {e}")
            return False

    async def send_file(
        self, event: AstrMessageEvent, player: BaseMusicPlayer, song: Song
    ) -> bool:
        logger.debug(f"开始发送文件模式：{song.name}")
        
        if not song.audio_url:
            logger.debug(f"歌曲 {song.name} 没有audio_url，尝试获取")
            song = await player.fetch_extra(song, prefer_high_quality=True)
        if not song.audio_url:
            logger.warning(f"【{song.name}】音频获取失败")
            await event.send(event.plain_result(f"【{song.name}】音频获取失败"))
            return False

        logger.debug(f"正在下载歌曲：{song.audio_url}")
        future, position = self.downloader.enqueue(song.audio_url)
        if position == 0:
            logger.debug(f"歌曲 {song.name} 命中缓存，跳过下载")
        else:
            await event.send(event.plain_result(f"已添加到下载队列，当前排第 {position} 位"))
        try:
            file_path = await future
        except Exception as e:
            logger.error(f"【{song.name}】下载异常: {e}")
            await event.send(event.plain_result(f"【{song.name}】下载失败: {e}"))
            return False

        async def send_by_url():
            try:
                file_name_url = f"{song.name}_{song.artists}.mp3"
                if song.audio_url:
                    logger.debug(f"尝试通过URL发送文件：{file_name_url}")
                    seg_url = File(name=file_name_url, url=song.audio_url)
                    await event.send(event.chain_result([seg_url]))
                    return True
            except Exception as e_url:
                logger.error(f"URL 发送失败: {e_url}")
                return False
            return False

        if not file_path:
            logger.warning(f"【{song.name}】下载失败，尝试直接发送 URL")
            if await send_by_url():
                return True
            await event.send(
                event.plain_result(f"【{song.name}】音频文件下载和发送均失败")
            )
            return False

        try:
            file_name = f"{song.name}_{song.artists}{file_path.suffix}"
            logger.debug(f"尝试发送本地文件：{file_name}，路径：{file_path}")
            seg = File(name=file_name, file=str(file_path.resolve()))
            await event.send(event.chain_result([seg]))
            logger.debug(f"文件发送成功：{file_name}")
            return True
        except Exception as e:
            logger.warning(f"【{song.name}】本地文件发送失败: {e}，尝试直接发送 URL")
            if await send_by_url():
                return True

            await event.send(
                event.plain_result(f"【{song.name}】音频文件发送失败: {e}")
            )
            return False

    async def send_text(
        self, event: AstrMessageEvent, player: BaseMusicPlayer, song: Song
    ) -> bool:
        try:
            song = await player.fetch_extra(song, prefer_high_quality=True)
            info = song.to_lines()
            await event.send(event.plain_result(info))
            return True
        except Exception as e:
            logger.error(f"发送歌曲信息失败: {e}")
            return False

    def _get_sender(self, mode: str):
        return {
            "record": self.send_record,
            "file": self.send_file,
            "text": self.send_text,
        }.get(mode)

    def _is_mode_supported(
        self, mode: str, event: AstrMessageEvent
    ) -> bool:
        platform = event.get_platform_name()
        match mode:
            case "text":
                return True
            case "record":
                return platform in self.cfg.record_supported
            case "file":
                return platform in self.cfg.file_supported
            case _:
                return False

    async def send_song(
        self,
        event: AstrMessageEvent,
        player: BaseMusicPlayer,
        song: Song,
        modes: list[str] | None = None,
    ):
        logger.debug(
            f"{event.get_sender_name()}（{event.get_sender_id()}）点歌："
            f"{player.platform.display_name} -> {song.name}_{song.artists}"
        )

        sent = False
        target_modes = modes if modes is not None else self.cfg.real_send_modes

        for mode in target_modes:
            if not self._is_mode_supported(mode, event):
                logger.debug(f"{mode} 不支持，跳过")
                continue

            sender = self._get_sender(mode)
            if not sender:
                continue

            try:
                ok = await sender(event, player, song)
            except Exception as e:
                logger.error(f"{mode} 发送异常: {e}")
                ok = False

            if ok:
                logger.debug(f"{mode} 发送成功")
                sent = True
                break
            else:
                logger.debug(f"{mode} 发送失败，尝试下一种")

        if not sent:
            await event.send(event.plain_result("歌曲发送失败"))

        if sent and self.cfg.enable_comments:
            await self.send_comment(event, player, song)
