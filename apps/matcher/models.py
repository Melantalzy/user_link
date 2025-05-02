from django.db import models

class UserSpeech(models.Model):
    comment = models.TextField(default="No comment")  # 在这里提供默认值
    email = models.EmailField()   # 存储用户邮箱
    embedding = models.JSONField()  # 存储嵌入向量（以JSON格式存储）

    def __str__(self):
        return self.comment


class UserHash(models.Model):
    user = models.OneToOneField(UserSpeech, on_delete=models.CASCADE, primary_key=True)
    # 外键关联到 UserSpeech，且 user_id 就是 primary key
    hash_value = models.BigIntegerField()

    def __str__(self):
        return f'User {self.user.id} - Hash {self.hash_value}'


class SensitiveEntity(models.Model):
    entity_id = models.CharField(max_length=20, unique=True)  # 记录json里面的编号（比如"554"）
    entity_type = models.CharField(max_length=50)             # 比如 EMAIL, PHONE等
    entity_text = models.TextField()                          # 具体的敏感内容，比如"nicolas"

    def __str__(self):
        return f"{self.entity_type}: {self.entity_text}"


class UserEntityMap(models.Model):
    user = models.OneToOneField(UserSpeech, on_delete=models.CASCADE)
    entity_ids = models.JSONField()

    def __str__(self):
        return f"User {self.user.id} - Entities {self.entity_ids}"