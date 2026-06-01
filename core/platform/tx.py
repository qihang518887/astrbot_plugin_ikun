from typing import ClassVar

from astrbot.api import logger

from ..config import PluginConfig
from ..model import Platform, Song
from .base import BaseMusicPlayer


class QQMusic(BaseMusicPlayer):
    platform: ClassVar[Platform] = Platform(
        name="qq",
        display_name="QQ音乐",
        keywords=["qq", "QQ点歌", "tx", "qq音乐"],
    )

    def __init__(self, config: PluginConfig):
        super().__init__(config)

    async def fetch_songs(
        self,
        keyword: str,
        limit: int = 5,
        extra: str | None = None,
    ) -> list[Song]:
        # 使用QQ音乐的搜索API
        result = await self._request(
            url="https://c.y.qq.com/soso/fcgi-bin/client_search_cp",
            method="GET",
            data={
                "w": keyword,
                "p": 1,
                "n": limit,
                "format": "json",
                "cr": 1,
                "new_json": 1,
            },
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://y.qq.com/",
            },
        )

        if not isinstance(result, dict) or "data" not in result:
            logger.error(f"QQ音乐搜索返回了意料之外的数据：{result}")
            return []

        song_list = result.get("data", {}).get("song", {}).get("list", [])
        songs = []

        for s in song_list[:limit]:
            # 获取歌手名称
            singers = s.get("singer", [])
            artists = "、".join(singer.get("name", "") for singer in singers)

            # 获取歌曲ID
            song_id = s.get("songmid") or s.get("mid", "")

            # 获取封面
            album_mid = s.get("albummid", "")
            cover_url = f"https://y.gtimg.cn/music/photo_new/T002R500x500M000{album_mid}.jpg" if album_mid else ""

            songs.append(
                Song(
                    id=song_id,
                    name=s.get("songname", s.get("title", "")),
                    artists=artists,
                    duration=s.get("interval", 0) * 1000,  # 转换为毫秒
                    cover_url=cover_url,
                    source="tx",
                )
            )

        return songs
