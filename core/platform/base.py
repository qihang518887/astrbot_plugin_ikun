import json
from abc import ABC, abstractmethod
from typing import ClassVar

import aiohttp

from astrbot.api import logger

from ..config import PluginConfig
from ..lx_api import LxMusicAPI
from ..model import Platform, Song


class BaseMusicPlayer(ABC):
    _registry: ClassVar[list[type["BaseMusicPlayer"]]] = []

    platform: ClassVar[Platform]

    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; WOW64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/55.0.2883.87 Safari/537.36"
        )
    }

    def __init__(self, config: PluginConfig):
        self.cfg = config
        timeout = aiohttp.ClientTimeout(total=30)
        self.session = aiohttp.ClientSession(proxy=self.cfg.http_proxy, timeout=timeout)
        self.lx_api = LxMusicAPI(
            proxy=self.cfg.http_proxy,
            js_url=self.cfg.lx_js_url or None,
        )
        self._initialized = False

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if ABC not in cls.__bases__:
            BaseMusicPlayer._registry.append(cls)

    @classmethod
    def get_all_subclass(cls) -> list[type["BaseMusicPlayer"]]:
        return cls._registry

    async def async_initialize(self):
        """异步初始化，加载JS配置"""
        if not self._initialized:
            await self.lx_api.initialize()
            self._initialized = True

    @abstractmethod
    async def fetch_songs(
        self, keyword: str, limit: int, extra: str | None = None
    ) -> list[Song]:
        raise NotImplementedError

    async def fetch_extra(self, song: Song) -> Song:
        if song.audio_url:
            return song

        if not song.source:
            logger.warning(f"歌曲 {song.name} 没有音源信息")
            return song

        url = await self.lx_api.get_music_url(
            source=song.source,
            music_id=song.id,
            quality=self.cfg.lx_quality,
        )

        if url:
            song.audio_url = url

        return song

    async def fetch_comments(self, song: Song) -> Song:
        if song.comments:
            return song
        return song

    async def fetch_lyrics(self, song: Song) -> Song:
        if song.lyrics:
            return song
        return song

    async def resolve_lyrics(self, song: Song) -> Song:
        lyrics = song.lyrics.strip() if isinstance(song.lyrics, str) else ""
        if not lyrics.startswith(("http://", "https://")):
            return song

        try:
            async with self.session.get(lyrics, headers=self.HEADERS) as resp:
                if resp.status != 200:
                    logger.warning(f"歌词 URL 请求返回 {resp.status}: {lyrics}")
                    return song

                content = (await resp.text()).strip("\ufeff").strip()
                if content:
                    song.lyrics = content
        except Exception as e:
            logger.warning(f"{self.__class__.__name__} resolve_lyrics 失败: {e}")

        return song

    async def close(self):
        if not self.session.closed:
            await self.session.close()
        await self.lx_api.close()

    async def _request(
        self,
        url: str,
        *,
        method: str = "GET",
        data: dict | bytes | None = None,
        headers: dict | None = None,
        cookies: dict | None = None,
        params: dict | None = None,
        ssl: bool = True,
    ):
        headers = headers or self.HEADERS

        if method.upper() == "POST":
            async with self.session.post(
                url, data=data, headers=headers, cookies=cookies, params=params, ssl=ssl
            ) as resp:
                return await self._parse_response(resp)

        async with self.session.get(
            url, headers=headers, cookies=cookies, params=params, ssl=ssl
        ) as resp:
            return await self._parse_response(resp)

    async def _parse_response(self, resp: aiohttp.ClientResponse):
        try:
            resp_text = await resp.text()

            if resp.status != 200:
                logger.warning(f"HTTP 请求返回 {resp.status}: {resp_text[:200]}")
                return None

            if not resp_text.strip():
                logger.warning("HTTP 响应为空")
                return None

            try:
                return json.loads(resp_text)
            except json.JSONDecodeError:
                return resp_text

        except Exception as e:
            logger.warning(f"解析响应失败: {e}")
            return None
