"""
URL-маршруты для приложения тестирования функционала.
"""

from django.urls import path

from . import views

app_name = 'testing'

urlpatterns = [
    # Тестовые проекты
    path('projects/', views.TestProjectListView.as_view(), name='testproject_list'),
    path('projects/create/', views.TestProjectCreateView.as_view(), name='testproject_create'),
    path('projects/<int:pk>/', views.TestProjectDetailView.as_view(), name='testproject_detail'),
    path('projects/<int:pk>/edit/', views.TestProjectUpdateView.as_view(), name='testproject_edit'),
    
    # Функционал
    path('features/', views.FeatureListView.as_view(), name='feature_list'),
    path('features/create/', views.FeatureCreateView.as_view(), name='feature_create'),
    path('features/<int:pk>/', views.FeatureDetailView.as_view(), name='feature_detail'),
    path('features/<int:pk>/edit/', views.FeatureUpdateView.as_view(), name='feature_update'),
    path('features/<int:pk>/status/', views.FeatureUpdateStatusView.as_view(), name='feature_update_status'),
    path('features/<int:pk>/comment/', views.FeatureAddCommentView.as_view(), name='feature_add_comment'),
    path('features/<int:pk>/comment/<int:comment_id>/resolve/', views.FeatureResolveCommentView.as_view(), name='feature_resolve_comment'),
    path('features/<int:pk>/comment/<int:comment_id>/complete/', views.FeatureCommentCompleteView.as_view(), name='feature_comment_complete'),
    path('features/<int:pk>/comment/<int:comment_id>/return-to-rework/', views.FeatureCommentReturnToReworkView.as_view(), name='feature_comment_return_to_rework'),
    path('features/<int:pk>/return-to-rework/', views.FeatureReturnToReworkView.as_view(), name='feature_return_to_rework'),
    
    # API
    path('api/features/<int:pk>/mark-completed/', views.mark_completed_api, name='api_mark_completed'),
]
