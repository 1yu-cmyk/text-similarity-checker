# -*- coding: utf-8 -*-
"""
相似度算法单元测试
==================

使用 pytest 或 unittest 运行：
    python -m pytest tests/ -v
或
    python -m unittest discover -s tests -v
"""

import unittest

from similarity import (
    cosine_similarity_tfidf,
    jaccard_similarity,
    levenshtein_similarity,
    simhash_similarity,
    combined_similarity,
    batch_compare,
)


class TestSimilarity(unittest.TestCase):
    """相似度算法基础测试。"""

    def setUp(self):
        # 三段测试文本：t2 与 t1 高度相似，t3 与 t1 不相关
        self.t1 = "我喜欢在周末去公园散步，呼吸新鲜空气，放松心情。"
        self.t2 = "我喜欢周末去公园散步，呼吸新鲜空气，放松心情。"
        self.t3 = "今天的股票市场出现了大幅波动，投资者情绪紧张。"

    def test_self_similarity(self):
        """文本与自身比较，相似度应接近 1。"""
        self.assertGreater(cosine_similarity_tfidf(self.t1, self.t1), 0.95)
        self.assertGreater(jaccard_similarity(self.t1, self.t1), 0.95)
        self.assertGreater(levenshtein_similarity(self.t1, self.t1), 0.99)
        self.assertGreater(simhash_similarity(self.t1, self.t1), 0.95)

    def test_similar_vs_unrelated(self):
        """相似文本的得分应明显高于无关文本。"""
        sim, _ = combined_similarity(self.t1, self.t2)
        unrel, _ = combined_similarity(self.t1, self.t3)
        self.assertGreater(sim, unrel)

    def test_range(self):
        """所有算法得分应落在 [0, 1] 区间内。"""
        for fn in (
            cosine_similarity_tfidf,
            jaccard_similarity,
            levenshtein_similarity,
            simhash_similarity,
        ):
            v = fn(self.t1, self.t3)
            self.assertGreaterEqual(v, 0.0)
            self.assertLessEqual(v, 1.0)

    def test_batch_compare_shape(self):
        """批量比对应返回正确的矩阵形状，且对角线为 1。"""
        docs = [self.t1, self.t2, self.t3]
        matrix, names = batch_compare(docs)
        self.assertEqual(matrix.shape, (3, 3))
        self.assertEqual(len(names), 3)
        for i in range(3):
            self.assertAlmostEqual(matrix[i][i], 1.0)

    def test_batch_compare_ordering(self):
        """t1 与 t2 的相似度应大于 t1 与 t3。"""
        docs = [self.t1, self.t2, self.t3]
        matrix, _ = batch_compare(docs)
        self.assertGreater(matrix[0][1], matrix[0][2])


if __name__ == "__main__":
    unittest.main()
