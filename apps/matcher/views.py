from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from sentence_transformers import SentenceTransformer
import numpy as np
from apps.matcher.models import UserSpeech
from sklearn.metrics.pairwise import cosine_similarity
import json

# 加载预训练的模型
model = SentenceTransformer('model/finetuned_model_v1')


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
@csrf_protect
def find_similar_comment(request):
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

            # 预期格式: List of { "email": ..., "comments": [list of comments] }
            for entry in comments_data:
                email = entry.get('email')
                comments = entry.get('comments', [])
                if email and comments:
                    # 对所有评论做嵌入
                    embeddings = model.encode(comments)
                    pooled_embedding = np.mean(embeddings, axis=0)

                    # 保存到数据库
                    user_speech = UserSpeech.objects.create(
                        email=email,
                        comment='\n'.join(comments),
                        embedding=pooled_embedding.tolist()
                    )

                    # 对上传评论进行哈希
                    hasher = LSHHasher(num_planes=32)
                    user_comment_hash = hasher.hash(pooled_embedding)

                    # 获取数据库中所有评论的哈希
                    speeches = UserSpeech.objects.all()
                    embeddings = np.array([speech.embedding for speech in speeches])
                    hashed_speeches = [hasher.hash(embedding) for embedding in embeddings]

                    # 计算上传评论与数据库中所有评论的哈希差距（汉明距离）
                    hamming_distances = [bin(user_comment_hash ^ hash_val).count('1') for hash_val in hashed_speeches]

                    # 筛选出汉明距离小于等于10的评论（初步筛查）
                    similar_speeches = [idx for idx, dist in enumerate(hamming_distances) if dist <= 10]

                    # 精确匹配：计算筛选后的评论与上传评论的余弦相似度
                    if similar_speeches:
                        filtered_speeches = [speeches[idx] for idx in similar_speeches]
                        filtered_embeddings = np.array([speech.embedding for speech in filtered_speeches])
                        similarities = cosine_similarity([pooled_embedding], filtered_embeddings)[0]

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

            return JsonResponse({'error': 'Invalid comment format or missing comments'}, status=400)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return render(request, 'matcher/upload_comments.html')



def user_detail(request, user_id):
    user_speech = get_object_or_404(UserSpeech, id=user_id)  # 改名
    return render(request, 'matcher/user_detail.html', {'user_speech': user_speech})


def user_list(request):
    users = UserSpeech.objects.all()
    return render(request, 'matcher/user_list.html', {'users': users})
