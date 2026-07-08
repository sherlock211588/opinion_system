"""
分词增强：自定义词典 + 停用词扩展 + TF-IDF 低频词过滤
"""

import jieba
import jieba.posseg as pseg
from pathlib import Path
from typing import Set, List
import pandas as pd


class EnhancedTokenizer:
    """
    增强版分词器
    - 支持自定义词典加载
    - 支持停用词扩展
    - 支持词性过滤
    """
    
    def __init__(self, stopwords: Set[str] = None, user_dict_path: Path = None):
        self.stopwords = stopwords or set()
        self.user_dict_path = user_dict_path
        
        # 确保 jieba 已初始化（如果缓存损坏，删除缓存后自动重建）
        # 注意：initialize() 不接受参数，直接调用即可
        jieba.initialize()
        
        # 加载自定义词典
        if user_dict_path and user_dict_path.exists():
            try:
                jieba.load_userdict(str(user_dict_path))
                print(f"[OK] 加载自定义词典: {user_dict_path}")
            except Exception as e:
                print(f"[WARN] 自定义词典加载失败: {e}")
        
        # 默认词性过滤（只保留名词、动词、形容词）
        self.allowed_pos = ['n', 'nr', 'ns', 'nt', 'nz', 'v', 'a', 'an', 'vn']
    
    def segment(self, text: str, pos_filter: bool = True) -> List[str]:
        """
        分词并过滤
        pos_filter: 是否启用词性过滤（只保留名词/动词/形容词）
        """
        if not text:
            return []
        
        words = []
        for word, flag in pseg.cut(text):
            # 过滤停用词
            if word in self.stopwords:
                continue
            # 过滤单字
            if len(word) < 2:
                continue
            # 词性过滤
            if pos_filter and flag not in self.allowed_pos:
                continue
            words.append(word)
        
        return words


# ==========================================
# TF-IDF 低频词过滤
# ==========================================
def filter_low_freq_terms(df, text_column: str = 'segmented', min_df: int = 2):
    """
    使用 TF-IDF 的 min_df 参数过滤低频词
    出现次数 < min_df 的词会被忽略
    
    注意：此函数会导入 sklearn，在大数据量时可能较慢
    如果卡死，可以将 min_df 设为 1 或跳过此步骤
    """
    if text_column not in df.columns:
        return df
    
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
    except ImportError:
        print("[WARN] sklearn 未安装，低频词过滤跳过")
        return df
    
    # 如果列是空格分隔的词，直接使用
    corpus = df[text_column].fillna('').tolist()
    
    # 检查是否有非空数据
    if all(len(text.strip()) == 0 for text in corpus):
        print("[WARN] 所有文本为空，低频词过滤跳过")
        return df
    
    try:
        vectorizer = TfidfVectorizer(
            min_df=min_df,
            max_df=0.9,
            token_pattern=r'(?u)\b\w+\b'
        )
        
        matrix = vectorizer.fit_transform(corpus)
        # 获取保留的特征词
        kept_features = set(vectorizer.get_feature_names_out())
        
        # 过滤每个文档：只保留被选中的特征词
        def filter_doc(text):
            if not text:
                return ''
            words = text.split()
            filtered = [w for w in words if w in kept_features]
            return ' '.join(filtered)
        
        df[text_column] = df[text_column].apply(filter_doc)
        print(f"[OK] 低频词过滤完成，保留 {len(kept_features)} 个特征词")
        
    except Exception as e:
        print(f"[WARN] 低频词过滤失败: {e}")
    
    return df


# ==========================================
# 测试代码
# ==========================================
if __name__ == '__main__':
    # 测试分词器
    tokenizer = EnhancedTokenizer()
    text = "今日北京市气象台升级发布高温橙色预警信号"
    result = tokenizer.segment(text)
    print(f"分词结果: {' '.join(result)}")