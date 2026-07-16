"""
通用工具函数
"""

import re
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd


def setup_logger(log_file: Path, level: str = 'INFO') -> logging.Logger:
    """
    配置日志系统：同时输出到文件和控制台
    """
    logger = logging.getLogger('PreprocessLogger')
    logger.setLevel(getattr(logging, level.upper()))
    
    # 避免重复添加 handler
    if logger.handlers:
        return logger
    
    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger


def compute_md5(text: str) -> str:
    """计算文本的 MD5 哈希值"""
    if not text:
        return ''
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def is_valid_body(text: str, min_len: int = 50, max_len: int = 50000) -> bool:
    """判断提取的正文是否有效"""
    if not text or not isinstance(text, str):
        return False
    length = len(text.strip())
    return min_len <= length <= max_len


def normalize_text(text: str) -> str:
    """
    文本标准化：全角转半角、去除多余空白、压缩标点
    """
    if not text:
        return ''
    
    # 全角转半角（英文、数字、标点）
    fullwidth_chars = {
        '！': '!', '＂': '"', '＃': '#', '＄': '$', '％': '%', '＆': '&',
        '＇': "'", '（': '(', '）': ')', '＊': '*', '＋': '+', '，': ',',
        '－': '-', '．': '.', '／': '/', '：': ':', '；': ';', '＜': '<',
        '＝': '=', '＞': '>', '？': '?', '＠': '@', '［': '[', '＼': '\\',
        '］': ']', '＾': '^', '＿': '_', '｀': '`', '｛': '{', '｜': '|',
        '｝': '}', '～': '~', '　': ' '
    }
    for full, half in fullwidth_chars.items():
        text = text.replace(full, half)
    
    # 去除不可见控制字符
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # 合并多余空白
    text = re.sub(r'\s+', ' ', text)
    
    # 压缩连续中文标点
    text = re.sub(r'([！？。，、：；])\1+', r'\1', text)
    
    # 去除首尾空格
    return text.strip()


def extract_keywords_textrank(text: str, top_n: int = 10) -> List[str]:
    """
    使用 TextRank 算法提取关键词（需要安装 textrank4zh）
    如果没有安装，降级使用 TF-IDF 方式
    """
    try:
        from textrank4zh import TextRank4Keyword
        tr4w = TextRank4Keyword()
        tr4w.analyze(text, window=2, lower=True)
        keywords = [item.word for item in tr4w.get_keywords(num=top_n)]
        return keywords
    except ImportError:
        # 降级方案：简单的词频统计
        import jieba.posseg as pseg
        word_freq = {}
        for word, flag in pseg.cut(text):
            if flag.startswith('n') and len(word) > 1:  # 只保留名词
                word_freq[word] = word_freq.get(word, 0) + 1
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:top_n]]