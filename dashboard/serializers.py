"""
SkillSight REST API Serializers.
Defines representation schemas for Skills, Jobs, Aggregates, and Operational Logs.
"""
from rest_framework import serializers
from .models import Skill, JobPosting, DailySkillAggregate, PipelineRunLog


class SkillSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Skill
        fields = ['id', 'name', 'slug', 'category', 'category_display', 'color', 'created_at']


class JobPostingSerializer(serializers.ModelSerializer):
    skills = SkillSerializer(many=True, read_only=True)

    class Meta:
        model = JobPosting
        fields = [
            'id', 'job_id', 'title', 'company_name', 'location',
            'is_remote', 'job_type', 'url', 'description_snippet',
            'posted_date', 'created_at', 'skills'
        ]


class DailySkillAggregateSerializer(serializers.ModelSerializer):
    skill_name = serializers.CharField(source='skill.name', read_only=True)
    skill_slug = serializers.CharField(source='skill.slug', read_only=True)
    skill_category = serializers.CharField(source='skill.category', read_only=True)
    skill_color = serializers.CharField(source='skill.color', read_only=True)

    class Meta:
        model = DailySkillAggregate
        fields = [
            'id', 'date', 'skill', 'skill_name', 'skill_slug',
            'skill_category', 'skill_color', 'job_count',
            'total_jobs_analyzed', 'demand_percentage'
        ]


class PipelineRunLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = PipelineRunLog
        fields = [
            'id', 'run_id', 'status', 'executed_at', 'duration_seconds',
            'jobs_fetched', 'jobs_processed', 'skills_identified',
            'source', 'error_message', 'details'
        ]
