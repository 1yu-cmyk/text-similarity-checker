# 基于多算法融合的中文文本相似度分析与查重系统

一个基于 Python + Streamlit 的轻量化文本相似度分析工具，纯离线运行，无需 GPU、无需联网、无需调用任何大模型 API。适用于文档查重、作业比对、内容去重等场景。

## 一、功能特性

- **两篇文本比对**：输入或上传两段文本，实时计算相似度并给出结论。
- **批量查重**：上传多篇文档，两两比对，生成相似度矩阵与热力图，自动定位重复文档对。
- **多算法融合**：综合 TF-IDF 余弦相似度、Jaccard 相似度、编辑距离相似度、SimHash 相似度四项指标，按权重线性融合，结果更稳健。

## 二、技术栈

| 技术 | 用途 |
| --- | --- |
| Python 3 | 主开发语言 |
| Streamlit | Web 交互界面 |
| jieba | 中文分词 |
| scikit-learn | TF-IDF 向量化 |
| numpy / pandas | 数值计算与矩阵展示 |
| matplotlib | 相似度热力图 |

## 三、目录结构

```
text-similarity-checker/
├── app.py               # Streamlit 前端界面（程序入口）
├── similarity.py        # 相似度算法核心模块
├── requirements.txt     # 依赖清单
├── README.md            # 本说明文档
├── data/                # 示例文档（可选，用于测试）
└── tests/               # 测试脚本
    └── test_similarity.py
```

## 四、环境安装

1. 确认已安装 Python 3.8 及以上版本：

   ```bash
   python --version
   ```

2. 创建虚拟环境（推荐）：

   ```bash
   python -m venv venv
   # Windows 激活：
   venv\Scripts\activate
   # macOS / Linux 激活：
   source venv/bin/activate
   ```

3. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

## 五、运行

在项目根目录下执行：

```bash
streamlit run app.py
```

启动后浏览器会自动打开页面（默认地址 http://localhost:8501）。

## 六、使用说明

### 模式一：两篇文本比对

1. 在「文本 A」「文本 B」区域分别粘贴或上传两段文本（支持 `.txt` 文件）。
2. 点击「开始比对」。
3. 页面展示：综合相似度、判定结论、四项算法各自的得分。

### 模式二：批量查重

1. 在「批量查重」标签页上传多篇 `.txt` 文档（可多选）。
2. 点击「开始批量查重」。
3. 页面展示：最相似文档对、相似度矩阵、热力图、相似度排序列表。

## 七、核心算法说明

| 算法 | 原理 | 默认权重 |
| --- | --- | --- |
| TF-IDF 余弦相似度 | 词频-逆文档频率向量夹角的余弦值 | 40% |
| Jaccard 相似度 | 词集合交并比 | 20% |
| 编辑距离相似度 | 字符级 Levenshtein 编辑距离归一化 | 20% |
| SimHash 相似度 | 局部敏感哈希指纹的海明距离 | 20% |

融合公式：`score = Σ(权重 × 算法得分)`，相似度阈值 **≥ 0.80** 判定为疑似重复。

## 八、测试

```bash
python -m pytest tests/ -v
```

或直接运行核心模块自测：

```bash
python similarity.py
```

## 九、许可与声明

本项目仅用于《专业综合实训》课程教学与学习，代码为独立开发。
