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


def parse_user_input(arg: str) -> tuple[int, list[str] | None, str | None]:
    parts = arg.split()
    index = 0
    way = None
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
            else:
                return 0, None, "模式数字应为 1-3：1语音 2文件 3文本"
        else:
            way = MODE_MAP_CN.get(second_part)
            if way is None:
                return (
                    0,
                    None,
                    f"未知模式「{second_part}」，可用模式：语音/文件/文本 或 1/2/3",
                )
    modes = mode_map.get(way) if way else None
    return index, modes, None
