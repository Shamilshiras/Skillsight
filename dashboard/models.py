"""
SkillSight Data Models.
Stores extracted job postings, normalized tech skills, daily aggregate trends,
and pipeline execution logs for system administration and monitoring.
"""
from django.db import models


class Skill(models.Model):
    """Normalized technical skills tracked by the pipeline."""
    CATEGORY_CHOICES = [
        ('language', 'Programming Language'),
        ('framework', 'Framework & Library'),
        ('database', 'Database'),
        ('cloud_devops', 'Cloud & DevOps'),
        ('tool', 'Tool & Other'),
    ]

    name = models.CharField(max_length=100, unique=True, help_text="Skill display name (e.g. Python, React)")
    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, db_index=True)
    color = models.CharField(max_length=7, default='#3B82F6', help_text="Hex color code for charts")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class JobPosting(models.Model):
    """Raw and processed tech job postings extracted from public APIs."""
    job_id = models.CharField(max_length=255, unique=True, db_index=True, help_text="Unique external identifier or slug")
    title = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    is_remote = models.BooleanField(default=False)
    job_type = models.CharField(max_length=100, blank=True, default='Full-time')
    url = models.URLField(max_length=500, blank=True)
    description_snippet = models.TextField(blank=True, help_text="Short preview of job description")
    posted_date = models.DateField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    skills = models.ManyToManyField(Skill, related_name='job_postings', blank=True)

    class Meta:
        ordering = ['-posted_date', '-created_at']
        indexes = [
            models.Index(fields=['posted_date']),
            models.Index(fields=['is_remote']),
        ]
        verbose_name = 'Job Posting'
        verbose_name_plural = 'Job Postings'

    def __str__(self):
        return f"{self.title} at {self.company_name} ({self.posted_date})"


class DailySkillAggregate(models.Model):
    """
    Optimized daily aggregate metrics for sub-1.5s chart query performance.
    Enables blazing fast time-series trend lines and top-N skill leaderboards.
    """
    date = models.DateField(db_index=True)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='daily_aggregates')
    job_count = models.PositiveIntegerField(default=0, help_text="Number of postings mentioning this skill")
    total_jobs_analyzed = models.PositiveIntegerField(default=0, help_text="Total jobs scanned on this date")
    demand_percentage = models.FloatField(default=0.0, help_text="Percentage of jobs mentioning this skill")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('date', 'skill')
        ordering = ['-date', '-job_count']
        indexes = [
            models.Index(fields=['date', 'skill']),
            models.Index(fields=['date']),
            models.Index(fields=['skill']),
        ]
        verbose_name = 'Daily Skill Aggregate'
        verbose_name_plural = 'Daily Skill Aggregates'

    def __str__(self):
        return f"{self.date} - {self.skill.name}: {self.job_count} jobs ({self.demand_percentage:.1f}%)"


class PipelineRunLog(models.Model):
    """
    System administrator operational logs.
    Tracks Airflow and standalone ETL runs, durations, status, and error details.
    """
    STATUS_CHOICES = [
        ('SUCCESS', 'Success'),
        ('WARNING', 'Warning'),
        ('FAILED', 'Failed'),
    ]

    run_id = models.CharField(max_length=100, unique=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='SUCCESS', db_index=True)
    executed_at = models.DateTimeField(auto_now_add=True, db_index=True)
    duration_seconds = models.FloatField(default=0.0)
    jobs_fetched = models.PositiveIntegerField(default=0)
    jobs_processed = models.PositiveIntegerField(default=0)
    skills_identified = models.PositiveIntegerField(default=0)
    source = models.CharField(max_length=100, default='Arbeitnow API')
    error_message = models.TextField(blank=True, null=True)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-executed_at']
        verbose_name = 'Pipeline Run Log'
        verbose_name_plural = 'Pipeline Run Logs'

    def __str__(self):
        return f"[{self.status}] {self.run_id} at {self.executed_at:%Y-%m-%d %H:%M:%S}"
