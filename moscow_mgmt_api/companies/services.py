from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import median
from typing import Any, Iterable
from functools import lru_cache

from django.db import models
from django.db.models import (
    Case,
    CharField,
    DecimalField,
    ExpressionWrapper,
    F,
    FloatField,
    IntegerField,
    Max,
    OuterRef,
    Prefetch,
    QuerySet,
    Subquery,
    Value,
    When,
)

from django.db.models.functions import Cast, Coalesce, Least

from .models import ManagingCompany, ManagingCompanyYearStat

ZERO = Decimal('0')
METRIC_LABELS = {
    'violations_per_house': 'нарушения на один дом',
    'fines_per_house': 'штрафы на один дом',
    'fines_per_1000_m2': 'штрафы на 1000 кв. м',
    'prescriptions_per_house': 'предписания на один дом',
    'protocols_per_house': 'протоколы на один дом',
    'overdue_events_rate': 'доля просроченных мероприятий',
    'problem_index': 'индекс проблемности',
}

def metric_label(metric_name: str) -> str:
    return METRIC_LABELS.get(metric_name, metric_name)


def join_metric_labels(metric_names: list[str]) -> str:
    labels = [metric_label(name) for name in metric_names]
    return ', '.join(labels)

@dataclass
class MetricBundle:
    violations_per_house: float
    fines_per_house: float
    fines_per_1000_m2: float
    prescriptions_per_house: float
    protocols_per_house: float
    overdue_events_rate: float
    problem_index: float



def decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)

# @lru_cache(maxsize=32)
# def get_service_rank_map(year: int) -> dict[int, int]:
#     stats = list(
#         ManagingCompanyYearStat.objects.filter(year=year).select_related('company')
#     )

#     stats.sort(
#         key=lambda stat: (
#             compute_metrics(stat).problem_index,
#             -(stat.houses_quantity or 0),
#             stat.company.short_name or stat.company.full_name or '',
#             stat.company_id,
#         )
#     )

#     return {stat.id: index + 1 for index, stat in enumerate(stats)}
@lru_cache(maxsize=32)
def get_service_rank_map(year: int) -> dict[int, int]:
    stats = list(
        ManagingCompanyYearStat.objects.filter(year=year).select_related('company')
    )

    stats.sort(
        key=lambda stat: (
            compute_metrics(stat).problem_index,
            -(stat.houses_quantity or 0),
            stat.company.short_name or stat.company.full_name or '',
            stat.company_id,
        )
    )

    rank_map: dict[int, int] = {}
    current_rank = 0
    previous_problem_index = None

    for stat in stats:
        current_problem_index = compute_metrics(stat).problem_index

        if previous_problem_index is None or current_problem_index != previous_problem_index:
            current_rank += 1

        rank_map[stat.id] = current_rank
        previous_problem_index = current_problem_index

    return rank_map


def get_service_rank(stat: ManagingCompanyYearStat | None) -> int | None:
    if not stat:
        return None
    return get_service_rank_map(stat.year).get(stat.id)

def get_latest_year() -> int | None:
    rated_year = (
        ManagingCompanyYearStat.objects
        .filter(final_rating__isnull=False)
        .aggregate(max_year=Max('year'))
        .get('max_year')
    )
    if rated_year is not None:
        return rated_year

    return ManagingCompanyYearStat.objects.aggregate(max_year=Max('year')).get('max_year')



def resolve_year(requested_year: int | None) -> int | None:
    return requested_year or get_latest_year()



def stat_for_year(company: ManagingCompany, year: int | None) -> ManagingCompanyYearStat | None:
    if year is None:
        return None
    cached = getattr(company, 'selected_year_stats', None)
    if cached:
        return cached[0] if cached else None
    return company.year_stats.filter(year=year).first()

def annotate_selected_stats(queryset: QuerySet[ManagingCompany], year: int | None) -> QuerySet[ManagingCompany]:
    stats = ManagingCompanyYearStat.objects.filter(company_id=OuterRef('pk'))

    if year is not None:
        stats = stats.filter(year=year).order_by('-id')
    else:
        stats = stats.order_by('-year', '-id')

    queryset = queryset.annotate(
        selected_year=Subquery(stats.values('year')[:1], output_field=IntegerField()),
        selected_adm_area=Subquery(stats.values('adm_area')[:1], output_field=CharField()),
        selected_houses_quantity=Subquery(stats.values('houses_quantity')[:1], output_field=IntegerField()),
        selected_houses_area=Subquery(stats.values('houses_area')[:1], output_field=IntegerField()),
        selected_total_area=Subquery(stats.values('total_area')[:1], output_field=IntegerField()),
        selected_final_rating=Subquery(stats.values('final_rating')[:1], output_field=IntegerField()),
        selected_total_amount_of_scores=Subquery(
            stats.values('total_amount_of_scores')[:1],
            output_field=DecimalField(max_digits=8, decimal_places=2),
        ),
        selected_issued_prescriptions=Subquery(
            stats.values('issued_prescriptions')[:1],
            output_field=IntegerField(),
        ),
        selected_violations_amount=Subquery(
            stats.values('violations_amount')[:1],
            output_field=IntegerField(),
        ),
        selected_protocols_composed=Subquery(
            stats.values('protocols_composed')[:1],
            output_field=IntegerField(),
        ),
        selected_cancelled_contracts_amount=Subquery(
            stats.values('cancelled_contracts_amount')[:1],
            output_field=IntegerField(),
        ),
        selected_events_executed=Subquery(
            stats.values('events_executed')[:1],
            output_field=IntegerField(),
        ),
        selected_events_not_executed_in_time=Subquery(
            stats.values('events_not_executed_in_time')[:1],
            output_field=IntegerField(),
        ),
        selected_sum_of_fine=Subquery(
            stats.values('sum_of_fine')[:1],
            output_field=DecimalField(max_digits=14, decimal_places=2),
        ),
    ).filter(selected_year__isnull=False)

    queryset = queryset.annotate(
        houses_for_calc=Case(
            When(selected_houses_quantity__gt=0, then=Cast(F('selected_houses_quantity'), FloatField())),
            default=Value(0.0),
            output_field=FloatField(),
        ),
        area_for_calc=Case(
            When(selected_houses_area__gt=0, then=Cast(F('selected_houses_area'), FloatField())),
            When(selected_total_area__gt=0, then=Cast(F('selected_total_area'), FloatField())),
            default=Value(0.0),
            output_field=FloatField(),
        ),
        total_events_for_calc=ExpressionWrapper(
            Cast(Coalesce(F('selected_events_executed'), Value(0)), FloatField())
            + Cast(Coalesce(F('selected_events_not_executed_in_time'), Value(0)), FloatField()),
            output_field=FloatField(),
        ),
    ).annotate(
        violations_per_house_sort=Case(
            When(
                houses_for_calc__gt=0,
                then=ExpressionWrapper(
                    Cast(Coalesce(F('selected_violations_amount'), Value(0)), FloatField()) / F('houses_for_calc'),
                    output_field=FloatField(),
                ),
            ),
            default=Value(0.0),
            output_field=FloatField(),
        ),
        prescriptions_per_house_sort=Case(
            When(
                houses_for_calc__gt=0,
                then=ExpressionWrapper(
                    Cast(Coalesce(F('selected_issued_prescriptions'), Value(0)), FloatField()) / F('houses_for_calc'),
                    output_field=FloatField(),
                ),
            ),
            default=Value(0.0),
            output_field=FloatField(),
        ),
        protocols_per_house_sort=Case(
            When(
                houses_for_calc__gt=0,
                then=ExpressionWrapper(
                    Cast(Coalesce(F('selected_protocols_composed'), Value(0)), FloatField()) / F('houses_for_calc'),
                    output_field=FloatField(),
                ),
            ),
            default=Value(0.0),
            output_field=FloatField(),
        ),
        fines_per_1000_m2_sort=Case(
            When(
                area_for_calc__gt=0,
                then=ExpressionWrapper(
                    Cast(Coalesce(F('selected_sum_of_fine'), Value(0)), FloatField()) * Value(1000.0)
                    / F('area_for_calc'),
                    output_field=FloatField(),
                ),
            ),
            default=Value(0.0),
            output_field=FloatField(),
        ),
        overdue_events_rate_sort=Case(
            When(
                total_events_for_calc__gt=0,
                then=ExpressionWrapper(
                    Cast(Coalesce(F('selected_events_not_executed_in_time'), Value(0)), FloatField())
                    / F('total_events_for_calc') * Value(100.0),
                    output_field=FloatField(),
                ),
            ),
            default=Value(0.0),
            output_field=FloatField(),
        ),
    ).annotate(
        problem_index_sort=ExpressionWrapper(
            F('violations_per_house_sort') * Value(18.0)
            + F('prescriptions_per_house_sort') * Value(14.0)
            + F('protocols_per_house_sort') * Value(10.0)
            + F('fines_per_1000_m2_sort') * Value(0.12)
            + F('overdue_events_rate_sort') * Value(0.3),
            output_field=FloatField(),
        )
    )

    return queryset


def annotate_problem_index(queryset: QuerySet[ManagingCompany], year: int | None) -> QuerySet[ManagingCompany]:
    if year is None:
        return queryset

    queryset = queryset.annotate(
        houses_for_calc=Case(
            When(year_stats__houses_quantity__gt=0, then=Cast(F('year_stats__houses_quantity'), FloatField())),
            default=Value(0.0),
            output_field=FloatField(),
        ),
        area_for_calc=Case(
            When(year_stats__houses_area__gt=0, then=Cast(F('year_stats__houses_area'), FloatField())),
            When(year_stats__total_area__gt=0, then=Cast(F('year_stats__total_area'), FloatField())),
            default=Value(0.0),
            output_field=FloatField(),
        ),
        total_events_for_calc=ExpressionWrapper(
            Cast(Coalesce(F('year_stats__events_executed'), Value(0)), FloatField())
            + Cast(Coalesce(F('year_stats__events_not_executed_in_time'), Value(0)), FloatField()),
            output_field=FloatField(),
        ),
    ).annotate(
        violations_per_house_sort=Case(
            When(
                houses_for_calc__gt=0,
                then=ExpressionWrapper(
                    Cast(Coalesce(F('year_stats__violations_amount'), Value(0)), FloatField()) / F('houses_for_calc'),
                    output_field=FloatField(),
                ),
            ),
            default=Value(0.0),
            output_field=FloatField(),
        ),
        prescriptions_per_house_sort=Case(
            When(
                houses_for_calc__gt=0,
                then=ExpressionWrapper(
                    Cast(Coalesce(F('year_stats__issued_prescriptions'), Value(0)), FloatField()) / F('houses_for_calc'),
                    output_field=FloatField(),
                ),
            ),
            default=Value(0.0),
            output_field=FloatField(),
        ),
        protocols_per_house_sort=Case(
            When(
                houses_for_calc__gt=0,
                then=ExpressionWrapper(
                    Cast(Coalesce(F('year_stats__protocols_composed'), Value(0)), FloatField()) / F('houses_for_calc'),
                    output_field=FloatField(),
                ),
            ),
            default=Value(0.0),
            output_field=FloatField(),
        ),
        fines_per_1000_m2_sort=Case(
            When(
                area_for_calc__gt=0,
                then=ExpressionWrapper(
                    Cast(Coalesce(F('year_stats__sum_of_fine'), Value(0)), FloatField()) * Value(1000.0) / F('area_for_calc'),
                    output_field=FloatField(),
                ),
            ),
            default=Value(0.0),
            output_field=FloatField(),
        ),
        overdue_events_rate_sort=Case(
            When(
                total_events_for_calc__gt=0,
                then=ExpressionWrapper(
                    Cast(Coalesce(F('year_stats__events_not_executed_in_time'), Value(0)), FloatField()) / F('total_events_for_calc') * Value(100.0),
                    output_field=FloatField(),
                ),
            ),
            default=Value(0.0),
            output_field=FloatField(),
        ),
    ).annotate(
        problem_index_sort=ExpressionWrapper(
            F('violations_per_house_sort') * Value(18.0)
            + F('prescriptions_per_house_sort') * Value(14.0)
            + F('protocols_per_house_sort') * Value(10.0)
            + F('fines_per_1000_m2_sort') * Value(0.12)
            + F('overdue_events_rate_sort') * Value(0.3),
            output_field=FloatField(),
        )
    )

    return queryset


def prefetch_year_stats(year: int | None) -> Prefetch | None:
    if year is None:
        return None
    return Prefetch(
        'year_stats',
        queryset=ManagingCompanyYearStat.objects.filter(year=year).select_related('company'),
        to_attr='selected_year_stats',
    )


def safe_div(numerator: float | Decimal | int, denominator: float | Decimal | int) -> float:
    denominator = float(denominator)
    if denominator == 0:
        return 0.0
    return round(float(numerator) / denominator, 4)



def compute_metrics(stat: ManagingCompanyYearStat) -> MetricBundle:
    houses = stat.houses_quantity or 0
    area = stat.houses_area or stat.total_area or 0
    total_events = (stat.events_executed or 0) + (stat.events_not_executed_in_time or 0)

    violations_per_house = safe_div(stat.violations_amount, houses)
    fines_per_house = safe_div(stat.sum_of_fine, houses)
    fines_per_1000_m2 = safe_div(stat.sum_of_fine, (area / 1000) if area else 0)
    prescriptions_per_house = safe_div(stat.issued_prescriptions, houses)
    protocols_per_house = safe_div(stat.protocols_composed, houses)
    overdue_events_rate = round(safe_div(stat.events_not_executed_in_time, total_events) * 100, 4) if total_events else 0.0

    problem_index = round(
        violations_per_house * 18
        + prescriptions_per_house * 14
        + protocols_per_house * 10
        + fines_per_1000_m2 * 0.12
        + overdue_events_rate * 0.3,
        2,
    )

    return MetricBundle(
        violations_per_house=violations_per_house,
        fines_per_house=fines_per_house,
        fines_per_1000_m2=fines_per_1000_m2,
        prescriptions_per_house=prescriptions_per_house,
        protocols_per_house=protocols_per_house,
        overdue_events_rate=overdue_events_rate,
        problem_index=problem_index,
    )


def compute_stability_index(history: list[ManagingCompanyYearStat]) -> float:
    if len(history) < 2:
        return 100.0

    rating_changes = 0.0
    problem_changes = 0.0
    pairs_count = 0
    for previous, current in zip(history, history[1:]):
        if previous.final_rating is not None and current.final_rating is not None:
            rating_changes += abs(current.final_rating - previous.final_rating)
        previous_problem = compute_metrics(previous).problem_index
        current_problem = compute_metrics(current).problem_index
        problem_changes += abs(current_problem - previous_problem)
        pairs_count += 1

    if pairs_count == 0:
        return 100.0

    avg_rating_change = rating_changes / pairs_count
    avg_problem_change = problem_changes / pairs_count
    stability = 100 - (avg_rating_change * 10 + avg_problem_change * 0.8)
    return round(max(0.0, min(100.0, stability)), 2)



def risk_level(problem_index: float) -> str:
    if problem_index >= 50:
        return 'high'
    if problem_index >= 20:
        return 'medium'
    return 'low'



def build_company_queryset(year: int | None) -> QuerySet[ManagingCompany]:
    queryset = ManagingCompany.objects.all()
    prefetch = prefetch_year_stats(year)
    if prefetch:
        queryset = queryset.prefetch_related(prefetch)
    return queryset



def filter_company_queryset(queryset: QuerySet[ManagingCompany], params: dict[str, Any], year: int | None) -> QuerySet[ManagingCompany]:
    if year is None:
        return queryset.none()

    queryset = queryset.filter(year_stats__year=year).distinct()

    search = params.get('search')
    if search:
        queryset = queryset.filter(
            models.Q(inn__icontains=search)
            | models.Q(full_name__icontains=search)
            | models.Q(short_name__icontains=search)
        )

    adm_area = params.get('adm_area')
    if adm_area:
        queryset = queryset.filter(year_stats__year=year, year_stats__adm_area=adm_area)

    official_rating = params.get('official_rating')
    if official_rating not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__final_rating=int(official_rating))

    official_rating_min = params.get('official_rating_min')
    if official_rating_min not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__final_rating__gte=int(official_rating_min))

    official_rating_max = params.get('official_rating_max')
    if official_rating_max not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__final_rating__lte=int(official_rating_max))

    scores_min = params.get('scores_min')
    if scores_min not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__total_amount_of_scores__gte=float(scores_min))

    scores_max = params.get('scores_max')
    if scores_max not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__total_amount_of_scores__lte=float(scores_max))

    houses_min = params.get('houses_min')
    if houses_min not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__houses_quantity__gte=int(houses_min))

    houses_max = params.get('houses_max')
    if houses_max not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__houses_quantity__lte=int(houses_max))

    area_min = params.get('area_min')
    if area_min not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__houses_area__gte=int(area_min))

    area_max = params.get('area_max')
    if area_max not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__houses_area__lte=int(area_max))

    ordering = params.get('ordering')

    if ordering == 'final_rating':
        ordering = 'problem_index'
    elif ordering == '-final_rating':
        ordering = '-problem_index'
    elif ordering == 'official_rating':
        ordering = 'db_final_rating'
    elif ordering == '-official_rating':
        ordering = '-db_final_rating'

    if ordering == 'name':
        queryset = queryset.order_by('short_name', 'id')
    elif ordering == '-name':
        queryset = queryset.order_by('-short_name', 'id')

    elif ordering == 'db_final_rating':
        queryset = queryset.order_by(F('year_stats__final_rating').asc(nulls_last=True), 'id')
    elif ordering == '-db_final_rating':
        queryset = queryset.order_by(F('year_stats__final_rating').desc(nulls_last=True), 'id')

    elif ordering == 'houses_quantity':
        queryset = queryset.order_by(F('year_stats__houses_quantity').asc(nulls_last=True), 'id')
    elif ordering == '-houses_quantity':
        queryset = queryset.order_by(F('year_stats__houses_quantity').desc(nulls_last=True), 'id')

    elif ordering == 'houses_area':
        queryset = queryset.order_by(F('year_stats__houses_area').asc(nulls_last=True), 'id')
    elif ordering == '-houses_area':
        queryset = queryset.order_by(F('year_stats__houses_area').desc(nulls_last=True), 'id')

    elif ordering == 'scores':
        queryset = queryset.order_by(F('year_stats__total_amount_of_scores').asc(nulls_last=True), 'id')
    elif ordering == '-scores':
        queryset = queryset.order_by(F('year_stats__total_amount_of_scores').desc(nulls_last=True), 'id')

    elif ordering == 'problem_index':
        queryset = annotate_problem_index(queryset, year).order_by(
            'problem_index_sort',
            F('year_stats__houses_quantity').desc(nulls_last=True),
            'id',
        )
    elif ordering == '-problem_index':
        queryset = annotate_problem_index(queryset, year).order_by(
            '-problem_index_sort',
            F('year_stats__houses_quantity').desc(nulls_last=True),
            'id',
        )

    else:
        queryset = queryset.order_by('short_name', 'id')

    return queryset


def get_similar_stats(stat: ManagingCompanyYearStat, limit: int = 5) -> list[ManagingCompanyYearStat]:
    houses = stat.houses_quantity or 1
    area = stat.houses_area or stat.total_area or 1

    lower_houses = max(1, int(houses * 0.5))
    upper_houses = max(lower_houses, int(houses * 1.5))
    lower_area = max(1, int(area * 0.5))
    upper_area = max(lower_area, int(area * 1.5))

    queryset = ManagingCompanyYearStat.objects.filter(year=stat.year).exclude(company_id=stat.company_id)
    if stat.adm_area:
        queryset = queryset.filter(adm_area=stat.adm_area)
    queryset = queryset.filter(houses_quantity__gte=lower_houses, houses_quantity__lte=upper_houses)
    queryset = queryset.filter(houses_area__gte=lower_area, houses_area__lte=upper_area)
    queryset = queryset.select_related('company')

    candidates = list(queryset)
    if not candidates:
        candidates = list(
            ManagingCompanyYearStat.objects.filter(year=stat.year)
            .exclude(company_id=stat.company_id)
            .select_related('company')[: max(limit * 3, 15)]
        )

    def score(candidate: ManagingCompanyYearStat) -> float:
        houses_score = abs((candidate.houses_quantity or 0) - houses) / max(houses, 1)
        area_score = abs((candidate.houses_area or candidate.total_area or 0) - area) / max(area, 1)
        same_district_penalty = 0 if candidate.adm_area == stat.adm_area else 1
        return round(houses_score * 0.45 + area_score * 0.45 + same_district_penalty * 0.1, 4)

    candidates.sort(key=score)
    top = candidates[:limit]
    for candidate in top:
        candidate.similarity_score = score(candidate)
    return top



def summarize_against_peers(target_stat: ManagingCompanyYearStat, peers: Iterable[ManagingCompanyYearStat]) -> dict[str, Any]:
    target_metrics = compute_metrics(target_stat)
    peer_metrics = [compute_metrics(item) for item in peers]
    if not peer_metrics:
        return {
            'company': target_metrics.__dict__,
            'peer_group_avg': {},
            'peer_group_median': {},
            'deviation_pct': {},
            'summary': 'Для выбранной организации не найдено достаточного числа сопоставимых организаций.',
        }

    metric_names = list(target_metrics.__dict__.keys())
    avg_metrics: dict[str, float] = {}
    median_metrics: dict[str, float] = {}
    deviation_pct: dict[str, float] = {}

    for name in metric_names:
        values = [getattr(item, name) for item in peer_metrics]
        avg_value = sum(values) / len(values)
        median_value = median(values)
        avg_metrics[name] = round(avg_value, 4)
        median_metrics[name] = round(median_value, 4)
        base = avg_value if avg_value else 1
        deviation_pct[name] = round(((getattr(target_metrics, name) - avg_value) / base) * 100, 2)

    worse_metrics = [name for name, value in deviation_pct.items() if value > 15]
    better_metrics = [name for name, value in deviation_pct.items() if value < -15]

    if worse_metrics:
        summary = (
            'Организация выглядит хуже средней по сопоставимой группе по следующим показателям: '
            + join_metric_labels(worse_metrics[:3])
            + '.'
        )
    elif better_metrics:
        summary = (
            'Организация выглядит лучше средней по сопоставимой группе по следующим показателям: '
            + join_metric_labels(better_metrics[:3])
            + '.'
        )
    else:
        summary = 'Организация находится близко к среднему уровню сопоставимой группы.'

    return {
        'company': target_metrics.__dict__,
        'peer_group_avg': avg_metrics,
        'peer_group_median': median_metrics,
        'deviation_pct': deviation_pct,
        'summary': summary,
    }


def build_insights(target_stat: ManagingCompanyYearStat, history: list[ManagingCompanyYearStat], peers: list[ManagingCompanyYearStat]) -> dict[str, Any]:
    metrics = compute_metrics(target_stat)
    benchmark = summarize_against_peers(target_stat, peers)
    signals: list[str] = []
    strengths: list[str] = []
    weaknesses: list[str] = []

    risk_text_map = {
        'low': 'низкий',
        'medium': 'средний',
        'high': 'высокий',
    }

    if metrics.problem_index >= 50:
        signals.append('Зафиксирован высокий индекс проблемности организации.')
    elif metrics.problem_index >= 20:
        signals.append('Зафиксирован средний индекс проблемности организации.')

    if benchmark.get('deviation_pct', {}).get('violations_per_house', 0) > 15:
        signals.append('Число нарушений на один дом выше среднего по сопоставимой группе.')
        weaknesses.append('Повышенная интенсивность нарушений.')
    else:
        strengths.append('Уровень нарушений не превышает средний по сопоставимой группе.')

    if benchmark.get('deviation_pct', {}).get('fines_per_1000_m2', 0) > 15:
        signals.append('Штрафная нагрузка на 1000 кв. м выше средней по сопоставимой группе.')
        weaknesses.append('Повышенная интенсивность штрафов.')
    else:
        strengths.append('Штрафная нагрузка не превышает среднюю по сопоставимой группе.')

    if benchmark.get('deviation_pct', {}).get('prescriptions_per_house', 0) > 15:
        weaknesses.append('Число предписаний на один дом выше среднего по сопоставимой группе.')

    if benchmark.get('deviation_pct', {}).get('protocols_per_house', 0) > 15:
        weaknesses.append('Число протоколов на один дом выше среднего по сопоставимой группе.')

    if benchmark.get('deviation_pct', {}).get('overdue_events_rate', 0) > 15:
        weaknesses.append('Доля просроченных мероприятий выше средней по сопоставимой группе.')

    if len(history) >= 2:
        previous = history[-2]
        previous_metrics = compute_metrics(previous)
        if metrics.problem_index - previous_metrics.problem_index > 10:
            signals.append(f'В {target_stat.year} году показатели ухудшились по сравнению с {previous.year} годом.')
            weaknesses.append('Наблюдается негативная динамика по сравнению с предыдущим годом.')
        elif previous_metrics.problem_index - metrics.problem_index > 10:
            strengths.append('В последнем доступном периоде показатели улучшились.')

    stability = compute_stability_index(history)
    if stability >= 75:
        strengths.append('Показатели организации относительно стабильны по годам.')
    elif stability < 50:
        weaknesses.append('Показатели организации заметно колеблются по годам.')

    risk_text = risk_text_map.get(risk_level(metrics.problem_index), risk_level(metrics.problem_index))

    summary_parts = [
        f'Организация имеет {risk_text} уровень риска.',
        benchmark['summary'],
    ]
    if weaknesses:
        summary_parts.append('Ключевые проблемные стороны: ' + ', '.join(dict.fromkeys(weaknesses[:3])) + '.')
    if strengths:
        summary_parts.append('Сильные стороны: ' + ', '.join(dict.fromkeys(strengths[:3])) + '.')

    return {
        'risk_level': risk_level(metrics.problem_index),
        'signals': list(dict.fromkeys(signals)),
        'strengths': list(dict.fromkeys(strengths)),
        'weaknesses': list(dict.fromkeys(weaknesses)),
        'stability_index': stability,
        'summary': ' '.join(summary_parts),
    }