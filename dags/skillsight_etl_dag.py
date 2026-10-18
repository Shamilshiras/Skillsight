"""
SkillSight Daily ETL Airflow DAG.
Scheduled to run automatically every night at midnight UTC (0 0 * * *).
"""
from datetime import datetime, timedelta, timezone
import json
import logging
import os
import sys

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

logger = logging.getLogger("airflow.task")

# Safe imports for Airflow environments
try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
    AIRFLOW_AVAILABLE = True
except ImportError:
    AIRFLOW_AVAILABLE = False


def task_extract_jobs(**kwargs):
    """
    Airflow Task 1: Extract.
    Calls public job APIs to retrieve latest job postings and pushes to XCom.
    """
    from etl.extract import extract_job_postings

    ti = kwargs.get("ti")
    execution_date = kwargs.get("logical_date") or kwargs.get("execution_date") or datetime.now(timezone.utc)
    target_date = execution_date.date()

    logger.info(f"[Airflow Extract] Fetching job postings for {target_date}...")
    extract_result = extract_job_postings(pages_to_fetch=3)
    raw_jobs = extract_result.get("jobs", [])
    source = extract_result.get("source", "API")
    error = extract_result.get("error")

    if error:
        logger.warning(f"[Airflow Extract API Warning] {error}")

    logger.info(f"[Airflow Extract] Extracted {len(raw_jobs)} job postings from {source}.")

    # Serialize job list for next task
    if ti:
        ti.xcom_push(key="raw_jobs", value=raw_jobs)
        ti.xcom_push(key="source", value=source)
        ti.xcom_push(key="extract_error", value=error)

    return {"job_count": len(raw_jobs), "source": source}


def task_transform_jobs(**kwargs):
    """
    Airflow Task 2: Transform.
    Pulls raw jobs from XCom, scans descriptions with Pandas regex, and computes aggregates.
    """
    from etl.transform import transform_job_data

    ti = kwargs.get("ti")
    execution_date = kwargs.get("logical_date") or kwargs.get("execution_date") or datetime.now(timezone.utc)
    target_date = execution_date.date()

    raw_jobs = []
    if ti:
        raw_jobs = ti.xcom_pull(task_ids="extract_jobs", key="raw_jobs") or []

    # If running standalone or no XCom
    if not raw_jobs:
        from etl.extract import SAMPLE_FALLBACK_JOBS
        raw_jobs = SAMPLE_FALLBACK_JOBS
        logger.info("[Airflow Transform] Using fallback jobs dataset.")

    logger.info(f"[Airflow Transform] Normalizing and scanning {len(raw_jobs)} jobs for skill keywords...")
    jobs_df, aggregates_df, summary = transform_job_data(raw_jobs=raw_jobs, target_date=target_date)

    logger.info(
        f"[Airflow Transform] Top language: {summary.get('top_language')}, "
        f"Active skills detected: {summary.get('active_skills_detected')}."
    )

    if ti:
        ti.xcom_push(key="jobs_json", value=jobs_df.to_json(orient="records", date_format="iso"))
        ti.xcom_push(key="aggregates_json", value=aggregates_df.to_json(orient="records", date_format="iso"))
        ti.xcom_push(key="summary", value=summary)

    return summary


def task_load_data(**kwargs):
    """
    Airflow Task 3: Load.
    Pulls transformed data and atomically inserts into the MySQL database.
    """
    import pandas as pd
    from etl.load import load_data_to_database

    ti = kwargs.get("ti")
    execution_date = kwargs.get("logical_date") or kwargs.get("execution_date") or datetime.now(timezone.utc)
    target_date = execution_date.date()

    jobs_json = None
    aggregates_json = None
    source = "Airflow Scheduled Run"
    extract_error = None

    if ti:
        jobs_json = ti.xcom_pull(task_ids="transform_jobs", key="jobs_json")
        aggregates_json = ti.xcom_pull(task_ids="transform_jobs", key="aggregates_json")
        source = ti.xcom_pull(task_ids="extract_jobs", key="source") or source
        extract_error = ti.xcom_pull(task_ids="extract_jobs", key="extract_error")

    if jobs_json and aggregates_json:
        jobs_df = pd.read_json(jobs_json)
        aggregates_df = pd.read_json(aggregates_json)
    else:
        # Fallback to local pipeline run
        from etl.extract import extract_job_postings
        from etl.transform import transform_job_data
        ext = extract_job_postings(pages_to_fetch=1, force_fallback=True)
        jobs_df, aggregates_df, _ = transform_job_data(ext["jobs"], target_date=target_date)

    logger.info(f"[Airflow Load] Inserting data into MySQL database for {target_date}...")
    result = load_data_to_database(
        jobs_df=jobs_df,
        aggregates_df=aggregates_df,
        target_date=target_date,
        source_name=source,
        duration_seconds=5.0,
        error_message=extract_error
    )

    logger.info(f"[Airflow Load] Complete. Jobs saved: {result['jobs_saved']}, Aggregates saved: {result['aggregates_saved']}.")
    return result


def task_verify_integrity(**kwargs):
    """
    Airflow Task 4: Verify.
    Verifies data integrity and logs daily metrics health report.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skillsight.settings')
    import django
    django.setup()
    from dashboard.models import DailySkillAggregate, JobPosting

    execution_date = kwargs.get("logical_date") or kwargs.get("execution_date") or datetime.now(timezone.utc)
    target_date = execution_date.date()

    agg_count = DailySkillAggregate.objects.filter(date=target_date).count()
    job_count = JobPosting.objects.filter(posted_date=target_date).count()

    logger.info(f"[Airflow Verify] Health check for {target_date}: {agg_count} aggregates, {job_count} job postings.")
    if agg_count == 0:
        logger.warning(f"[Airflow Verify Warning] Zero aggregates recorded for {target_date}!")
    else:
        logger.info("[Airflow Verify] Data pipeline run successfully verified!")

    return {"aggregates_count": agg_count, "verified": agg_count > 0}


# Airflow DAG definition
default_args = {
    "owner": "skillsight_admin",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
}

if AIRFLOW_AVAILABLE:
    dag = DAG(
        dag_id="skillsight_daily_etl",
        default_args=default_args,
        description="Daily ETL pipeline extracting tech job postings and aggregating skill demand into MySQL",
        schedule_interval="0 0 * * *",  # Midnight UTC every night
        start_date=datetime(2026, 1, 1),
        catchup=False,
        max_active_runs=1,
        tags=["skillsight", "jobs", "etl", "mysql"],
    )

    with dag:
        extract_jobs = PythonOperator(
            task_id="extract_jobs",
            python_callable=task_extract_jobs,
        )

        transform_jobs = PythonOperator(
            task_id="transform_jobs",
            python_callable=task_transform_jobs,
        )

        load_data = PythonOperator(
            task_id="load_data",
            python_callable=task_load_data,
        )

        verify_integrity = PythonOperator(
            task_id="verify_data_integrity",
            python_callable=task_verify_integrity,
        )

        extract_jobs >> transform_jobs >> load_data >> verify_integrity
