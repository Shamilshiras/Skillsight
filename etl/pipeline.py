"""
SkillSight ETL Pipeline Orchestrator.
Coordinates the end-to-end execution of the Extract, Transform, and Load phases.
Can be invoked programmatically, from an Airflow DAG task, or via CLI.
"""
import time
import logging
from datetime import datetime, timezone, date
from typing import Dict, Any, Optional

from .extract import extract_job_postings
from .transform import transform_job_data
from .load import load_data_to_database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)
logger = logging.getLogger("skillsight.etl")


def run_etl_pipeline(
    pages_to_fetch: int = 3,
    target_date: Optional[date] = None,
    force_fallback: bool = False
) -> Dict[str, Any]:
    """
    Executes the full SkillSight ETL pipeline:
    1. Extract: Fetches job postings from public APIs (e.g., Arbeitnow)
    2. Transform: Cleans text with Pandas, scans for tech keywords, generates aggregates
    3. Load: Inserts cleaned jobs & aggregates into MySQL / Django DB
    
    Args:
        pages_to_fetch: Number of API pages to query.
        target_date: Date to record aggregates under (defaults to today).
        force_fallback: Whether to use fallback sample dataset directly.
        
    Returns:
        Summary dict containing execution status, counts, and timings.
    """
    start_time = time.time()
    if target_date is None:
        target_date = datetime.now(timezone.utc).date()

    logger.info(f"=== Starting SkillSight ETL Pipeline Run for {target_date} ===")

    # Phase 1: Extract
    extract_result = extract_job_postings(
        pages_to_fetch=pages_to_fetch,
        force_fallback=force_fallback
    )
    raw_jobs = extract_result.get("jobs", [])
    source = extract_result.get("source", "Job API")
    extract_error = extract_result.get("error")

    logger.info(f"Extract Phase Complete: {len(raw_jobs)} jobs retrieved from {source}.")

    # Phase 2: Transform
    jobs_df, aggregates_df, summary_stats = transform_job_data(
        raw_jobs=raw_jobs,
        target_date=target_date
    )

    logger.info(
        f"Transform Phase Complete: {len(jobs_df)} jobs normalized, "
        f"{len(aggregates_df)} aggregate skill metrics computed."
    )

    # Phase 3: Load
    elapsed_time = time.time() - start_time
    load_result = load_data_to_database(
        jobs_df=jobs_df,
        aggregates_df=aggregates_df,
        target_date=target_date,
        source_name=source,
        duration_seconds=elapsed_time,
        error_message=extract_error
    )

    total_duration = time.time() - start_time
    logger.info(f"=== SkillSight ETL Pipeline Run Completed in {total_duration:.2f}s ===")

    return {
        "status": "SUCCESS",
        "target_date": str(target_date),
        "source": source,
        "jobs_extracted": len(raw_jobs),
        "jobs_saved": load_result["jobs_saved"],
        "aggregates_saved": load_result["aggregates_saved"],
        "total_skills_identified": load_result["total_skills_identified"],
        "duration_seconds": round(total_duration, 2),
        "summary": summary_stats,
    }
