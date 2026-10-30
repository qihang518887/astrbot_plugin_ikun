from enum import IntEnum


class SendMode(IntEnum):
    RECORD = 1
    FILE = 2
    TEXT = 3


MODE_MAP_CN: dict[str, SendMode] = {
    "语音": SendMode.RECORD,
    "文件": SendMode.FILE,
    "文本": SendMode.TEXT,
    "record": SendMode.RECORD,
    "file": SendMode.FILE,
    "text": SendMode.TEXT,
}


def parse_send_mode(val: str | None) -> list[str] | None:
    """解析发送模式字符串为模式列表（例如 ['record']、['file']）。
    若为空或无法识别，返回 None（表示使用插件默认配置）。
    """
    if not val:
        return None
    v = str(val).strip().lower()
    if not v:
        return None

    # 精确匹配 MODE_MAP_CN
    if v in MODE_MAP_CN:
        way = MODE_MAP_CN[v]
        mode_map = {
            SendMode.RECORD: ["record"],
            SendMode.FILE: ["file"],
            SendMode.TEXT: ["text"],
        }
        return mode_map.get(way)

    # 包含关键字匹配（优先匹配文件类关键词）
    if any(k in v for k in ["file", "文件", "mp3", "文档"]):
        return ["file"]
    if any(k in v for k in ["record", "voice", "语音", "录音"]):
        return ["record"]
    if any(k in v for k in ["text", "文本", "文字", "链接", "link", "url"]):
        return ["text"]

    return None


def parse_user_input(arg: str) -> tuple[int, list[str] | None, str | None]:
    parts = arg.split()
    index = 0
    modes = None
    mode_map = {
        SendMode.RECORD: ["record"],
        SendMode.FILE: ["file"],
        SendMode.TEXT: ["text"],
    }

    if len(parts) == 1 and parts[0].isdigit():
        index = int(parts[0])

    elif len(parts) == 2 and parts[0].isdigit():
        index = int(parts[0])
        second_part = parts[1]

        if second_part.isdigit():
            mode_value = int(second_part)
            if 1 <= mode_value <= 3:
                way = SendMode(mode_value)
                modes = mode_map.get(way)
            else:
                return 0, None, "模式数字应为 1-3：1语音 2文件 3文本"
        else:
            modes = parse_send_mode(second_part)
            if modes is None:
                return (
                    0,
                    None,
                    f"未知模式「{second_part}」，可用模式：语音/文件/文本 或 1/2/3",
                )
    return index, modes, None
