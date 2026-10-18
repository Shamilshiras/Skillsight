"""
Tests for SkillSight ETL pipeline modules:
- Extraction resilience
- Text cleaning and HTML stripping
- Skill regex keyword matching and boundary checks
- Pandas transformation and aggregate calculations
- Database load and atomic persistence
"""
import os
import unittest
from datetime import date
from django.test import TestCase

from etl.transform import clean_html_text, extract_skills_from_text, transform_job_data
from etl.extract import SAMPLE_FALLBACK_JOBS, extract_job_postings
from etl.load import load_data_to_database, ensure_skills_seeded
from dashboard.models import Skill, JobPosting, DailySkillAggregate, PipelineRunLog


class TextCleaningTestCase(unittest.TestCase):
    def test_clean_html_text(self):
        raw_html = "<p>We are seeking a <strong>Python</strong> &amp; <em>Django</em> engineer.</p>"
        cleaned = clean_html_text(raw_html)
        self.assertEqual(cleaned, "We are seeking a Python & Django engineer.")

    def test_empty_and_none_text(self):
        self.assertEqual(clean_html_text(""), "")
        self.assertEqual(clean_html_text(None), "")


class SkillExtractionTestCase(unittest.TestCase):
    def test_extract_exact_matches(self):
        text = "Senior Software Engineer with expertise in Python, Django, React, and AWS."
        matched = extract_skills_from_text(text)
        slugs = [s["slug"] for s in matched]
        self.assertIn("python", slugs)
        self.assertIn("django", slugs)
        self.assertIn("react", slugs)
        self.assertIn("aws", slugs)

    def test_word_boundaries_no_false_positives(self):
        # "going" should not match "go", "reaction" should not match "react"
        text = "The company is going forward with a new strategy to avoid negative reaction."
        matched = extract_skills_from_text(text)
        slugs = [s["slug"] for s in matched]
        self.assertNotIn("go", slugs)
        self.assertNotIn("react", slugs)

    def test_c_plus_plus_and_c_sharp(self):
        text = "Systems development using C++ and C# on modern cloud platforms."
        matched = extract_skills_from_text(text)
        slugs = [s["slug"] for s in matched]
        self.assertIn("cpp", slugs)
        self.assertIn("csharp", slugs)


class ETLTransformTestCase(unittest.TestCase):
    def test_transform_sample_jobs(self):
        today = date(2026, 10, 16)
        jobs_df, aggregates_df, summary = transform_job_data(SAMPLE_FALLBACK_JOBS, target_date=today)

        self.assertFalse(jobs_df.empty)
        self.assertEqual(len(jobs_df), len(SAMPLE_FALLBACK_JOBS))
        self.assertIn("matched_skills", jobs_df.columns)

        self.assertFalse(aggregates_df.empty)
        self.assertIn("job_count", aggregates_df.columns)
        self.assertIn("demand_percentage", aggregates_df.columns)

        self.assertGreater(summary["total_jobs"], 0)
        self.assertIn("top_language", summary)


class ETLLoadTestCase(TestCase):
    def test_load_to_database(self):
        today = date(2026, 10, 16)
        jobs_df, aggregates_df, _ = transform_job_data(SAMPLE_FALLBACK_JOBS, target_date=today)

        result = load_data_to_database(
            jobs_df=jobs_df,
            aggregates_df=aggregates_df,
            target_date=today,
            source_name="Test Source",
            duration_seconds=0.5
        )

        self.assertEqual(result["status"], "SUCCESS")
        self.assertGreater(result["jobs_saved"], 0)
        self.assertGreater(result["aggregates_saved"], 0)

        # Verify DB records
        self.assertEqual(JobPosting.objects.count(), len(SAMPLE_FALLBACK_JOBS))
        self.assertGreater(DailySkillAggregate.objects.filter(date=today).count(), 0)
        self.assertEqual(PipelineRunLog.objects.count(), 1)
