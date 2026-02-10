from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from statistics import median
from typing import Any, Iterable

from django.db import models
from django.db.models import Max, Prefetch, QuerySet

from .models import ManagingCompany, ManagingCompanyYearStat

ZERO = Decimal('0')


@dataclass
class MetricBundle:
    violations_per_house: float
    fines_per_house: float
    fines_per_1000_m2: float
    prescriptions_per_house: float
    protocols_per_house: float
    cancelled_contracts_per_100_houses: float
    punished_violations_per_house: float
    overdue_events_rate: float
    problem_index: float



def decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)



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
    cancelled_contracts_per_100_houses = round(safe_div(stat.cancelled_contracts_amount, houses) * 100, 4) if houses else 0.0
    punished_violations_per_house = safe_div(stat.violations_punished, houses)
    overdue_events_rate = round(safe_div(stat.events_not_executed_in_time, total_events) * 100, 4) if total_events else 0.0

    problem_index = min(
        100.0,
        round(
            violations_per_house * 18
            + prescriptions_per_house * 14
            + protocols_per_house * 10
            + fines_per_1000_m2 * 0.12
            + cancelled_contracts_per_100_houses * 0.6
            + overdue_events_rate * 0.3,
            2,
        ),
    )

    return MetricBundle(
        violations_per_house=violations_per_house,
        fines_per_house=fines_per_house,
        fines_per_1000_m2=fines_per_1000_m2,
        prescriptions_per_house=prescriptions_per_house,
        protocols_per_house=protocols_per_house,
        cancelled_contracts_per_100_houses=cancelled_contracts_per_100_houses,
        punished_violations_per_house=punished_violations_per_house,
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

    final_rating = params.get('final_rating')
    if final_rating not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__final_rating=int(final_rating))

    final_rating_min = params.get('final_rating_min')
    if final_rating_min not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__final_rating__gte=int(final_rating_min))

    final_rating_max = params.get('final_rating_max')
    if final_rating_max not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__final_rating__lte=int(final_rating_max))

    scores_min = params.get('scores_min')
    if scores_min not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__total_amount_of_scores__gte=float(scores_min))

    scores_max = params.get('scores_max')
    if scores_max not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__total_amount_of_scores__lte=float(scores_max))

    houses_min = params.get('houses_min')
    if houses_min not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__houses_quantity__gte=houses_min)

    houses_max = params.get('houses_max')
    if houses_max not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__houses_quantity__lte=houses_max)

    area_min = params.get('area_min')
    if area_min not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__houses_area__gte=area_min)

    area_max = params.get('area_max')
    if area_max not in (None, ''):
        queryset = queryset.filter(year_stats__year=year, year_stats__houses_area__lte=area_max)

    ordering = params.get('ordering')
    ordering_map = {
        'name': 'short_name',
        '-name': '-short_name',
        'final_rating': 'year_stats__final_rating',
        '-final_rating': '-year_stats__final_rating',
        'houses_quantity': 'year_stats__houses_quantity',
        '-houses_quantity': '-year_stats__houses_quantity',
        'houses_area': 'year_stats__houses_area',
        '-houses_area': '-year_stats__houses_area',
        'scores': 'year_stats__total_amount_of_scores',
        '-scores': '-year_stats__total_amount_of_scores',
    }
    if ordering in ordering_map:
        queryset = queryset.order_by(ordering_map[ordering], 'id')
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

    worse_metrics = [name for name, value in deviation_pct.items() if value > 15 and name != 'punished_violations_per_house']
    better_metrics = [name for name, value in deviation_pct.items() if value < -15 and name != 'punished_violations_per_house']

    if worse_metrics:
        summary = 'Организация уступает средней по сопоставимой группе по следующим метрикам: ' + ', '.join(worse_metrics[:3]) + '.'
    elif better_metrics:
        summary = 'Организация выглядит лучше средней по сопоставимой группе по следующим метрикам: ' + ', '.join(better_metrics[:3]) + '.'
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

    if metrics.problem_index >= 50:
        signals.append('Высокий интегральный индекс проблемности организации.')
    elif metrics.problem_index >= 20:
        signals.append('Обнаружен средний уровень проблемности организации.')

    if benchmark.get('deviation_pct', {}).get('violations_per_house', 0) > 15:
        signals.append('Число нарушений на один дом выше среднего по сопоставимой группе.')
        weaknesses.append('Повышенная интенсивность нарушений.')
    else:
        strengths.append('Уровень нарушений не превышает средний по сопоставимой группе.')

    if benchmark.get('deviation_pct', {}).get('fines_per_1000_m2', 0) > 15:
        signals.append('Сумма штрафов на 1000 кв. м выше среднего по сопоставимой группе.')
        weaknesses.append('Повышенная интенсивность штрафов.')
    else:
        strengths.append('Штрафная нагрузка не превышает среднюю по сопоставимой группе.')

    if len(history) >= 2:
        previous = history[-2]
        previous_metrics = compute_metrics(previous)
        if metrics.problem_index - previous_metrics.problem_index > 10:
            signals.append(f'За {target_stat.year} год наблюдается ухудшение интегральных показателей относительно {previous.year} года.')
            weaknesses.append('Негативная динамика в последнем доступном периоде.')
        elif previous_metrics.problem_index - metrics.problem_index > 10:
            strengths.append('В последнем доступном периоде показатели улучшились.')

        if previous.final_rating is not None and target_stat.final_rating is not None and target_stat.final_rating > previous.final_rating:
            signals.append('Итоговый рейтинг стал хуже по сравнению с предыдущим годом.')

    stability = compute_stability_index(history)
    if stability >= 75:
        strengths.append('Показатели организации относительно стабильны по годам.')
    elif stability < 50:
        weaknesses.append('Показатели организации заметно колеблются по годам.')

    summary_parts = [
        f"Организация имеет {risk_level(metrics.problem_index)} уровень риска.",
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
