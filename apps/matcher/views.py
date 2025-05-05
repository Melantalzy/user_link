from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from sentence_transformers import SentenceTransformer
import numpy as np
from .models import UserSpeech, SensitiveEntity, UserEntityMap
from apps.matcher.models import UserSpeech
from sklearn.metrics.pairwise import cosine_similarity
import json
from django.conf import settings
from collections import defaultdict
import pprint
from rest_framework.decorators import api_view
from rest_framework.response import Response

# 加载预训练的模型
model = SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL_PATH)


def build_user_entity_graph(request, user_id):
    try:
        user = UserSpeech.objects.get(pk=user_id)
        user_entity_map = UserEntityMap.objects.get(user=user)
        user_entities = user_entity_map.entity_ids  # 是一个 list

        all_mappings = UserEntityMap.objects.all()

        related_users = set()
        for mapping in all_mappings:
            if mapping.user.id == user_id:
                continue
            if any(eid in user_entities for eid in mapping.entity_ids):
                related_users.add(mapping.user)

        privacy_categories = []

        for entity_id in user_entities:
            entity = SensitiveEntity.objects.get(entity_id=entity_id)
            category = next((c for c in privacy_categories if c["name"] == entity.entity_type), None)
            if not category:
                category = {"name": entity.entity_type, "privacies": []}
                privacy_categories.append(category)

            category["privacies"].append({
                "name": entity.entity_text,
                "users": [{"email": u.email, "id": u.id} for u in related_users if
                          entity_id in UserEntityMap.objects.get(user=u).entity_ids]
            })

        result = {
            "email": user.email,
            "privacyCategories": privacy_categories
        }

        return JsonResponse(result, json_dumps_params={'ensure_ascii': False, 'indent': 2})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
def simple_test_view(request):
    if request.method == "POST":
        print("Request method:", request.method)
        print("Raw request body:", request.body)

        try:
            body = json.loads(request.body)  # 尝试解析 JSON 数据
        except json.JSONDecodeError as e:
            print("JSON decode error:", e)
            return JsonResponse({"error": "Invalid JSON"}, status=400)

        # 从请求体中提取 comment 字段
        comment = body.get("comment", "")
        print("Parsed comment:", comment)

        return JsonResponse({"received_comment": comment})  # 返回处理结果

    return JsonResponse({"error": "Invalid request method"}, status=405)  # 只允许 POST 请求
# LSH哈希器（模糊哈希）
class LSHHasher:
    def __init__(self, num_planes=32, seed=42):
        np.random.seed(seed)
        self.planes = np.random.randn(num_planes, 384)  # 384维是常见的句子向量长度

    def hash(self, embedding):
        projections = np.dot(self.planes, embedding)
        bits = (projections >= 0).astype(int)
        hash_int = 0
        for bit in bits:
            hash_int = (hash_int << 1) | bit
        return hash_int

# 用于渲染评论提交页面的视图
def submit_comment(request):
    return render(request, 'matcher/submit_comment.html')


# 处理提交的评论并计算相似度
# 视图函数
# 处理提交的评论并计算相似度
@csrf_exempt
def find_similar_comment(request):
    print("=== request received ===")
    print("Method:", request.method)
    print("Raw body:", request.body)
    try:
        body = json.loads(request.body)
    except Exception as e:
        print("!!! JSON Decode Error:", e)
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    if request.method == 'POST':
        # 获取前端传来的评论
        data = json.loads(request.body)
        user_comment = data.get('comment')

        # 将评论转化为嵌入向量
        user_comment_embedding = model.encode([user_comment])[0]

        # 初始化LSH哈希器
        hasher = LSHHasher(num_planes=32)

        # 获取数据库中的所有评论及其嵌入向量
        speeches = UserSpeech.objects.all()
        embeddings = np.array([speech.embedding for speech in speeches])

        # 对所有评论进行哈希
        hashed_speeches = [hasher.hash(embedding) for embedding in embeddings]

        # 对用户评论进行哈希
        user_comment_hash = hasher.hash(user_comment_embedding)

        # 计算用户输入的评论与数据库中所有评论的哈希差距（汉明距离）
        hamming_distances = [bin(user_comment_hash ^ hash_val).count('1') for hash_val in hashed_speeches]

        # 筛选出汉明距离小于等于10的评论（初步筛查）
        similar_speeches = [idx for idx, dist in enumerate(hamming_distances) if dist <= 10]

        # 精确匹配：计算筛选后的评论与用户评论的余弦相似度
        if similar_speeches:
            filtered_speeches = [speeches[idx] for idx in similar_speeches]
            filtered_embeddings = np.array([speech.embedding for speech in filtered_speeches])
            similarities = cosine_similarity([user_comment_embedding], filtered_embeddings)[0]

            # 找到相似度最高的3个评论
            top_indices = np.argsort(similarities)[-3:][::-1]

            top_users = []
            for idx in top_indices:
                speech = filtered_speeches[idx]
                top_users.append({
                    'id': speech.id,
                    'email': speech.email,
                    'comment': speech.comment,
                    'similarity': round(float(similarities[idx]), 4)  # 小数保留4位
                })

            # 返回这3个最相似的用户信息
            return JsonResponse({'top_users': top_users})

        else:
            return JsonResponse({'error': '没有找到相似的评论'}, status=404)

    return JsonResponse({'error': 'Invalid request'}, status=400)


# 上传评论并计算相似度
@csrf_protect
def upload_comments(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({'error': 'No file uploaded'}, status=400)

        try:
            file_data = file.read().decode('utf-8')
            comments_data = json.loads(file_data)

            for entry in comments_data:
                email = entry.get('email')
                comments = entry.get('comments', [])
                if not comments:
                    continue  # 忽略空评论

                # 计算嵌入
                embeddings = model.encode(comments)
                pooled_embedding = np.mean(embeddings, axis=0)

                user_speech = None  # 标记为仅用于匹配，不保存

                # 哈希 + 匹配逻辑
                hasher = LSHHasher(num_planes=32)
                user_comment_hash = hasher.hash(pooled_embedding)

                # 获取数据库所有评论
                speeches = UserSpeech.objects.all()
                embeddings_db = np.array([speech.embedding for speech in speeches])
                hashed_db = [hasher.hash(emb) for emb in embeddings_db]

                # 哈希初筛
                hamming_distances = [bin(user_comment_hash ^ h).count('1') for h in hashed_db]
                similar_indices = [i for i, d in enumerate(hamming_distances) if d <= 10]

                if similar_indices:
                    filtered = [speeches[i] for i in similar_indices]
                    filtered_embeddings = np.array([s.embedding for s in filtered])
                    similarities = cosine_similarity([pooled_embedding], filtered_embeddings)[0]

                    top_indices = np.argsort(similarities)[-3:][::-1]
                    top_users = [{
                        'id': filtered[i].id,
                        'email': filtered[i].email,
                        'comment': filtered[i].comment,
                        'similarity': round(float(similarities[i]), 4)
                    } for i in top_indices]

                    return JsonResponse({'top_users': top_users})

                else:
                    return JsonResponse({'error': '没有找到相似的评论'}, status=404)

            return JsonResponse({'error': '未上传有效的评论'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return render(request, 'matcher/upload_comments.html')



def user_detail(request, user_id):
    user_speech = get_object_or_404(UserSpeech, id=user_id)

    # 如果 comment 是列表，转换为字符串
    comment = user_speech.comment
    if isinstance(comment, list):
        comment = '\n\n'.join(comment)  # 加换行增强可读性
    elif isinstance(comment, str) and comment.startswith("[") and comment.endswith("]"):
        # 处理字符串化的列表：尝试用 ast.literal_eval 转回列表
        import ast
        try:
            comment_list = ast.literal_eval(comment)
            if isinstance(comment_list, list):
                comment = '\n\n'.join(comment_list)
        except Exception:
            pass  # 保持原始字符串

    return render(request, 'matcher/user_detail.html', {
        'user_speech': user_speech,
        'comment_text': comment  # 将处理后的字符串传给模板
    })


def user_list(request):
    users = UserSpeech.objects.all()
    return render(request, 'matcher/user_list.html', {'users': users})
