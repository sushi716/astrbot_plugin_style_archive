# -*- coding: utf-8 -*-
"""聊天语料自动归档（style_archive）

把群里/私聊里出现的文字消息按天追加到 <archive_dir>/YYYY-MM-DD.jsonl，
为"学我的文风"持续攒语料。只写文件、不调模型、不发消息，开销极小。

要点：
- 机器人自己发的消息会跳过；其他人的消息都记，并用 is_owner 标出哪条是你（OWNER_QQ）写的。
  想只取"你自己说的话"，按 is_owner=true 过滤即可。
- 纯图片/语音/表情包消息跳过（那些交给 meme 插件）；短于 2 字跳过。
- 每天一个文件，方便按时间切分（早期语料 / 近期语料）。
"""
from __future__ import annotations

# -*- coding: utf-8 -*-
# ---- 开源版路径解析：优先环境变量，其次插件自身目录（不依赖任何绝对路径）----
import os
from pathlib import Path as _Path

PLUGIN_DIR = _Path(__file__).resolve().parent
# <AstrBot>/data/plugins/<本插件> -> parents[0]=plugins, [1]=data, [2]=AstrBot 根
ASTRBOT_ROOT = _Path(os.environ.get("ASTRBOT_ROOT") or PLUGIN_DIR.parents[2])
DATA_DIR = _Path(os.environ.get("ASTRBOT_DATA_DIR") or (ASTRBOT_ROOT / "data"))
STATE_DIR = _Path(os.environ.get("ASTRBOT_STATE_DIR") or (PLUGIN_DIR / "state"))
STATE_DIR.mkdir(parents=True, exist_ok=True)


def _state(name: str) -> _Path:
    return STATE_DIR / name


import asyncio
import json
import time
from pathlib import Path

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core.platform.message_type import MessageType

ARCHIVE_DIR = _Path(os.environ.get("STYLE_ARCHIVE_DIR") or (PLUGIN_DIR / "archive"))
OWNER_QQ = {x.strip() for x in os.environ.get("OWNER_QQ", "").split(",") if x.strip()}  # 你的 QQ，可多个
MIN_CHARS = 2
MAX_CHARS = 2000


class StyleArchive(Star):
    def __init__(self, context: Context, config: dict = None):
        super().__init__(context)
        self.config = config or {}
        self._lock = asyncio.Lock()
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        self._warned = False

    async def _append(self, rec: dict) -> None:
        path = ARCHIVE_DIR / f"{time.strftime('%Y-%m-%d')}.jsonl"
        async with self._lock:
            try:
                with path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            except Exception as e:
                if not self._warned:
                    self._warned = True
                    logger.warning(f"[style_archive] 写入失败 {path}: {e}")

    async def _handle(self, event: AstrMessageEvent, kind: str) -> None:
        try:
            text = (event.message_str or "").strip()
            if not (MIN_CHARS <= len(text) <= MAX_CHARS):
                return
            sender = str(event.get_sender_id())
            try:
                self_id = str(event.get_self_id())
            except Exception:
                self_id = ""
            if self_id and sender == self_id:
                return  # 机器人自己发的
            umo = event.unified_msg_origin
            group = ""
            if kind == "group" and ":" in umo:
                group = umo.split(":")[-1]
            await self._append(
                {
                    "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "umo": umo,
                    "kind": kind,
                    "group": group,
                    "sender": sender,
                    "name": (event.get_sender_name() or "")[:32],
                    "is_owner": sender in OWNER_QQ,
                    "scene": "group" if kind == "group" else "chat",
                    "text": text,
                }
            )
        except Exception as e:
            logger.warning(f"[style_archive] record fail: {e}")

    @filter.event_message_type(filter.EventMessageType.PRIVATE_MESSAGE)
    async def on_private(self, event: AstrMessageEvent):
        await self._handle(event, "friend")

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def on_group(self, event: AstrMessageEvent):
        await self._handle(event, "group")
