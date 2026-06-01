from typing import ClassVar

from astrbot.api import logger

from ..config import PluginConfig
from ..model import Platform, Song
from .base import BaseMusicPlayer


class KuwoMusic(BaseMusicPlayer):
    platform: ClassVar[Platform] = Platform(
        name="kuwo",
        display_name="酷我音乐",
        keywords=["酷我", "酷我点歌", "kw"],
    )

    BASE_URL = "https://music.txqq.pro/"
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:146.0) "
            "Gecko/20100101 Firefox/146.0"
        ),
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "https://music.txqq.pro",
        "Referer": "https://music.txqq.pro",
    }

    def __init__(self, config: PluginConfig):
        super().__init__(config)

    async def fetch_songs(
        self,
        keyword: str,
        limit: int = 5,
        extra: str | None = None,
    ) -> list[Song]:
        result = await self._request(
            url=self.BASE_URL,
            method="POST",
            data={
                "input": keyword,
                "filter": "name",
                "type": "kuwo",
                "page": 1,
            },
            headers=self.HEADERS,
        )
        if not isinstance(result, dict) or "data" not in result:
            logger.error(f"返回了意料之外的数据：{result}")
            return []
        songs = []
        for s in result["data"]:
            songs.append(
                Song(
                    id=s.get("songid"),
                    name=s.get("title"),
                    artists=s.get("author"),
                    cover_url=s.get("pic"),
                    lyrics=s.get("lrc", ""),
                    source="kw",
                )
            )
        return songs[:limit]
