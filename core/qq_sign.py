import hashlib
import base64
import random
import json
import re

# QQ音乐签名算法 - 移植自musicdl项目

PART_1_INDEXES = [23, 14, 6, 36, 16, 40, 7, 19]
PART_2_INDEXES = [16, 1, 32, 12, 19, 27, 8, 5]
SCRAMBLE_VALUES = [89, 39, 179, 150, 218, 82, 58, 252, 177, 52, 186, 123, 120, 64, 242, 133, 143, 161, 121, 179]


def zzc_sign(request: dict) -> str:
    """QQ音乐签名算法 - 移植自musicdl"""
    # 过滤掉索引40（超出SHA1哈希范围）
    valid_indexes = [i for i in PART_1_INDEXES if i < 40]
    
    # 计算SHA1哈希（与orjson.dumps行为一致）
    request_str = json.dumps(request, separators=(',', ':'), ensure_ascii=False)
    hash_str = hashlib.sha1(request_str.encode('utf-8')).hexdigest().upper()
    
    # 计算各部分
    part1 = "".join(hash_str[i] for i in valid_indexes)
    part2 = "".join(hash_str[i] for i in PART_2_INDEXES)
    part3 = bytearray(20)
    for i, v in enumerate(SCRAMBLE_VALUES):
        part3[i] = v ^ int(hash_str[i * 2:i * 2 + 2], 16)
    
    # Base64编码并移除特殊字符
    b64_part = re.sub(r'[\\/+=]', '', base64.b64encode(part3).decode('utf-8'))
    
    return f"zzc{part1}{b64_part}{part2}".lower()


def build_search_data(keyword: str, page: int = 1, limit: int = 30) -> dict:
    """构建QQ音乐搜索请求数据"""
    searchid = str(random.randint(1, 20) * 18014398509481984 + 
                   random.randint(0, 4194304) * 4294967296 + 
                   round(random.random() * 1000) % (24 * 60 * 60 * 1000))
    
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
                "searchid": searchid,
                "query": keyword,
                "page_num": page,
                "num_per_page": limit,
                "highlight": 1,
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
    return zzc_sign(data)
