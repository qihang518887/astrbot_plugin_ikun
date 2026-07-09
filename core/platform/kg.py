from typing import ClassVar

from astrbot.api import logger

from ..config import PluginConfig
from ..model import Platform, Song
from .base import BaseMusicPlayer


class KuGouMusic(BaseMusicPlayer):
    platform: ClassVar[Platform] = Platform(
        name="kugou",
        display_name="酷狗音乐",
        keywords=["kg"],
    )

    def __init__(self, config: PluginConfig):
        super().__init__(config)

    async def fetch_songs(
        self,
        keyword: str,
        limit: int = 5,
        extra: str | None = None,
    ) -> list[Song]:
        # 使用酷狗音乐的搜索API
        result = await self._request(
            url=f"https://songsearch.kugou.com/song_search_v2",
            method="GET",
            data={
                "keyword": keyword,
                "page": 1,
                "pagesize": limit,
                "userid": 0,
                "clientver": "",
                "platform": "WebFilter",
                "filter": 2,
                "iscorrection": 1,
                "privilege_filter": 0,
                "area_code": 1,
            },
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.kugou.com/",
            },
        )

        if not isinstance(result, dict) or result.get("error_code") != 0:
            logger.error(f"酷狗搜索返回了意料之外的数据：{result}")
            return []

        song_list = result.get("data", {}).get("lists", [])
        songs = []

        for s in song_list[:limit]:
            # 获取歌手名称
            singers = s.get("Singers", [])
            artists = "、".join(singer.get("name", "") for singer in singers)

            # 获取歌曲ID和hash
            song_id = s.get("Audioid", "")
            file_hash = s.get("FileHash", "")

            songs.append(
                Song(
                    id=str(song_id),
                    name=s.get("SongName", ""),
                    artists=artists,
                    duration=s.get("Duration", 0) * 1000,  # 转换为毫秒
                    source="kg",
                    note=file_hash,  # 保存hash用于获取URL
                )
            )

        return songs
