"""
SkillSight ETL - Transformation Module.
Parses JSON with Pandas, cleans and normalizes text, extracts technical keywords
using regular expressions, and computes daily demand metrics and aggregates.
"""
import re
import html
import logging
from datetime import datetime, timezone, date
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd

from .config import TECH_SKILLS

logger = logging.getLogger(__name__)


def clean_html_text(text: str) -> str:
    """Strips HTML tags, unescapes HTML entities, and normalizes whitespace."""
    if not text or not isinstance(text, str):
        return ""
    # Unescape HTML entities (&amp; -> &, &lt; -> <, etc.)
    unescaped = html.unescape(text)
    # Remove HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", unescaped)
    # Normalize multiple whitespace characters
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def extract_skills_from_text(text: str, tags: List[str] = None) -> List[Dict[str, Any]]:
    """
    Scans cleaned job description, title, and tags for technical skill keywords.
    
    Args:
        text: Combined title and description text.
        tags: Optional list of skill tags provided by the API.
        
    Returns:
        List of matched skill dictionaries containing name, slug, category, and color.
    """
    matched_skills = []
    text_lower = text.lower() if text else ""
    tag_set = {t.lower().strip() for t in (tags or []) if t}

    for skill in TECH_SKILLS:
        pattern = skill["pattern"]
        slug = skill["slug"]
        name_lower = skill["name"].lower()

        # Check in explicit tags or regex match in text
        matched_in_tags = (name_lower in tag_set) or (slug in tag_set)
        matched_in_text = bool(re.search(pattern, text_lower, re.IGNORECASE))

        if matched_in_tags or matched_in_text:
            matched_skills.append({
                "name": skill["name"],
                "slug": skill["slug"],
                "category": skill["category"],
                "color": skill["color"],
            })

    return matched_skills


def transform_job_data(
    raw_jobs: List[Dict[str, Any]],
    target_date: Optional[date] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Transforms raw API job postings into structured Pandas DataFrames:
    1. Normalized jobs DataFrame with extracted skill keywords.
    2. Daily aggregate metrics DataFrame for optimized time-series queries.
    3. Summary analytics dictionary.
    
    Args:
        raw_jobs: Raw JSON job postings list.
        target_date: The date to associate with daily aggregates (defaults to today).
        
    Returns:
        Tuple of (jobs_df, aggregates_df, summary_stats)
    """
    if target_date is None:
        target_date = datetime.now(timezone.utc).date()

    logger.info(f"Transforming {len(raw_jobs)} job postings with Pandas.")

    processed_rows = []
    for item in raw_jobs:
        # Extract external job identifier
        job_id = str(item.get("slug") or item.get("id") or item.get("url") or f"job-{len(processed_rows)+1}")
        title = item.get("title", "Software Engineer").strip()
        company = item.get("company_name", "Unknown Tech Co.").strip()
        location = item.get("location", "Remote").strip()
        is_remote = bool(item.get("remote", False) or "remote" in location.lower())
        
        job_types = item.get("job_types", ["Full-time"])
        job_type = job_types[0] if isinstance(job_types, list) and job_types else "Full-time"
        url = item.get("url", "")
        raw_description = item.get("description", "")
        clean_desc = clean_html_text(raw_description)

        # Parse posted date
        created_val = item.get("created_at")
        job_posted_date = target_date
        if isinstance(created_val, (int, float)):
            try:
                job_posted_date = datetime.fromtimestamp(created_val, tz=timezone.utc).date()
            except Exception:
                job_posted_date = target_date
        elif isinstance(created_val, str):
            try:
                # Try ISO parsing
                job_posted_date = datetime.fromisoformat(created_val.replace("Z", "+00:00")).date()
            except Exception:
                job_posted_date = target_date

        tags = item.get("tags") or []
        combined_text = f"{title} {clean_desc}"
        matched_skills = extract_skills_from_text(combined_text, tags)

        processed_rows.append({
            "job_id": job_id,
            "title": title,
            "company_name": company,
            "location": location,
            "is_remote": is_remote,
            "job_type": job_type,
            "url": url,
            "description_snippet": clean_desc[:400] + ("..." if len(clean_desc) > 400 else ""),
            "posted_date": job_posted_date,
            "matched_skills": matched_skills,
            "skill_count": len(matched_skills),
            "skill_slugs": [s["slug"] for s in matched_skills],
        })

    jobs_df = pd.DataFrame(processed_rows)

    if jobs_df.empty:
        empty_aggregates = pd.DataFrame(columns=[
            "date", "skill_name", "skill_slug", "category", "color",
            "job_count", "total_jobs_analyzed", "demand_percentage"
        ])
        return jobs_df, empty_aggregates, {"total_jobs": 0, "total_skills_detected": 0}

    total_jobs = len(jobs_df)

    # Calculate skill counts across all jobs
    skill_occurrences: Dict[str, Dict[str, Any]] = {}
    for skill_meta in TECH_SKILLS:
        slug = skill_meta["slug"]
        skill_occurrences[slug] = {
            "date": target_date,
            "skill_name": skill_meta["name"],
            "skill_slug": slug,
            "category": skill_meta["category"],
            "color": skill_meta["color"],
            "job_count": 0,
            "total_jobs_analyzed": total_jobs,
            "demand_percentage": 0.0,
        }

    for skill_list in jobs_df["matched_skills"]:
        for s in skill_list:
            slug = s["slug"]
            if slug in skill_occurrences:
                skill_occurrences[slug]["job_count"] += 1

    # Calculate percentages
    for slug, record in skill_occurrences.items():
        if total_jobs > 0:
            percentage = round((record["job_count"] / total_jobs) * 100.0, 2)
            record["demand_percentage"] = percentage

    aggregates_df = pd.DataFrame(list(skill_occurrences.values()))
    aggregates_df.sort_values(by="job_count", ascending=False, inplace=True)

    # Top skills summary
    top_languages = aggregates_df[aggregates_df["category"] == "language"].head(5)
    top_frameworks = aggregates_df[aggregates_df["category"] == "framework"].head(5)

    summary_stats = {
        "target_date": str(target_date),
        "total_jobs": total_jobs,
        "remote_jobs": int(jobs_df["is_remote"].sum()),
        "remote_percentage": round((jobs_df["is_remote"].sum() / total_jobs) * 100.0, 1) if total_jobs else 0,
        "total_skills_tracked": len(TECH_SKILLS),
        "active_skills_detected": int((aggregates_df["job_count"] > 0).sum()),
        "top_language": top_languages.iloc[0]["skill_name"] if not top_languages.empty else "N/A",
        "top_framework": top_frameworks.iloc[0]["skill_name"] if not top_frameworks.empty else "N/A",
    }

    logger.info(
        f"Transform complete: {total_jobs} jobs analyzed. "
        f"Top language: {summary_stats['top_language']}, Top framework: {summary_stats['top_framework']}."
    )

    return jobs_df, aggregates_df, summary_stats
