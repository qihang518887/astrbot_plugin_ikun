from typing import ClassVar

from astrbot.api import logger

from ..config import PluginConfig
from ..model import Platform, Song
from ..qq_sign import build_search_data, get_sign
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
        # 构建请求数据
        data = build_search_data(keyword, page=1, limit=limit)
        sign = get_sign(data)

        # 使用洛雪音乐的签名方式调用QQ音乐API
        result = await self._request(
            url=f"https://u.y.qq.com/cgi-bin/musics.fcg?sign={sign}",
            method="POST",
            data=data,
            headers={
                "User-Agent": "QQMusic 14090508(android 12)",
                "Content-Type": "application/json",
            },
        )

        if not isinstance(result, dict):
            logger.error(f"QQ音乐搜索返回了意料之外的数据：{result}")
            return []

        # 检查返回码
        if result.get("code") != 0:
            logger.error(f"QQ音乐搜索失败: {result}")
            return []

        req_data = result.get("req", {})
        if req_data.get("code") != 0:
            logger.error(f"QQ音乐搜索请求失败: {req_data}")
            return []

        # 解析歌曲列表
        song_list = req_data.get("data", {}).get("body", {}).get("item_song", [])
        songs = []

        for s in song_list[:limit]:
            # 检查是否有media_mid
            file_info = s.get("file", {})
            if not file_info.get("media_mid"):
                continue

            # 获取歌手名称
            singers = s.get("singer", [])
            artists = "、".join(singer.get("name", "") for singer in singers)

            # 获取歌曲ID
            song_id = s.get("mid", "")

            # 获取封面
            album = s.get("album", {})
            album_mid = album.get("mid", "")
            cover_url = f"https://y.gtimg.cn/music/photo_new/T002R500x500M000{album_mid}.jpg" if album_mid else ""

            songs.append(
                Song(
                    id=song_id,
                    name=s.get("title", ""),
                    artists=artists,
                    duration=s.get("interval", 0) * 1000,  # 转换为毫秒
                    cover_url=cover_url,
                    source="tx",
                )
            )

        return songs
