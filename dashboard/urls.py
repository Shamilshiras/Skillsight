"""
SkillSight Dashboard and API URL Routing.
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard View
    path('', views.dashboard_view, name='index'),

    # REST API Endpoints
    path('api/summary/', views.summary_api, name='api-summary'),
    path('api/top-skills/', views.top_skills_api, name='api-top-skills'),
    path('api/trends/', views.trends_api, name='api-trends'),
    path('api/categories/', views.categories_api, name='api-categories'),
    path('api/jobs/', views.job_list_api, name='api-jobs'),
    path('api/logs/', views.pipeline_logs_api, name='api-logs'),
    path('api/trigger-etl/', views.trigger_etl_api, name='api-trigger-etl'),
]
