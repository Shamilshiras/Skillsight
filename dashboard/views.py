"""
SkillSight Views and REST API Controllers.
Serves interactive HTML dashboard and high-performance REST APIs for Chart.js visualization.
"""
from datetime import datetime, timedelta, timezone, date
import logging
from django.shortcuts import render
from django.db.models import Sum, Avg, Count, Max, Q, F
from django.core.paginator import Paginator
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import Skill, JobPosting, DailySkillAggregate, PipelineRunLog
from .serializers import (
    SkillSerializer,
    JobPostingSerializer,
    DailySkillAggregateSerializer,
    PipelineRunLogSerializer,
)

logger = logging.getLogger(__name__)


def dashboard_view(request):
    """
    Renders the main interactive SkillSight Analytics Dashboard.
    """
    total_jobs = JobPosting.objects.count()
    total_skills = Skill.objects.count()
    latest_log = PipelineRunLog.objects.first()
    
    context = {
        'total_jobs': total_jobs,
        'total_skills': total_skills,
        'latest_log': latest_log,
        'now_year': datetime.now().year,
    }
    return render(request, 'dashboard/index.html', context)


@api_view(['GET'])
def summary_api(request):
    """
    Returns high-level KPI metrics for the dashboard summary cards:
    - Total jobs analyzed
    - Top programming language (this week)
    - Top framework (this week)
    - Remote job percentage
    - Latest ETL pipeline status
    """
    days = int(request.GET.get('days', 7))
    start_date = datetime.now(timezone.utc).date() - timedelta(days=days)

    total_jobs_analyzed = JobPosting.objects.filter(posted_date__gte=start_date).count()
    if total_jobs_analyzed == 0:
        total_jobs_analyzed = JobPosting.objects.count()

    remote_count = JobPosting.objects.filter(posted_date__gte=start_date, is_remote=True).count()
    remote_percentage = round((remote_count / total_jobs_analyzed * 100), 1) if total_jobs_analyzed else 0

    # Top language in the window
    top_lang_agg = (
        DailySkillAggregate.objects.filter(date__gte=start_date, skill__category='language')
        .values('skill__name')
        .annotate(total_mentions=Sum('job_count'))
        .order_by('-total_mentions')
        .first()
    )
    top_language = top_lang_agg['skill__name'] if top_lang_agg else "Python"

    # Top framework in the window
    top_framework_agg = (
        DailySkillAggregate.objects.filter(date__gte=start_date, skill__category='framework')
        .values('skill__name')
        .annotate(total_mentions=Sum('job_count'))
        .order_by('-total_mentions')
        .first()
    )
    top_framework = top_framework_agg['skill__name'] if top_framework_agg else "React"

    # Fastest growing skill (compare last 7 days vs previous 7 days)
    mid_date = datetime.now(timezone.utc).date() - timedelta(days=7)
    prior_date = mid_date - timedelta(days=7)

    recent_skills = dict(
        DailySkillAggregate.objects.filter(date__gte=mid_date)
        .values('skill__name')
        .annotate(cnt=Sum('job_count'))
        .values_list('skill__name', 'cnt')
    )
    prior_skills = dict(
        DailySkillAggregate.objects.filter(date__gte=prior_date, date__lt=mid_date)
        .values('skill__name')
        .annotate(cnt=Sum('job_count'))
        .values_list('skill__name', 'cnt')
    )

    fastest_growth_skill = "Python"
    max_growth_pct = 0.0
    for name, r_cnt in recent_skills.items():
        p_cnt = prior_skills.get(name, 0)
        if p_cnt > 0:
            growth = ((r_cnt - p_cnt) / p_cnt) * 100
        else:
            growth = 100.0 if r_cnt > 0 else 0.0
        if growth > max_growth_pct:
            max_growth_pct = growth
            fastest_growth_skill = name

    latest_log = PipelineRunLog.objects.first()
    latest_run_info = None
    if latest_log:
        latest_run_info = {
            'run_id': latest_log.run_id,
            'status': latest_log.status,
            'source': latest_log.source,
            'executed_at': latest_log.executed_at.isoformat(),
            'duration_seconds': latest_log.duration_seconds,
            'jobs_fetched': latest_log.jobs_fetched,
            'error_message': latest_log.error_message,
        }

    return Response({
        'total_jobs_analyzed': total_jobs_analyzed,
        'remote_percentage': remote_percentage,
        'top_language': top_language,
        'top_framework': top_framework,
        'fastest_growing_skill': fastest_growth_skill,
        'fastest_growth_percentage': round(max_growth_pct, 1),
        'latest_pipeline_run': latest_run_info,
    })


@api_view(['GET'])
def top_skills_api(request):
    """
    Returns top requested technical skills for bar chart visualization.
    Query params:
        - days: int (default 7)
        - category: 'all', 'language', 'framework', 'database', 'cloud_devops' (default 'language')
        - limit: int (default 10)
    """
    days = int(request.GET.get('days', 7))
    category = request.GET.get('category', 'language').strip().lower()
    limit = int(request.GET.get('limit', 10))

    start_date = datetime.now(timezone.utc).date() - timedelta(days=days)

    filters = Q(date__gte=start_date)
    if category != 'all':
        filters &= Q(skill__category=category)

    # Aggregate by skill
    aggregates = (
        DailySkillAggregate.objects.filter(filters)
        .values('skill__id', 'skill__name', 'skill__slug', 'skill__category', 'skill__color')
        .annotate(
            total_jobs=Sum('job_count'),
            avg_demand=Avg('demand_percentage'),
            total_scanned=Sum('total_jobs_analyzed')
        )
        .order_by('-total_jobs')[:limit]
    )

    results = []
    for item in aggregates:
        results.append({
            'skill_id': item['skill__id'],
            'name': item['skill__name'],
            'slug': item['skill__slug'],
            'category': item['skill__category'],
            'color': item['skill__color'],
            'job_count': item['total_jobs'] or 0,
            'demand_percentage': round(item['avg_demand'] or 0.0, 1),
        })

    return Response({
        'time_window_days': days,
        'category': category,
        'count': len(results),
        'skills': results,
    })


@api_view(['GET'])
def trends_api(request):
    """
    Returns historical daily trend line data for specified technologies.
    Query params:
        - skills: comma-separated skill slugs (e.g., 'django,flask' or 'react,vue')
        - days: int (default 30)
    """
    skills_param = request.GET.get('skills', 'django,flask').strip()
    days = int(request.GET.get('days', 30))

    skill_slugs = [s.strip().lower() for s in skills_param.split(',') if s.strip()]
    if not skill_slugs:
        skill_slugs = ['django', 'flask']

    start_date = datetime.now(timezone.utc).date() - timedelta(days=days)

    # Fetch skills
    matched_skills = Skill.objects.filter(slug__in=skill_slugs)
    skill_meta = {s.id: {'name': s.name, 'slug': s.slug, 'color': s.color} for s in matched_skills}

    # Fetch daily aggregates
    aggregates = (
        DailySkillAggregate.objects.filter(
            skill__slug__in=skill_slugs,
            date__gte=start_date
        )
        .select_related('skill')
        .order_by('date')
    )

    # Collect sorted unique dates
    dates_set = sorted(list(set(agg.date.strftime('%Y-%m-%d') for agg in aggregates)))
    
    # If no dates found, generate placeholder dates
    if not dates_set:
        today = datetime.now(timezone.utc).date()
        dates_set = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in reversed(range(days))]

    # Build series for each requested skill
    series_map = {}
    for skill_obj in matched_skills:
        series_map[skill_obj.slug] = {
            'name': skill_obj.name,
            'slug': skill_obj.slug,
            'color': skill_obj.color,
            'job_counts': {d: 0 for d in dates_set},
            'demand_percentages': {d: 0.0 for d in dates_set},
        }

    for agg in aggregates:
        slug = agg.skill.slug
        d_str = agg.date.strftime('%Y-%m-%d')
        if slug in series_map and d_str in series_map[slug]['job_counts']:
            series_map[slug]['job_counts'][d_str] = agg.job_count
            series_map[slug]['demand_percentages'][d_str] = round(agg.demand_percentage, 1)

    series_data = []
    for slug, info in series_map.items():
        series_data.append({
            'name': info['name'],
            'slug': slug,
            'color': info['color'],
            'counts': [info['job_counts'][d] for d in dates_set],
            'percentages': [info['demand_percentages'][d] for d in dates_set],
        })

    return Response({
        'days': days,
        'dates': dates_set,
        'series': series_data,
    })


@api_view(['GET'])
def categories_api(request):
    """
    Returns all tracked technical skills organized by category.
    """
    skills = Skill.objects.all().order_by('category', 'name')
    grouped = {}
    for s in skills:
        cat = s.category
        if cat not in grouped:
            grouped[cat] = {
                'category_slug': cat,
                'category_name': s.get_category_display(),
                'skills': [],
            }
        grouped[cat]['skills'].append({
            'id': s.id,
            'name': s.name,
            'slug': s.slug,
            'color': s.color,
        })

    return Response({
        'categories': list(grouped.values())
    })


@api_view(['GET'])
def job_list_api(request):
    """
    Returns paginated job listings with matched skill badges.
    Query params:
        - page: int (default 1)
        - page_size: int (default 10)
        - skill: filter by skill slug
        - remote: filter by remote (true/false)
        - search: search keyword
    """
    skill_filter = request.GET.get('skill', '').strip()
    remote_filter = request.GET.get('remote', '').strip().lower()
    search_query = request.GET.get('search', '').strip()

    queryset = JobPosting.objects.prefetch_related('skills').order_by('-posted_date', '-created_at')

    if skill_filter:
        queryset = queryset.filter(skills__slug=skill_filter)
    if remote_filter in ('true', '1'):
        queryset = queryset.filter(is_remote=True)
    elif remote_filter in ('false', '0'):
        queryset = queryset.filter(is_remote=False)
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query) |
            Q(company_name__icontains=search_query) |
            Q(location__icontains=search_query)
        )

    page_number = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 10))

    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page_number)

    serializer = JobPostingSerializer(page_obj.object_list, many=True)

    return Response({
        'total_count': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': page_obj.number,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'jobs': serializer.data,
    })


@api_view(['GET'])
def pipeline_logs_api(request):
    """
    Returns pipeline execution logs for system administrator inspection and debugging.
    """
    limit = int(request.GET.get('limit', 20))
    logs = PipelineRunLog.objects.all().order_by('-executed_at')[:limit]
    serializer = PipelineRunLogSerializer(logs, many=True)
    return Response({
        'count': len(serializer.data),
        'logs': serializer.data,
    })


@api_view(['POST'])
def trigger_etl_api(request):
    """
    Triggers an on-demand run of the SkillSight ETL pipeline.
    """
    from etl.pipeline import run_etl_pipeline
    pages = int(request.data.get('pages', 2) or 2)
    force_fallback = bool(request.data.get('force_fallback', False))

    try:
        result = run_etl_pipeline(pages_to_fetch=pages, force_fallback=force_fallback)
        return Response({
            'message': 'ETL Pipeline executed successfully.',
            'details': result
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Manual ETL run failed: {e}", exc_info=True)
        return Response({
            'message': 'ETL Pipeline execution failed.',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
