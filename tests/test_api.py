"""
Tests for SkillSight REST API Endpoints:
- Top skills endpoint (User Story 1)
- 30-day historical trend lines endpoint (User Story 2)
- Summary KPI endpoint
- Category taxonomy endpoint
- Paginated jobs endpoint
- Operational pipeline logs endpoint (User Story 4)
- Performance validation (< 1.5s response time metric)
"""
import time
from datetime import date, timedelta, datetime, timezone
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from dashboard.models import Skill, JobPosting, DailySkillAggregate, PipelineRunLog
from etl.config import TECH_SKILLS


class SkillSightAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.today = datetime.now(timezone.utc).date()

        # Seed test skills
        self.python_skill = Skill.objects.create(name="Python", slug="python", category="language", color="#3B82F6")
        self.js_skill = Skill.objects.create(name="JavaScript", slug="javascript", category="language", color="#F59E0B")
        self.django_skill = Skill.objects.create(name="Django", slug="django", category="framework", color="#059669")
        self.flask_skill = Skill.objects.create(name="Flask", slug="flask", category="framework", color="#64748B")

        # Seed 30 days of daily aggregates
        for day_offset in range(30):
            d = self.today - timedelta(days=day_offset)
            DailySkillAggregate.objects.create(
                date=d, skill=self.python_skill, job_count=25 + day_offset,
                total_jobs_analyzed=100, demand_percentage=25.0
            )
            DailySkillAggregate.objects.create(
                date=d, skill=self.django_skill, job_count=15 + (day_offset % 3),
                total_jobs_analyzed=100, demand_percentage=15.0
            )
            DailySkillAggregate.objects.create(
                date=d, skill=self.flask_skill, job_count=10 - (day_offset % 2),
                total_jobs_analyzed=100, demand_percentage=10.0
            )

        # Seed sample job posting
        self.job = JobPosting.objects.create(
            job_id="test-job-001",
            title="Senior Python Backend Engineer",
            company_name="Acme Corp",
            location="Remote",
            is_remote=True,
            posted_date=self.today,
            description_snippet="Building web applications using Python and Django."
        )
        self.job.skills.add(self.python_skill, self.django_skill)

        # Seed sample log
        PipelineRunLog.objects.create(
            run_id="test_run_001",
            status="SUCCESS",
            duration_seconds=1.1,
            jobs_fetched=50,
            jobs_processed=50,
            skills_identified=120,
            source="Test API"
        )

    def test_summary_api(self):
        url = reverse('dashboard:api-summary')
        start = time.time()
        response = self.client.get(url)
        elapsed = time.time() - start

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(elapsed, 1.5, "Performance metric violated: summary API took > 1.5s")
        data = response.json()
        self.assertIn('total_jobs_analyzed', data)
        self.assertIn('top_language', data)
        self.assertIn('top_framework', data)
        self.assertIn('latest_pipeline_run', data)

    def test_top_skills_api(self):
        # User Story 1: Top requested programming languages this week
        url = reverse('dashboard:api-top-skills')
        start = time.time()
        response = self.client.get(url, {'days': 7, 'category': 'language', 'limit': 10})
        elapsed = time.time() - start

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(elapsed, 1.5, "Performance metric violated: top-skills API took > 1.5s")
        data = response.json()
        self.assertEqual(data['category'], 'language')
        skills = data['skills']
        self.assertGreater(len(skills), 0)
        self.assertEqual(skills[0]['slug'], 'python')

    def test_trends_api_django_vs_flask(self):
        # User Story 2: 30-day historical trend line for Django vs. Flask
        url = reverse('dashboard:api-trends')
        start = time.time()
        response = self.client.get(url, {'skills': 'django,flask', 'days': 30})
        elapsed = time.time() - start

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(elapsed, 1.5, "Performance metric violated: trends API took > 1.5s")
        data = response.json()
        self.assertEqual(data['days'], 30)
        self.assertEqual(len(data['series']), 2)
        series_slugs = [s['slug'] for s in data['series']]
        self.assertIn('django', series_slugs)
        self.assertIn('flask', series_slugs)

    def test_categories_api(self):
        url = reverse('dashboard:api-categories')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('categories', data)

    def test_job_list_api(self):
        url = reverse('dashboard:api-jobs')
        response = self.client.get(url, {'skill': 'python'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['total_count'], 1)
        self.assertEqual(data['jobs'][0]['job_id'], 'test-job-001')

    def test_pipeline_logs_api(self):
        # User Story 4: View logs to debug pipeline
        url = reverse('dashboard:api-logs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['logs'][0]['run_id'], 'test_run_001')
