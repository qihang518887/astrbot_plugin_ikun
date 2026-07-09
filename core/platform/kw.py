from typing import ClassVar

from astrbot.api import logger

from ..config import PluginConfig
from ..model import Platform, Song
from .base import BaseMusicPlayer


class KuwoMusic(BaseMusicPlayer):
    platform: ClassVar[Platform] = Platform(
        name="kuwo",
        display_name="酷我音乐",
        keywords=["kw"],
    )

    def __init__(self, config: PluginConfig):
        super().__init__(config)

    async def fetch_songs(
        self,
        keyword: str,
        limit: int = 5,
        extra: str | None = None,
    ) -> list[Song]:
        # 使用酷我音乐的搜索API
        result = await self._request(
            url="http://search.kuwo.cn/r.s",
            method="GET",
            data={
                "client": "kt",
                "all": keyword,
                "pn": 0,
                "rn": limit,
                "uid": "794762570",
                "ver": "kwplayer_ar_9.2.2.1",
                "vipver": "1",
                "show_copyright_off": "1",
                "newver": "1",
                "ft": "music",
                "cluster": "0",
                "strategy": "2012",
                "encoding": "utf8",
                "rformat": "json",
                "vermerge": "1",
                "mobi": "1",
                "issubtitle": "1",
            },
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "http://www.kuwo.cn/",
            },
        )

        if not isinstance(result, dict):
            logger.error(f"酷我搜索返回了意料之外的数据：{result}")
            return []

        song_list = result.get("abslist", [])
        songs = []

        for s in song_list[:limit]:
            # 获取歌曲ID
            music_rid = s.get("MUSICRID", "")
            song_id = music_rid.replace("MUSIC_", "")

            # 获取歌手名称
            artist = s.get("ARTIST", "")

            # 获取歌曲名称
            name = s.get("SONGNAME", "")

            # 获取专辑名称
            album = s.get("ALBUM", "")

            # 获取时长
            duration = int(s.get("DURATION", 0)) * 1000  # 转换为毫秒

            songs.append(
                Song(
                    id=song_id,
                    name=name,
                    artists=artist,
                    duration=duration,
                    source="kw",
                )
            )

        return songs
