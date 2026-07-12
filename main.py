import asyncio
import traceback

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.utils.session_waiter import (
    SessionController,
    session_waiter,
)

from .core.config import PluginConfig
from .core.downloader import Downloader
from .core.platform import BaseMusicPlayer
from .core.sender import MusicSender
from .core.utils import parse_user_input


class MusicPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.cfg = PluginConfig(config, context)
        self.players: list[BaseMusicPlayer] = []
        self.keywords: list[str] = []

    async def initialize(self):
        self._register_player()
        
        # 初始化所有播放器的LxMusic API配置
        for player in self.players:
            await player.async_initialize()
        
        self.downloader = Downloader(self.cfg)
        await self.downloader.initialize()
        self.sender = MusicSender(self.cfg, self.downloader)

    async def terminate(self):
        await self.downloader.close()
        for parser in self.players:
            await parser.close()

    def get_player(
        self, name: str | None = None, word: str | None = None
    ) -> BaseMusicPlayer | None:
        for player in self.players:
            if name:
                name_ = name.strip().lower()
                p = player.platform
                if p.display_name.lower() == name_ or p.name.lower() == name_:
                    return player
            elif word:
                word_ = word.strip().lower()
                for keyword in player.platform.keywords:
                    if keyword.lower() in word_:
                        return player

    def _register_player(self):
        all_subclass = BaseMusicPlayer.get_all_subclass()
        for _cls in all_subclass:
            player = _cls(self.cfg)
            self.players.append(player)
            self.keywords.extend(player.platform.keywords)
        logger.debug(f"已注册触发词：{self.keywords}")

    @filter.regex(r"^(wy|qq|kg|kw)\s+")
    async def on_search_song(self, event: AstrMessageEvent):
        cmd, _, arg = event.message_str.partition(" ")
        logger.debug(f"收到消息: cmd={cmd}, arg={arg}")
        if not arg:
            return
        player = self.get_player(word=cmd)
        if not player:
            logger.debug(f"未找到匹配的播放器, cmd={cmd}")
            return
        args = arg.split()
        if args[-1].isdigit():
            index = int(args[-1])
            song_name = " ".join(args[:-1])
        else:
            index = 0
            song_name = arg
        if not song_name:
            yield event.plain_result("未指定歌名")
            return
        logger.debug(f"正在通过{player.platform.display_name}搜索歌曲：{song_name}")
        songs = await player.fetch_songs(
            keyword=song_name, limit=self.cfg.real_song_limit, extra=cmd
        )
        if not songs:
            logger.debug(f"搜索【{song_name}】无结果")
            yield event.plain_result(f"搜索【{song_name}】无结果")
            return

        logger.debug(f"搜索到 {len(songs)} 首歌曲")
        if len(songs) == 1:
            index = 1

        if index and 0 <= index <= len(songs):
            selected_song = songs[int(index) - 1]
            logger.debug(f"用户选择了第 {index} 首歌曲: {selected_song.name}")
            await self.sender.send_song(event, player, selected_song)

        else:
            title = f"【{player.platform.display_name}】"
            
            async def _send_selection():
                try:
                    await self.sender.send_song_selection(event=event, songs=songs, title=title)
                except Exception as e:
                    logger.error(f"发送选歌消息失败: {e}")
            
            asyncio.create_task(_send_selection())

            song_selected = False
            new_search_event = None

            @session_waiter(timeout=self.cfg.timeout)
            async def empty_mention_waiter(
                controller: SessionController, event: AstrMessageEvent
            ):
                nonlocal song_selected, new_search_event
                try:
                    arg = event.message_str.strip()
                    arg_lower = arg.lower()
                    for kw in self.keywords:
                        if kw in arg_lower:
                            new_search_event = event
                            controller.stop()
                            return
                    index, modes, error = parse_user_input(arg)
                    if error:
                        await event.send(event.plain_result(error))
                        return
                    if index == 0:
                        return
                    if index < 1 or index > len(songs):
                        controller.stop()
                        return
                    selected_song = songs[index - 1]
                    song_selected = True
                    controller.stop()
                    asyncio.create_task(
                        self.sender.send_song(event, player, selected_song, modes=modes)
                    )
                except Exception as e:
                    logger.error(f"session_waiter处理异常: {e}")
                    controller.stop()

            try:
                await empty_mention_waiter(event)
            except TimeoutError as _:
                if not song_selected:
                    yield event.plain_result("点歌超时！")
            except Exception as e:
                logger.error(traceback.format_exc())
                logger.error("点歌发生错误" + str(e))
                yield event.plain_result("点歌发生错误，请稍后再试")

            if new_search_event:
                async for result in self.on_search_song(new_search_event):
                    yield result
                return

        event.stop_event()

    @filter.llm_tool()
    async def play_song_by_name(self, event: AstrMessageEvent, song_name: str):
        """
        当用户想听歌时，根据歌名（可含歌手）搜索并播放音乐。
        Args:
            song_name(string): 歌曲名称或包含歌手的关键词
        """
        player = self.players[0] if self.players else None
        if not player:
            return "无可用播放器"
        songs = await player.fetch_songs(keyword=song_name, limit=1)
        if not songs:
            return "没找到相关歌曲"
        await self.sender.send_song(event, player, songs[0])
