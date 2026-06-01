import hashlib
import base64
import random
import json

# QQ音乐签名算法 - 移植自洛雪音乐

PART_1_INDEXES = [23, 14, 6, 36, 16, 40, 7, 19]
PART_2_INDEXES = [16, 1, 32, 12, 19, 27, 8, 5]
SCRAMBLE_VALUES = [89, 39, 179, 150, 218, 82, 58, 252, 177, 52, 186, 123, 120, 64, 242, 133, 143, 161, 121, 179]


def _sha1_hash(text: str) -> str:
    """计算SHA1哈希"""
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


def _pick_hash_by_idx(hash_str: str, indexes: list) -> str:
    """从哈希字符串中按索引提取字符"""
    return ''.join(hash_str[idx % len(hash_str)] for idx in indexes)


def _base64_encode(data: bytes) -> str:
    """Base64编码并移除特殊字符"""
    return base64.b64encode(data).decode('utf-8').replace('\\', '').replace('/', '').replace('+', '').replace('=', '')


def zzc_sign(text: str) -> str:
    """QQ音乐签名算法"""
    hash_str = _sha1_hash(text)
    part1 = _pick_hash_by_idx(hash_str, PART_1_INDEXES)
    part2 = _pick_hash_by_idx(hash_str, PART_2_INDEXES)
    part3 = bytes([value ^ int(hash_str[i * 2:i * 2 + 2], 16) for i, value in enumerate(SCRAMBLE_VALUES)])
    b64_part = _base64_encode(part3)
    return f"zzc{part1}{b64_part}{part2}".lower()


def build_search_data(keyword: str, page: int = 1, limit: int = 30) -> dict:
    """构建QQ音乐搜索请求数据"""
    return {
        "comm": {
            "ct": "11",
            "cv": "14090508",
            "v": "14090508",
            "tmeAppID": "qqmusic",
            "phonetype": "EBG-AN10",
            "deviceScore": "553.47",
            "devicelevel": "50",
            "newdevicelevel": "20",
            "rom": "HuaWei/EMOTION/EmotionUI_14.2.0",
            "os_ver": "12",
            "OpenUDID": "0",
            "OpenUDID2": "0",
            "QIMEI36": "0",
            "udid": "0",
            "chid": "0",
            "aid": "0",
            "oaid": "0",
            "taid": "0",
            "tid": "0",
            "wid": "0",
            "uid": "0",
            "sid": "0",
            "modeSwitch": "6",
            "teenMode": "0",
            "ui_mode": "2",
            "nettype": "1020",
            "v4ip": "",
        },
        "req": {
            "module": "music.search.SearchCgiService",
            "method": "DoSearchForQQMusicMobile",
            "param": {
                "search_type": 0,
                "searchid": str(random.random())[2:],
                "query": keyword,
                "page_num": page,
                "num_per_page": limit,
                "highlight": 0,
                "nqc_flag": 0,
                "multi_zhida": 0,
                "cat": 2,
                "grp": 1,
                "sin": 0,
                "sem": 0,
            },
        },
    }


def get_sign(data: dict) -> str:
    """获取签名"""
    return zzc_sign(json.dumps(data))
