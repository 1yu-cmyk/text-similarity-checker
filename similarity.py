# -*- coding: utf-8 -*-
"""
文本相似度计算核心模块
=========================

本模块实现了多种常用的文本相似度算法，是本系统（基于多算法融合的中文
文本相似度分析与查重系统）的核心。所有算法均基于本地计算，不依赖任何
在线 API，具有轻量化、离线可用的特点。

已实现的算法：
    1. TF-IDF 余弦相似度   —— 基于词频-逆文档频率的向量空间模型
    2. Jaccard 相似度      —— 基于词集合交并比
    3. 编辑距离相似度      —— 基于字符级 Levenshtein 编辑距离
    4. SimHash 相似度      —— 基于 SimHash 指纹与海明距离
    5. 加权融合相似度      —— 将以上算法按权重线性融合
    6. 批量两两比对        —— 多文档之间计算相似度矩阵

作者：___（请填写姓名）
日期：2025-09
"""

import re
import hashlib
from collections import Counter

import numpy as np
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer

# ---------------------------------------------------------------------------
# 停用词表
# 中文文本中大量出现、但几乎不携带语义信息的词（如"的、了、和"等）。
# 在分词后需要将其过滤，以提升相似度计算的准确性。
# ---------------------------------------------------------------------------
STOPWORDS = set(
    """
    的 了 和 是 在 我 有 就 不 人 都 一 一个 上 也 很 到 说 要 去 你
    会 着 没有 看 好 自己 这 那 他 她 它 我们 你们 他们 这个 那个
    什么 怎么 为什么 还是 但是 因为 所以 如果 虽然 而且 并且 或者
    以及 等 等等 之 于 与 及 被 把 让 给 对 从 向 为 以 关于 通过
    """.split()
)


# ---------------------------------------------------------------------------
# 预处理函数
# ---------------------------------------------------------------------------
def preprocess(text):
    """对中文文本进行预处理：清洗 → 分词 → 去停用词。

    参数:
        text: 原始文本字符串。
    返回:
        list[str]: 分词后并过滤停用词得到的词语列表。
    """
    # 1. 只保留中文字符、英文字母和数字，去掉标点、换行等噪声
    text = re.sub(r"[^一-龥a-zA-Z0-9]", " ", text)

    # 2. 使用 jieba 进行中文分词
    words = jieba.cut(text)

    # 3. 过滤空白词、停用词，以及长度过短的单字（单字噪声较大）
    result = [
        w.strip()
        for w in words
        if w.strip() and w.strip() not in STOPWORDS and len(w.strip()) > 1
    ]
    return result


def _tokenize(text):
    """将文本预处理为用空格连接的字符串，供 TfidfVectorizer 使用。"""
    return " ".join(preprocess(text))


# ---------------------------------------------------------------------------
# 1. TF-IDF 余弦相似度
# ---------------------------------------------------------------------------
def cosine_similarity_tfidf(text1, text2):
    """计算两段文本的 TF-IDF 余弦相似度。

    TF-IDF（词频-逆文档频率）是一种经典的信息检索权重计算方法：某个词
    在一篇文档中出现的次数越多、而在其他文档中出现的次数越少，则它对
    这篇文档的代表性就越强。将每段文本表示成 TF-IDF 向量后，用两个向量
    夹角的余弦值衡量其相似程度，取值范围为 [0, 1]，越接近 1 越相似。

    参数:
        text1, text2: 待比较的两段文本字符串。
    返回:
        float: 余弦相似度，范围 [0, 1]。
    """
    vectorizer = TfidfVectorizer()
    try:
        # 对两段文本一起做 TF-IDF 向量化（共享同一词表）
        tfidf = vectorizer.fit_transform([_tokenize(text1), _tokenize(text2)])
    except ValueError:
        # 若两段文本分词后均为空（如只有停用词），则无法向量化
        return 0.0

    matrix = tfidf.toarray()
    vec1, vec2 = matrix[0], matrix[1]

    dot = float(np.dot(vec1, vec2))
    norm = float(np.linalg.norm(vec1) * np.linalg.norm(vec2))
    if norm == 0:
        return 0.0
    return dot / norm


# ---------------------------------------------------------------------------
# 2. Jaccard 相似度
# ---------------------------------------------------------------------------
def jaccard_similarity(text1, text2):
    """计算两段文本的 Jaccard 相似度。

    Jaccard 相似度衡量两个集合的交集与并集之比，即：
        Jaccard = |A ∩ B| / |A ∪ B|
    在本系统中，集合元素为分词后的词语。该指标直观、计算简单，但忽略了
    词频信息，适合作为余弦相似度的补充。

    参数:
        text1, text2: 待比较的两段文本字符串。
    返回:
        float: Jaccard 相似度，范围 [0, 1]。
    """
    set1 = set(preprocess(text1))
    set2 = set(preprocess(text2))
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)


# ---------------------------------------------------------------------------
# 3. 编辑距离相似度
# ---------------------------------------------------------------------------
def _levenshtein_distance(s1, s2):
    """计算两个字符串的 Levenshtein 编辑距离（动态规划实现）。

    编辑距离指：把一个字符串通过"插入、删除、替换"三种基本操作转换成
    另一个字符串所需的最少操作次数。
    """
    len1, len2 = len(s1), len(s2)
    # dp[i][j] 表示 s1 前 i 个字符与 s2 前 j 个字符的编辑距离
    dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]

    for i in range(len1 + 1):
        dp[i][0] = i
    for j in range(len2 + 1):
        dp[0][j] = j

    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j],      # 删除
                                   dp[i][j - 1],      # 插入
                                   dp[i - 1][j - 1])  # 替换
    return dp[len1][len2]


def levenshtein_similarity(text1, text2):
    """计算两段文本基于编辑距离的相似度。

    将编辑距离归一化为相似度：similarity = 1 - 距离 / 较长串长度。
    这里在"字符级"上进行比较，能捕获拼写、用字的细微差异，与基于词的
    方法形成互补。

    参数:
        text1, text2: 待比较的两段文本字符串。
    返回:
        float: 编辑距离相似度，范围 [0, 1]。
    """
    # 清洗文本，去掉空白符，保留字符
    s1 = re.sub(r"\s+", "", text1)
    s2 = re.sub(r"\s+", "", text2)
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0

    dist = _levenshtein_distance(s1, s2)
    return 1 - dist / max(len(s1), len(s2))


# ---------------------------------------------------------------------------
# 4. SimHash 相似度
# ---------------------------------------------------------------------------
def _simhash(words, hashbits=64):
    """根据词语及其权重生成 SimHash 指纹。

    SimHash 是一种局部敏感哈希（LSH）算法：它把高维的词频特征映射为
    固定长度的二进制指纹（默认 64 位），使得"相似文本 → 相似指纹"。
    本实现用词语出现次数作为权重，通过对每个词哈希值的每一位进行加权
    累加，最终按正负确定每一位，得到整数的二进制指纹。

    参数:
        words: 分词后的词语列表（可重复，用于统计词频）。
        hashbits: 指纹位数，默认 64。
    返回:
        int: 生成的 SimHash 指纹。
    """
    # 统计词频，词频越高的词权重越大
    word_weights = Counter(words)

    # v[i] 累计第 i 位上所有词的加权投票（正为 1，负为 0）
    v = [0] * hashbits
    for word, weight in word_weights.items():
        # 用 MD5 得到 128 位哈希，取前 hashbits 位
        h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
        for i in range(hashbits):
            bit = (h >> i) & 1
            v[i] += weight if bit else -weight

    fingerprint = 0
    for i in range(hashbits):
        if v[i] >= 0:
            fingerprint |= (1 << i)
    return fingerprint


def _hamming_distance(h1, h2):
    """计算两个整数的海明距离，即二进制表示中不同位的个数。"""
    return bin(h1 ^ h2).count("1")


def simhash_similarity(text1, text2, hashbits=64):
    """计算两段文本基于 SimHash 指纹的相似度。

    通过比较两份指纹的海明距离（不同位的个数）来判定相似性：
        similarity = 1 - 海明距离 / hashbits
    对于文本查重场景，海明距离 ≤ 3（64 位指纹下）通常可判定为近似重复。

    参数:
        text1, text2: 待比较的两段文本字符串。
        hashbits: 指纹位数，默认 64。
    返回:
        float: SimHash 相似度，范围 [0, 1]。
    """
    h1 = _simhash(preprocess(text1), hashbits)
    h2 = _simhash(preprocess(text2), hashbits)
    return 1 - _hamming_distance(h1, h2) / hashbits


# ---------------------------------------------------------------------------
# 5. 加权融合相似度
# ---------------------------------------------------------------------------
DEFAULT_WEIGHTS = {
    "tfidf": 0.40,       # TF-IDF 余弦相似度，主指标，权重最高
    "jaccard": 0.20,     # Jaccard 相似度
    "levenshtein": 0.20, # 编辑距离相似度
    "simhash": 0.20,     # SimHash 相似度
}


def combined_similarity(text1, text2, weights=None):
    """计算两段文本的加权融合相似度。

    单一算法各有局限（例如 Jaccard 忽略词频、编辑距离只比较字符），
    本函数将多种算法按权重线性融合，得到更稳健的综合得分：
        score = Σ(weight_k × similarity_k)

    参数:
        text1, text2: 待比较的两段文本字符串。
        weights: 可选，各算法的权重字典，缺省使用 DEFAULT_WEIGHTS。
    返回:
        tuple[float, dict]:
            - 融合后的综合相似度，范围 [0, 1]；
            - 各单项算法的得分字典，便于展示与解释。
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    scores = {
        "tfidf": cosine_similarity_tfidf(text1, text2),
        "jaccard": jaccard_similarity(text1, text2),
        "levenshtein": levenshtein_similarity(text1, text2),
        "simhash": simhash_similarity(text1, text2),
    }

    total = 0.0
    weight_sum = 0.0
    for key, w in weights.items():
        if key in scores:
            total += w * scores[key]
            weight_sum += w

    # 若权重和为 0（异常情况），退化为等权平均
    if weight_sum == 0:
        weight_sum = len(scores)
        total = sum(scores.values())

    return total / weight_sum, scores


# ---------------------------------------------------------------------------
# 6. 批量两两比对
# ---------------------------------------------------------------------------
def batch_compare(docs, names=None):
    """对多篇文档进行两两比对，返回相似度矩阵。

    参数:
        docs: 文档内容字符串列表，例如 ["文档A内容...", "文档B内容..."]。
        names: 可选，文档名称列表，长度需与 docs 一致，缺省用索引命名。
    返回:
        tuple[np.ndarray, list[str]]:
            - 相似度矩阵 matrix，matrix[i][j] 为第 i、j 篇文档的融合相似度；
            - 文档名称列表 names。
    """
    n = len(docs)
    if names is None or len(names) != n:
        names = [f"文档{i + 1}" for i in range(n)]

    matrix = np.zeros((n, n))
    for i in range(n):
        matrix[i][i] = 1.0  # 自己与自己的相似度为 1
        for j in range(i + 1, n):
            score, _ = combined_similarity(docs[i], docs[j])
            matrix[i][j] = matrix[j][i] = score
    return matrix, names


# ---------------------------------------------------------------------------
# 便捷入口：直接运行本文件时可做简单自测
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    t1 = "我喜欢在周末去公园散步，呼吸新鲜空气。"
    t2 = "我喜欢周末去公园散步，呼吸新鲜空气。"
    t3 = "今天的股票市场出现了大幅波动。"

    total, scores = combined_similarity(t1, t2)
    print("相似文本 vs 相似文本：")
    print("  综合得分 = {:.4f}".format(total))
    print("  各算法得分 =", {k: round(v, 4) for k, v in scores.items()})

    total2, _ = combined_similarity(t1, t3)
    print("\n相似文本 vs 无关文本：")
    print("  综合得分 = {:.4f}".format(total2))
