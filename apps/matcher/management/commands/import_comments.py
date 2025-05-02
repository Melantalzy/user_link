from django.core.management.base import BaseCommand
from apps.matcher.models import UserSpeech  # 确保导入正确的模型
import json

class Command(BaseCommand):
    help = 'Import comments from JSON file into the database'

    def handle(self, *args, **kwargs):
        # 打开并加载JSON文件
        with open('data/user_data_altenens.json', 'r', encoding='utf-8') as f:
            comments_data = json.load(f)

        # 逐条处理评论数据
        for data in comments_data:
            email = data.get('email')
            comments = data.get('comments', [])
            embedding = data.get('embedding', [])

            # 确保数据存在且合法
            if email and comments and embedding:
                # 创建 UserSpeech 对象并保存到数据库
                # 注意：embedding 是高维的，存储在 JSON 格式字段中
                UserSpeech.objects.create(
                    email=email,  # 使用模型中的 'email' 字段
                    comment=comments,  # 使用模型中的 'comments' 字段
                    embedding=embedding  # 使用模型中的 'embedding' 字段
                )
            else:
                self.stdout.write(self.style.WARNING(f"Skipping incomplete or invalid data for email: {email}"))

        # 打印导入结果
        self.stdout.write(self.style.SUCCESS(f"Comments imported successfully."))
