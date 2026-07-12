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
    future: asyncio.Future = field(default_factory=lambda: asyncio.get_running_loop().create_future())


class Downloader:
    def __init__(self, config: PluginConfig):
        self.cfg = config
        self.songs_dir = self.cfg.songs_dir
        self.session: aiohttp.ClientSession | None = None
        self._queue: asyncio.Queue[_DownloadTask] = asyncio.Queue()
        self._worker_task: asyncio.Task | None = None
        self._cache: dict[str, Path] = {}
        self._pending: dict[str, asyncio.Future] = {}

    async def initialize(self):
        timeout = aiohttp.ClientTimeout(total=60)
        self.session = aiohttp.ClientSession(proxy=self.cfg.http_proxy, timeout=timeout)
        if self.cfg.clear_cache:
            self._ensure_cache_dir()

    async def terminate(self):
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        if self.session:
            await self.session.close()

    async def close(self):
        await self.terminate()

    def _ensure_cache_dir(self) -> None:
        if self.songs_dir.exists():
            shutil.rmtree(self.songs_dir)
        self.songs_dir.mkdir(parents=True, exist_ok=True)
        self._cache.clear()
        logger.debug(f"缓存目录已重建：{self.songs_dir}")

    async def _worker_loop(self):
        try:
            while True:
                task = await self._queue.get()
                try:
                    result = await self._do_download(task.url)
                    if result:
                        self._cache[task.url] = result
                    if not task.future.done():
                        task.future.set_result(result)
                except Exception as e:
                    if not task.future.done():
                        task.future.set_exception(e)
                finally:
                    self._pending.pop(task.url, None)
                    if not task.future.done():
                        task.future.cancel()
                    self._queue.task_done()
        except asyncio.CancelledError:
            while not self._queue.empty():
                try:
                    task = self._queue.get_nowait()
                    self._pending.pop(task.url, None)
                    if not task.future.done():
                        task.future.cancel()
                    self._queue.task_done()
                except asyncio.QueueEmpty:
                    break
            raise

    def enqueue(self, url: str) -> tuple[asyncio.Future, int]:
        """将下载任务加入队列，返回 (future, 位置)。位置=0表示缓存/待处理命中，>0表示排队位置。"""
        if url in self._cache:
            future = asyncio.get_running_loop().create_future()
            future.set_result(self._cache[url])
            return future, 0

        if url in self._pending:
            return self._pending[url], 0

        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._worker_loop())

        task = _DownloadTask(url)
        self._pending[url] = task.future
        position = self._queue.qsize() + 1
        self._queue.put_nowait(task)
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
        future, _ = self.enqueue(url)
        return await future

    async def download_image(self, url: str, close_ssl: bool = True) -> bytes | None:
        url = url.replace("https://", "http://") if close_ssl else url
        try:
            async with self.session.get(url) as response:
                img_bytes = await response.read()
                return img_bytes
        except Exception as e:
            logger.error(f"图片下载失败: {e}")
            return None
