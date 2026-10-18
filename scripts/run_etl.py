#!/usr/bin/env python
"""
SkillSight Standalone ETL CLI Runner.
Allows manual execution of the data pipeline or scheduled execution via cron.
Usage:
    python scripts/run_etl.py --pages 3
    python scripts/run_etl.py --fallback
"""
import os
import sys
import argparse
from datetime import datetime, timezone

# Ensure project root is on PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Initialize Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillsight.settings')
import django
django.setup()

from etl.pipeline import run_etl_pipeline


def main():
    parser = argparse.ArgumentParser(description="SkillSight ETL Pipeline Runner")
    parser.add_argument("--pages", type=int, default=3, help="Number of API pages to fetch (default: 3)")
    parser.add_argument("--fallback", action="store_true", help="Force offline fallback dataset immediately")
    parser.add_argument("--date", type=str, default=None, help="Target date YYYY-MM-DD (default: today UTC)")

    args = parser.parse_args()

    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print(f"Invalid date format: {args.date}. Expected YYYY-MM-DD.")
            sys.exit(1)

    print(f"Starting SkillSight ETL Pipeline (pages={args.pages}, fallback={args.fallback})...")
    result = run_etl_pipeline(
        pages_to_fetch=args.pages,
        target_date=target_date,
        force_fallback=args.fallback
    )

    print("\n--- Pipeline Execution Summary ---")
    print(f"Status:             {result['status']}")
    print(f"Target Date:        {result['target_date']}")
    print(f"Source:             {result['source']}")
    print(f"Jobs Extracted:     {result['jobs_extracted']}")
    print(f"Jobs Saved:         {result['jobs_saved']}")
    print(f"Aggregates Saved:   {result['aggregates_saved']}")
    print(f"Skills Identified:  {result['total_skills_identified']}")
    print(f"Duration:           {result['duration_seconds']}s")
    print(f"Top Language:       {result['summary'].get('top_language')}")
    print(f"Top Framework:      {result['summary'].get('top_framework')}")
    print("----------------------------------\n")


if __name__ == "__main__":
    main()
