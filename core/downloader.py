import asyncio
import shutil
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import aiofiles
import aiohttp

from astrbot.api import logger

from .config import PluginConfig


@dataclass
class _DownloadTask:
    url: str
    future: asyncio.Future = field(default_factory=lambda: asyncio.get_event_loop().create_future())


class Downloader:
    def __init__(self, config: PluginConfig):
        self.cfg = config
        self.songs_dir = self.cfg.songs_dir
        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(proxy=self.cfg.http_proxy, timeout=timeout)
        self._queue: asyncio.Queue[_DownloadTask] = asyncio.Queue()
        self._count = 0
        self._worker_task: asyncio.Task | None = None

    async def initialize(self):
        if self.cfg.clear_cache:
            self._ensure_cache_dir()
        self._worker_task = asyncio.create_task(self._worker_loop())

    async def terminate(self):
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        await self.session.close()

    async def close(self):
        await self.terminate()

    def _ensure_cache_dir(self) -> None:
        if self.songs_dir.exists():
            shutil.rmtree(self.songs_dir)
        self.songs_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"缓存目录已重建：{self.songs_dir}")

    async def _worker_loop(self):
        try:
            while True:
                task = await self._queue.get()
                try:
                    result = await self._do_download(task.url)
                    if not task.future.done():
                        task.future.set_result(result)
                except Exception as e:
                    if not task.future.done():
                        task.future.set_exception(e)
                finally:
                    self._count -= 1
                    self._queue.task_done()
        except asyncio.CancelledError:
            while not self._queue.empty():
                try:
                    task = self._queue.get_nowait()
                    if not task.future.done():
                        task.future.cancel()
                    self._queue.task_done()
                except asyncio.QueueEmpty:
                    break
            raise

    async def enqueue(self, url: str) -> tuple[asyncio.Future, int]:
        """将下载任务加入队列，返回 (future, 你的位置)。位置从1开始。"""
        task = _DownloadTask(url)
        self._count += 1
        position = self._count
        await self._queue.put(task)
        return task.future, position

    async def _do_download(self, url: str) -> Path | None:
        song_uuid = uuid.uuid4().hex
        file_path = self.songs_dir / f"{song_uuid}.mp3"
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.error(f"歌曲下载失败，HTTP 状态码：{response.status}")
                    return None
                async with aiofiles.open(file_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(1024):
                        await f.write(chunk)

            logger.debug(f"歌曲下载完成，保存在：{file_path}")
            return file_path

        except Exception as e:
            logger.error(f"歌曲下载失败，错误信息：{e}")
            return None

    async def download_song(self, url: str) -> Path | None:
        future, _ = await self.enqueue(url)
        return await future

    async def download_image(self, url: str, close_ssl: bool = True) -> bytes | None:
        url = url.replace("https://", "http://") if close_ssl else url
        try:
            async with self.session.get(url) as response:
                img_bytes = await response.read()
                return img_bytes
        except Exception as e:
            logger.error(f"图片下载失败: {e}")
