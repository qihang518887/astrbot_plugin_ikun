from typing import ClassVar

from astrbot.api import logger

from ..config import PluginConfig
from ..model import Platform, Song
from .base import BaseMusicPlayer

# 网易云音乐默认cookies（来自musicdl）
DEFAULT_COOKIES = {'MUSIC_U': '1eb9ce22024bb666e99b6743b2222f29ef64a9e88fda0fd5754714b900a5d70d993166e004087dd3b95085f6a85b059f5e9aba41e3f2646e3cebdbec0317df58c119e5'}


class NetEaseMusic(BaseMusicPlayer):
    platform: ClassVar[Platform] = Platform(
        name="netease",
        display_name="网易云音乐",
        keywords=["wy"],
    )

    def __init__(self, config: PluginConfig):
        super().__init__(config)

    async def fetch_songs(self, keyword: str, limit=5, extra=None) -> list[Song]:
        # 使用网易云音乐的搜索API（与musicdl一致）
        result = await self._request(
            url="https://music.163.com/api/cloudsearch/pc",
            method="POST",
            data={
                "s": keyword,
                "limit": limit,
                "type": 1,  # 1: 单曲
                "offset": 0,
            },
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36",
                "Referer": "https://music.163.com/",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            cookies=DEFAULT_COOKIES,
        )
        
        if (
            not isinstance(result, dict)
            or "result" not in result
            or "songs" not in result.get("result", {})
        ):
            logger.error(f"网易云搜索返回了意料之外数据：{result}")
            return []

        songs = result["result"]["songs"][:limit]

        return [
            Song(
                id=str(s.get("id")),
                name=s.get("name"),
                artists="、".join(a["name"] for a in s.get("ar", [])),
                duration=s.get("dt"),
                cover_url=s.get("al", {}).get("picUrl"),
                source="wy",
            )
            for s in songs
        ]
