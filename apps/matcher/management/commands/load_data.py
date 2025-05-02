from sentence_transformers import SentenceTransformer
from apps.matcher.models import UserSpeech  # 确保这个 import 是对的
import django
import os

# 如果你在脚本外部执行（比如不是 manage.py 里面），需要初始化 Django 环境
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', '你的项目名.settings')
# django.setup()

# 加载 sentence-transformers 的模型
model = SentenceTransformer('all-MiniLM-L6-v2')

# 自己写的英文评论
comments = [
    "This website is absolutely amazing!",
    "The customer service was too slow, very disappointing.",
    "I love the clean and beautiful design of the homepage.",
    "They have a wide variety of products at reasonable prices.",
    "The checkout process is a bit complicated, needs improvement."
]

# 使用模型生成嵌入
embeddings = model.encode(comments, convert_to_numpy=True)

# 遍历保存到数据库
for comment, embedding in zip(comments, embeddings):
    UserSpeech.objects.create(
        speech=comment,
        speech_embedding=embedding.tolist()  # 如果是 JSONField，需要 list 类型
    )

print("✅ 5 条英语评论和对应向量已成功导入数据库！")
