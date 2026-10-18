"""
SkillSight ETL - Extraction Module.
Fetches daily tech job postings from public APIs (e.g. Arbeitnow)
with fault-tolerant fallback mechanisms, pagination support, and structured logging.
"""
import logging
import requests
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from .config import DEFAULT_API_URL, API_TIMEOUT_SECONDS, DEFAULT_FETCH_PAGES

logger = logging.getLogger(__name__)

# Sample job dataset used for resilient offline execution and test mocking
SAMPLE_FALLBACK_JOBS = [
    {
        "slug": "senior-python-django-engineer-101",
        "title": "Senior Python / Django Backend Engineer",
        "company_name": "CloudScale Systems",
        "location": "San Francisco, CA",
        "remote": True,
        "job_types": ["Full-time"],
        "url": "https://example.com/jobs/senior-python-django",
        "description": "We are seeking a Senior Python Engineer experienced in Django, FastAPI, PostgreSQL, Redis, and Docker. Experience with AWS, Kubernetes, and CI/CD pipelines is a huge plus.",
        "tags": ["Python", "Django", "FastAPI", "PostgreSQL", "Docker", "AWS"],
        "created_at": int(time.time()),
    },
    {
        "slug": "full-stack-react-typescript-developer-102",
        "title": "Full Stack Developer (React & TypeScript & Node.js)",
        "company_name": "Nexus Fintech",
        "location": "New York, NY",
        "remote": True,
        "job_types": ["Full-time"],
        "url": "https://example.com/jobs/fullstack-react-ts",
        "description": "Looking for a modern web engineer with strong skills in React, TypeScript, Next.js, Node.js, Express, and MySQL. Familiarity with Git, Linux, and REST APIs is required.",
        "tags": ["React", "TypeScript", "Next.js", "Node.js", "MySQL", "Git"],
        "created_at": int(time.time()),
    },
    {
        "slug": "devops-cloud-architect-103",
        "title": "DevOps & Cloud Infrastructure Architect",
        "company_name": "DataFlow Networks",
        "location": "Austin, TX",
        "remote": False,
        "job_types": ["Full-time"],
        "url": "https://example.com/jobs/devops-architect",
        "description": "Lead our cloud infrastructure with AWS, Terraform, Docker, Kubernetes, Linux, and automated CI/CD. Scripting experience in Python or Go is required.",
        "tags": ["AWS", "Docker", "Kubernetes", "Terraform", "Linux", "CI/CD", "Go", "Python"],
        "created_at": int(time.time()),
    },
    {
        "slug": "backend-go-distributed-systems-104",
        "title": "Backend Go Engineer - High Throughput Systems",
        "company_name": "StreamPulse Inc.",
        "location": "Seattle, WA",
        "remote": True,
        "job_types": ["Full-time"],
        "url": "https://example.com/jobs/backend-go-engineer",
        "description": "Build microservices in Go and Rust with MySQL, PostgreSQL, Redis, and Kafka. We deploy on GCP with Kubernetes and Docker.",
        "tags": ["Go", "Rust", "MySQL", "PostgreSQL", "Redis", "GCP", "Kubernetes"],
        "created_at": int(time.time()),
    },
    {
        "slug": "frontend-engineer-vue-angular-105",
        "title": "Senior Frontend Engineer (Vue.js / Angular)",
        "company_name": "Creative Interactive",
        "location": "Chicago, IL",
        "remote": True,
        "job_types": ["Contract"],
        "url": "https://example.com/jobs/frontend-vue-angular",
        "description": "Build high-performance web apps with Vue.js, Angular, JavaScript, HTML5, CSS3, and TypeScript. Experience integrating with Django and Flask REST APIs.",
        "tags": ["Vue.js", "Angular", "JavaScript", "TypeScript", "Django", "Flask"],
        "created_at": int(time.time()),
    },
    {
        "slug": "data-engineer-python-sql-106",
        "title": "Data Engineer (Python, SQL, Spark)",
        "company_name": "Insight Analytics",
        "location": "Boston, MA",
        "remote": True,
        "job_types": ["Full-time"],
        "url": "https://example.com/jobs/data-engineer-python-sql",
        "description": "Develop ETL pipelines using Python, SQL, PostgreSQL, MongoDB, Elasticsearch, and Docker. Experience with AWS cloud data services preferred.",
        "tags": ["Python", "SQL", "PostgreSQL", "MongoDB", "Elasticsearch", "AWS"],
        "created_at": int(time.time()),
    },
    {
        "slug": "java-spring-boot-enterprise-developer-107",
        "title": "Java Spring Boot Enterprise Developer",
        "company_name": "Apex Banking Solutions",
        "location": "London, UK",
        "remote": False,
        "job_types": ["Full-time"],
        "url": "https://example.com/jobs/java-spring-developer",
        "description": "Modernize enterprise microservices using Java, Spring Boot, MySQL, Docker, Kubernetes, and Azure. Experience in CI/CD and Linux environment.",
        "tags": ["Java", "Spring Boot", "MySQL", "Docker", "Kubernetes", "Azure", "CI/CD"],
        "created_at": int(time.time()),
    },
    {
        "slug": "ruby-on-rails-engineer-108",
        "title": "Senior Ruby on Rails Developer",
        "company_name": "SaaS Rocket",
        "location": "Remote, Global",
        "remote": True,
        "job_types": ["Full-time"],
        "url": "https://example.com/jobs/rails-developer",
        "description": "Looking for a seasoned Ruby on Rails developer with PostgreSQL, Redis, JavaScript, React, and Git. Fast-paced product company.",
        "tags": ["Ruby", "Ruby on Rails", "PostgreSQL", "Redis", "JavaScript", "React"],
        "created_at": int(time.time()),
    },
    {
        "slug": "mobile-engineer-swift-kotlin-109",
        "title": "Mobile Engineer (Swift & Kotlin)",
        "company_name": "AppWorks Studio",
        "location": "Berlin, Germany",
        "remote": True,
        "job_types": ["Full-time"],
        "url": "https://example.com/jobs/mobile-swift-kotlin",
        "description": "Build native iOS and Android apps using Swift and Kotlin. Interfacing with Node.js and Django backends via REST APIs.",
        "tags": ["Swift", "Kotlin", "Node.js", "Django", "Git"],
        "created_at": int(time.time()),
    },
    {
        "slug": "csharp-dotnet-cloud-engineer-110",
        "title": ".NET Core / C# Cloud Engineer",
        "company_name": "Horizon Digital",
        "location": "Toronto, Canada",
        "remote": True,
        "job_types": ["Full-time"],
        "url": "https://example.com/jobs/csharp-dotnet-engineer",
        "description": "Develop cloud-native services using C#, .NET Core, Azure, SQL Server, MySQL, Docker, and CI/CD pipelines.",
        "tags": ["C#", ".NET Core", "Azure", "MySQL", "Docker", "CI/CD"],
        "created_at": int(time.time()),
    },
]


def extract_job_postings(
    api_url: str = DEFAULT_API_URL,
    pages_to_fetch: int = DEFAULT_FETCH_PAGES,
    force_fallback: bool = False
) -> Dict[str, Any]:
    """
    Extracts tech job postings from public job API.
    
    Args:
        api_url: Public API URL endpoint
        pages_to_fetch: Number of pages to paginate through
        force_fallback: If True, uses offline fallback dataset immediately (useful for sandboxed test runs)
        
    Returns:
        Dict containing:
            - 'jobs': List of raw job postings
            - 'source': Name of API source used
            - 'page_count': Number of pages requested
            - 'status': 'SUCCESS' or 'FALLBACK'
            - 'error': Optional error message if API failed
    """
    if force_fallback:
        logger.info("Using fallback sample job postings dataset (force_fallback=True)")
        return {
            "jobs": SAMPLE_FALLBACK_JOBS,
            "source": "Sample Fallback Dataset",
            "page_count": 1,
            "status": "FALLBACK",
            "error": None,
        }

    raw_jobs: List[Dict[str, Any]] = []
    current_url: Optional[str] = api_url
    pages_completed = 0
    error_message: Optional[str] = None

    headers = {
        "User-Agent": "SkillSight-ETL-Bot/1.0 (Job Market Analytics)",
        "Accept": "application/json",
    }

    logger.info(f"Starting job extraction from API: {api_url}")

    for page in range(1, pages_to_fetch + 1):
        if not current_url:
            break

        try:
            logger.info(f"Fetching API page {page}: {current_url}")
            response = requests.get(current_url, headers=headers, timeout=API_TIMEOUT_SECONDS)
            
            if response.status_code == 200:
                data = response.json()
                page_data = data.get("data", [])
                raw_jobs.extend(page_data)
                pages_completed += 1
                
                # Check pagination next link
                links = data.get("links", {})
                current_url = links.get("next")
            else:
                error_message = f"API returned status {response.status_code}: {response.text[:200]}"
                logger.warning(error_message)
                break

        except Exception as e:
            error_message = f"API connection failed: {str(e)}"
            logger.warning(f"Error fetching from job API: {e}. Falling back to sample dataset.")
            break

    # If extraction returned jobs from API, return them
    if raw_jobs:
        logger.info(f"Successfully extracted {len(raw_jobs)} job postings from {pages_completed} pages.")
        return {
            "jobs": raw_jobs,
            "source": "Arbeitnow Public API",
            "page_count": pages_completed,
            "status": "SUCCESS",
            "error": error_message,
        }

    # If API call failed or yielded empty result, use fault-tolerant fallback
    logger.info("Engaging fallback dataset to guarantee ETL reliability.")
    return {
        "jobs": SAMPLE_FALLBACK_JOBS,
        "source": "Fallback Dataset (API Unavailable)",
        "page_count": 1,
        "status": "FALLBACK",
        "error": error_message,
    }
