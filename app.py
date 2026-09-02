# -*- coding: utf-8 -*-
"""
文本相似度分析与查重系统 —— Streamlit 前端界面
================================================

本文件基于 Streamlit 构建 Web 界面，提供两种交互模式：
    1. 两篇文本比对：输入/上传两段文本，展示各算法得分与融合得分；
    2. 批量查重：上传多篇文档，生成相似度矩阵与热力图，定位重复文档对。

运行方式（在项目根目录下执行）：
    streamlit run app.py

作者：___（请填写姓名）
日期：2025-09
"""

import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

# 导入核心算法模块
from similarity import (
    combined_similarity,
    batch_compare,
)

# ---------------------------------------------------------------------------
# 页面全局配置
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="文本相似度分析与查重系统",
    page_icon="📄",
    layout="wide",
)

# 设置 matplotlib 中文字体，避免热力图坐标轴中文乱码
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False

# 算法中文名映射，用于展示
ALGO_NAMES = {
    "tfidf": "TF-IDF 余弦相似度",
    "jaccard": "Jaccard 相似度",
    "levenshtein": "编辑距离相似度",
    "simhash": "SimHash 相似度",
}


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------
def interpret(score):
    """根据相似度得分给出结论文案与颜色。

    参数:
        score: 综合相似度得分，范围 [0, 1]。
    返回:
        tuple[str, str]: (结论文案, 对应的十六进制颜色)。
    """
    if score >= 0.80:
        return "高度相似（疑似抄袭 / 重复）", "#d32f2f"
    if score >= 0.60:
        return "较高相似（存在部分重复）", "#f57c00"
    if score >= 0.40:
        return "中等相似", "#fbc02d"
    if score >= 0.20:
        return "较低相似", "#7cb342"
    return "几乎不相似", "#388e3c"


def read_uploaded(uploaded_file):
    """读取上传的文本文件内容。

    参数:
        uploaded_file: Streamlit 的 UploadedFile 对象。
    返回:
        str: 文件解码后的文本内容。
    """
    return uploaded_file.getvalue().decode("utf-8", errors="ignore")


# ---------------------------------------------------------------------------
# 页面标题
# ---------------------------------------------------------------------------
st.title("📄 文本相似度分析与查重系统")
st.caption(
    "基于 TF-IDF、Jaccard、编辑距离、SimHash 的多算法融合 · 纯离线运行 · 无需 GPU / 无需联网"
)
st.markdown("---")

# ---------------------------------------------------------------------------
# 侧边栏：算法权重说明
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ 关于本系统")
    st.markdown(
        """
        本系统将 **四种相似度算法** 按权重线性融合，
        综合评估两段文本的相似程度：

        | 算法 | 默认权重 |
        | --- | --- |
        | TF-IDF 余弦 | 40% |
        | Jaccard | 20% |
        | 编辑距离 | 20% |
        | SimHash | 20% |

        融合公式：`score = Σ(权重 × 算法得分)`
        """
    )

    st.subheader("📌 相似度判定标准")
    st.markdown(
        """
        - **≥ 0.80** 高度相似（疑似抄袭）
        - **0.60 ~ 0.80** 较高相似
        - **0.40 ~ 0.60** 中等相似
        - **0.20 ~ 0.40** 较低相似
        - **< 0.20** 几乎不相似
        """
    )

# ---------------------------------------------------------------------------
# 主区域：两个标签页
# ---------------------------------------------------------------------------
tab1, tab2 = st.tabs(["🔍 两篇文本比对", "📊 批量查重"])

# ===========================================================================
# 模式一：两篇文本比对
# ===========================================================================
with tab1:
    st.subheader("两篇文本比对")
    st.write("输入或上传两段文本，系统将计算多种相似度并给出综合结论。")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**文本 A**")
        upload_a = st.file_uploader("上传文本 A（可选）", type=["txt"], key="ua")
        text_a = st.text_area(
            "文本 A 内容",
            height=220,
            placeholder="在此粘贴文本 A……",
            key="ta",
        )
        if upload_a is not None:
            text_a = read_uploaded(upload_a)

    with col2:
        st.markdown("**文本 B**")
        upload_b = st.file_uploader("上传文本 B（可选）", type=["txt"], key="ub")
        text_b = st.text_area(
            "文本 B 内容",
            height=220,
            placeholder="在此粘贴文本 B……",
            key="tb",
        )
        if upload_b is not None:
            text_b = read_uploaded(upload_b)

    if st.button("开始比对", type="primary", use_container_width=True):
        if not text_a.strip() or not text_b.strip():
            st.warning("请先输入或上传两段文本内容。")
        else:
            # 计算融合得分与各单项得分
            total, scores = combined_similarity(text_a, text_b)

            # 展示综合得分
            conclusion, color = interpret(total)
            st.markdown(
                f"""
                <div style="padding:16px;border-radius:8px;background:{color}22;border-left:6px solid {color};">
                    <span style="font-size:18px;font-weight:bold;">综合相似度：{total:.2%}</span>
                    &nbsp;&nbsp;|&nbsp;&nbsp;
                    <span style="font-size:16px;color:{color};font-weight:bold;">{conclusion}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # 综合得分进度条
            st.progress(min(float(total), 1.0))

            st.markdown("---")

            # 各算法得分
            st.subheader("各算法得分明细")
            c1, c2, c3, c4 = st.columns(4)
            cols = [c1, c2, c3, c4]
            for col, (key, name) in zip(cols, ALGO_NAMES.items()):
                value = scores.get(key, 0.0)
                col.metric(label=name, value=f"{value:.2%}")

            st.caption(
                "说明：TF-IDF 余弦相似度为主指标（权重 40%），其余三项各 20%，"
                "融合后得到综合得分。"
            )

# ===========================================================================
# 模式二：批量查重
# ===========================================================================
with tab2:
    st.subheader("批量查重")
    st.write("上传多篇文档（支持 .txt），系统将两两比对并生成相似度矩阵与热力图。")

    files = st.file_uploader(
        "上传文档（可多选）",
        type=["txt"],
        accept_multiple_files=True,
        key="batch",
    )

    if files:
        docs = []
        doc_names = []
        for f in files:
            docs.append(read_uploaded(f))
            doc_names.append(f.name)

        if st.button("开始批量查重", type="primary", use_container_width=True):
            if len(docs) < 2:
                st.warning("请至少上传两篇文档。")
            else:
                with st.spinner("正在两两比对，请稍候……"):
                    matrix, names = batch_compare(docs, doc_names)

                st.success(f"已完成 {len(docs)} 篇文档的比对。")

                # 找出最相似的一对文档
                n = len(docs)
                best_i, best_j, best_score = 0, 1, 0.0
                pairs = []
                for i in range(n):
                    for j in range(i + 1, n):
                        s = matrix[i][j]
                        pairs.append((names[i], names[j], s))
                        if s > best_score:
                            best_i, best_j, best_score = i, j, s

                conclusion, color = interpret(best_score)
                st.markdown(
                    f"""
                    <div style="padding:16px;border-radius:8px;background:{color}22;border-left:6px solid {color};">
                        <span style="font-weight:bold;">最相似文档对：</span>
                        《{names[best_i]}》 ↔ 《{names[best_j]}》
                        &nbsp;&nbsp;相似度 <b>{best_score:.2%}</b>（{conclusion}）
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # 相似度矩阵表格
                st.subheader("相似度矩阵")
                import pandas as pd

                df = pd.DataFrame(matrix, index=names, columns=names)
                st.dataframe(df.style.format("{:.2%}").background_gradient(
                    cmap="YlOrRd", vmin=0, vmax=1
                ))

                # 热力图
                st.subheader("相似度热力图")
                fig, ax = plt.subplots(figsize=(max(6, n * 1.2), max(5, n * 1.0)))
                im = ax.imshow(matrix, cmap="YlOrRd", vmin=0, vmax=1)

                # 在每个单元格标注数值
                for i in range(n):
                    for j in range(n):
                        ax.text(j, i, f"{matrix[i][j]:.2f}",
                                ha="center", va="center",
                                color="black" if matrix[i][j] < 0.6 else "white",
                                fontsize=10)

                ax.set_xticks(range(n))
                ax.set_yticks(range(n))
                ax.set_xticklabels(names, rotation=45, ha="right")
                ax.set_yticklabels(names)
                ax.set_title("文档两两相似度热力图")
                fig.colorbar(im, ax=ax, label="相似度")
                fig.tight_layout()
                st.pyplot(fig)

                # 相似度排序列表
                st.subheader("文档对相似度排序")
                pairs_sorted = sorted(pairs, key=lambda x: x[2], reverse=True)
                rank_df = pd.DataFrame(
                    pairs_sorted, columns=["文档 1", "文档 2", "相似度"]
                )
                rank_df["相似度"] = rank_df["相似度"].map(lambda x: f"{x:.2%}")
                st.dataframe(rank_df, use_container_width=True)
