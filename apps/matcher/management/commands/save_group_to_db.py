import numpy as np
from django.core.management.base import BaseCommand
from sentence_transformers import SentenceTransformer
from apps.matcher.models import UserSpeech, UserHash  # 根据你的项目结构调整路径


class LSHHasher:
    def __init__(self, num_planes=32, seed=42):
        np.random.seed(seed)
        self.planes = np.random.randn(num_planes, 384)

    def hash(self, embedding):
        projections = np.dot(self.planes, embedding)
        bits = (projections >= 0).astype(int)
        hash_int = 0
        for bit in bits:
            hash_int = (hash_int << 1) | bit
        return hash_int


class Command(BaseCommand):
    help = 'Encode a sentence group, compute average embedding, hash it, and store in DB.'

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 正在加载模型并处理句子组...")

        # 加载模型
        model = SentenceTransformer('model/finetuned_model_v1')

        # 示例句子组和邮箱（可以根据需要修改）
        sentence_group = [
            "114514"
        ]
        email = "testuser114514@example.com"

        # 获取嵌入并平均池化
        embeddings = model.encode(sentence_group)
        group_embedding = np.mean(embeddings, axis=0)

        # 哈希计算
        hasher = LSHHasher()
        group_hash = hasher.hash(group_embedding)

        # 更新或创建 UserSpeech
        user_speech, created = UserSpeech.objects.update_or_create(
            email=email,
            defaults={
                'comment': "\n".join(sentence_group),
                'embedding': group_embedding.tolist()
            }
        )

        # 更新或创建 UserHash
        UserHash.objects.update_or_create(
            user=user_speech,
            defaults={'hash_value': group_hash}
        )

        self.stdout.write(self.style.SUCCESS("✅ 已保存到数据库："))
        self.stdout.write(f"   用户 ID: {user_speech.id}")
        self.stdout.write(f"   邮箱: {email}")
        self.stdout.write(f"   哈希值（十进制）: {group_hash}")
        self.stdout.write(f"   哈希值（二进制）: {bin(group_hash)}")
