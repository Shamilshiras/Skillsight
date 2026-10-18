from django.contrib import admin
from .models import Skill, JobPosting, DailySkillAggregate, PipelineRunLog


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'slug', 'color', 'created_at')
    list_filter = ('category',)
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company_name', 'location', 'is_remote', 'posted_date', 'created_at')
    list_filter = ('is_remote', 'posted_date')
    search_fields = ('title', 'company_name', 'location', 'description_snippet')
    filter_horizontal = ('skills',)


@admin.register(DailySkillAggregate)
class DailySkillAggregateAdmin(admin.ModelAdmin):
    list_display = ('date', 'skill', 'job_count', 'total_jobs_analyzed', 'demand_percentage')
    list_filter = ('date', 'skill__category')
    search_fields = ('skill__name',)
    date_hierarchy = 'date'


@admin.register(PipelineRunLog)
class PipelineRunLogAdmin(admin.ModelAdmin):
    list_display = ('run_id', 'status', 'source', 'jobs_fetched', 'jobs_processed', 'duration_seconds', 'executed_at')
    list_filter = ('status', 'source', 'executed_at')
    search_fields = ('run_id', 'error_message')
    readonly_fields = ('run_id', 'status', 'source', 'jobs_fetched', 'jobs_processed', 'skills_identified', 'duration_seconds', 'executed_at', 'error_message', 'details')
