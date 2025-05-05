from django.test import TestCase

import numpy as np
from sentence_transformers import SentenceTransformer

# 定义 LSH 哈希器
class LSHHasher:
    def __init__(self, num_planes=32, seed=42):
        np.random.seed(seed)
        self.planes = np.random.randn(num_planes, 384)  # 嵌入维度是384

    def hash(self, embedding):
        projections = np.dot(self.planes, embedding)
        bits = (projections >= 0).astype(int)
        hash_int = 0
        for bit in bits:
            hash_int = (hash_int << 1) | bit
        return hash_int

# 示例：加载句子嵌入模型
model = SentenceTransformer('model/finetuned_model_v1')  # 或你自己的微调模型路径

# 输入句子组（如用户历史评论）
sentence_group = [
    "thanks for the share bro'",
    "thanks for sharing this info."
]

# 获取每条句子的嵌入
embeddings = model.encode(sentence_group)

# 对句子组做平均池化
group_embedding = np.mean(embeddings, axis=0)

# 初始化 LSH 哈希器
hasher = LSHHasher(num_planes=32)

# 计算哈希
group_hash = hasher.hash(group_embedding)

# 输出结果
print("句子组:")
for s in sentence_group:
    print("-", s)
print("\n平均池化后的嵌入向量形状:", group_embedding.shape)
print("LSH 哈希值（二进制）:", bin(group_hash))
print("LSH 哈希值（十进制）:", group_hash)

