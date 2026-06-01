from typing import ClassVar
import json

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

        # 将数据转换为bytes（与musicdl一致）
        data_bytes = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

        # 使用洛雪音乐的签名方式调用QQ音乐API
        result = await self._request(
            url=f"https://u.y.qq.com/cgi-bin/musics.fcg",
            method="POST",
            data=data_bytes,
            headers={
                "User-Agent": "QQMusic 14090508(android 12)",
                "Content-Type": "application/json",
            },
            params={"sign": sign},
        )

        if not isinstance(result, dict):
            logger.error(f"QQ音乐搜索返回了意料之外的数据：{result}")
            return []

        # 调试：打印返回数据的keys
        logger.debug(f"QQ音乐搜索返回keys: {list(result.keys())}")
        
        # 检查返回码
        if result.get("code") != 0:
            logger.error(f"QQ音乐搜索失败: code={result.get('code')}, result={result}")
            return []

        # 解析歌曲列表 - 尝试多种响应结构
        song_list = []
        
        # 方式1: music.search.SearchCgiService.DoSearchForQQMusicMobile
        search_data = result.get("music.search.SearchCgiService.DoSearchForQQMusicMobile", {})
        if search_data.get("code") == 0:
            song_list = search_data.get("data", {}).get("body", {}).get("item_song", [])
        
        # 方式2: req
        if not song_list:
            req_data = result.get("req", {})
            if req_data.get("code") == 0:
                song_list = req_data.get("data", {}).get("body", {}).get("item_song", [])
        
        # 方式3: 直接在data中
        if not song_list:
            data = result.get("data", {})
            if isinstance(data, dict):
                song_list = data.get("body", {}).get("item_song", [])

        if not song_list:
            logger.error(f"QQ音乐搜索未找到歌曲列表，完整响应: {json.dumps(result, ensure_ascii=False)[:500]}")
            return []

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
