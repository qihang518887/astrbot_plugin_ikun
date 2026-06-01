import json
import re
from pathlib import Path

import aiohttp

from astrbot.api import logger


class LxMusicAPI:
    """洛雪音乐API"""

    DEFAULT_API_URL = "https://c.wwwweb.top"
    DEFAULT_API_KEY = "IKM-P09400001-ktWbLCNWD5Ac10Ko-r7"

    DEFAULT_MUSIC_QUALITY = {
        "kg": ["128k", "320k", "flac", "flac24bit", "hires", "atmos", "master"],
        "kw": ["128k", "320k", "flac", "flac24bit", "hires"],
        "tx": ["128k", "320k", "flac", "flac24bit", "hires", "atmos", "atmos_plus", "master"],
        "wy": ["128k", "320k", "flac", "flac24bit", "hires", "atmos", "master"],
    }

    def __init__(self, proxy: str | None = None, js_url: str | None = None):
        self.session = aiohttp.ClientSession(proxy=proxy)
        self.proxy = proxy
        self.js_url = js_url
        self.api_url = self.DEFAULT_API_URL
        self.api_key = self.DEFAULT_API_KEY
        self.music_quality = self.DEFAULT_MUSIC_QUALITY.copy()

    async def initialize(self):
        """初始化API配置，如果设置了JS URL则从JS文件解析"""
        if self.js_url:
            await self._load_js_config()

    async def close(self):
        if not self.session.closed:
            await self.session.close()

    async def _fetch_js_content(self, url: str) -> str | None:
        """从URL获取JS文件内容"""
        try:
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    logger.error(f"获取JS文件失败: HTTP {resp.status}")
                    return None
                return await resp.text()
        except Exception as e:
            logger.error(f"获取JS文件失败: {e}")
            return None

    def _read_local_js(self, path: str) -> str | None:
        """读取本地JS文件内容"""
        try:
            file_path = Path(path)
            if not file_path.exists():
                logger.error(f"JS文件不存在: {path}")
                return None
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.error(f"读取JS文件失败: {e}")
            return None

    def _parse_js_config(self, js_content: str) -> bool:
        """解析JS文件中的配置"""
        try:
            # 解析 API_URL
            api_url_match = re.search(
                r'const\s+API_URL\s*=\s*["\']([^"\']+)["\']', js_content
            )
            if api_url_match:
                self.api_url = api_url_match.group(1)
                logger.debug(f"解析到 API_URL: {self.api_url}")

            # 解析 API_KEY
            api_key_match = re.search(
                r'const\s+API_KEY\s*=\s*["\']([^"\']+)["\']', js_content
            )
            if api_key_match:
                self.api_key = api_key_match.group(1)
                logger.debug(f"解析到 API_KEY: {self.api_key}")

            # 解析 MUSIC_QUALITY
            quality_match = re.search(
                r'const\s+MUSIC_QUALITY\s*=\s*JSON\.parse\(\s*["\'](.+?)["\']\s*\)',
                js_content,
            )
            if quality_match:
                quality_json_str = quality_match.group(1)
                # 处理转义的引号
                quality_json_str = quality_json_str.replace('\\"', '"')
                self.music_quality = json.loads(quality_json_str)
                logger.debug(f"解析到 MUSIC_QUALITY: {list(self.music_quality.keys())}")
            else:
                # 尝试直接解析 JSON 格式
                quality_match2 = re.search(
                    r'const\s+MUSIC_QUALITY\s*=\s*(\{[^;]+\})', js_content
                )
                if quality_match2:
                    quality_json_str = quality_match2.group(1)
                    self.music_quality = json.loads(quality_json_str)
                    logger.debug(f"解析到 MUSIC_QUALITY: {list(self.music_quality.keys())}")

            return True

        except Exception as e:
            logger.error(f"解析JS配置失败: {e}")
            return False

    async def _load_js_config(self):
        """加载JS配置"""
        js_content = None

        if self.js_url.startswith(("http://", "https://")):
            js_content = await self._fetch_js_content(self.js_url)
        else:
            js_content = self._read_local_js(self.js_url)

        if js_content:
            if self._parse_js_config(js_content):
                logger.info(f"已从JS文件加载配置，API地址: {self.api_url}")
            else:
                logger.warning("JS文件解析失败，使用默认配置")
        else:
            logger.warning("无法获取JS文件内容，使用默认配置")

    async def get_music_url(self, source: str, music_id: str, quality: str = "320k") -> str | None:
        """
        获取音乐播放URL

        :param source: 音源类型 (kg, kw, tx, wy)
        :param music_id: 歌曲ID
        :param quality: 音质 (128k, 320k, flac, flac24bit, hires, atmos, master等)
        :return: 音乐URL或None
        """
        if source not in self.music_quality:
            logger.error(f"不支持的音源: {source}")
            return None

        available_qualities = self.music_quality[source]
        if quality not in available_qualities:
            quality = available_qualities[0]
            logger.warning(f"音质不支持，使用默认: {quality}")

        try:
            async with self.session.post(
                f"{self.api_url}/music/url",
                json={
                    "source": source,
                    "musicId": music_id,
                    "quality": quality,
                },
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "lx-music-request/1.0",
                    "X-Api-Key": self.api_key,
                },
            ) as resp:
                if resp.status != 200:
                    logger.error(f"API请求失败: {resp.status}")
                    return None

                data = await resp.json()
                code = data.get("code")

                if code == 200:
                    return data.get("url")
                elif code == 403:
                    logger.error("API鉴权失败")
                elif code == 429:
                    logger.error("API请求过速")
                elif code == 500:
                    logger.error(f"获取URL失败: {data.get('message', '未知错误')}")
                else:
                    logger.error(f"未知错误: {data.get('message', '未知错误')}")

                return None

        except Exception as e:
            logger.error(f"获取音乐URL失败: {e}")
            return None

    def get_supported_qualities(self, source: str) -> list[str]:
        """获取指定音源支持的音质列表"""
        return self.music_quality.get(source, [])

    def get_available_sources(self) -> list[str]:
        """获取所有可用的音源列表"""
        return list(self.music_quality.keys())
