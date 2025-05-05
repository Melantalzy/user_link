from django.urls import path
from . import views

urlpatterns = [
    path('upload_comments/', views.upload_comments, name='upload_comments'),
    path('submit_comment/', views.submit_comment, name='submit_comment'),
    path('find_similar_comment/', views.find_similar_comment, name='find_similar_comment'),
    path('users/', views.user_list, name='user_list'),
    path('user/<int:user_id>/', views.user_detail, name='user_detail'),
    path('user_list/', views.user_list, name='user_list'),
    path('user_entity/<int:user_id>/', views.build_user_entity_graph, name='build_user_entity_graph'),


    path('api/simple_test/', views.simple_test_view, name='simple_test'),
]
