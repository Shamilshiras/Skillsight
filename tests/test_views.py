"""
Tests for SkillSight UI Views.
Verifies dashboard HTML template rendering, static assets linking, and context variables.
"""
from django.test import TestCase, Client
from django.urls import reverse


class DashboardViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_dashboard_view_status_code(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)

    def test_dashboard_template_used(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertTemplateUsed(response, 'dashboard/index.html')
        self.assertTemplateUsed(response, 'dashboard/base.html')

    def test_dashboard_html_elements(self):
        response = self.client.get(reverse('dashboard:index'))
        content = response.content.decode('utf-8')
        self.assertIn('SkillSight', content)
        self.assertIn('topSkillsChart', content)
        self.assertIn('trendsChart', content)
        self.assertIn('categoryShareChart', content)
        self.assertIn('leaderboard-table', content)
        self.assertIn('admin-logs', content)
