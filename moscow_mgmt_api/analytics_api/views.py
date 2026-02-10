from __future__ import annotations

from collections import defaultdict

from rest_framework.response import Response
from rest_framework.views import APIView

from companies.models import ManagingCompanyYearStat
from companies.services import compute_metrics, resolve_year


class DistrictAnalyticsView(APIView):
    def get(self, request):
        requested_year = request.query_params.get('year')
        year = resolve_year(int(requested_year) if requested_year else None)
        queryset = ManagingCompanyYearStat.objects.filter(year=year).exclude(adm_area='').select_related('company')

        groups: dict[str, list[ManagingCompanyYearStat]] = defaultdict(list)
        for item in queryset:
            groups[item.adm_area].append(item)

        result = []
        for adm_area, items in sorted(groups.items(), key=lambda entry: entry[0]):
            avg_problem_index = round(sum(compute_metrics(item).problem_index for item in items) / len(items), 2)
            avg_fines_per_1000_m2 = round(sum(compute_metrics(item).fines_per_1000_m2 for item in items) / len(items), 2)
            result.append(
                {
                    'adm_area': adm_area,
                    'companies_count': len(items),
                    'avg_final_rating': round(sum((item.final_rating or 0) for item in items) / len(items), 2),
                    'avg_total_amount_of_scores': round(sum(float(item.total_amount_of_scores or 0) for item in items) / len(items), 2),
                    'avg_violations_amount': round(sum(item.violations_amount for item in items) / len(items), 2),
                    'avg_sum_of_fine': round(sum(float(item.sum_of_fine) for item in items) / len(items), 2),
                    'avg_problem_index': avg_problem_index,
                    'avg_fines_per_1000_m2': avg_fines_per_1000_m2,
                }
            )

        return Response({'year': year, 'districts': result})


class RankingAnalyticsView(APIView):
    def get(self, request):
        requested_year = request.query_params.get('year')
        year = resolve_year(int(requested_year) if requested_year else None)
        metric = request.query_params.get('metric', 'final_rating')
        adm_area = request.query_params.get('adm_area')
        limit = int(request.query_params.get('limit', 20))
        direction = request.query_params.get('direction', 'desc')

        queryset = ManagingCompanyYearStat.objects.filter(year=year).select_related('company')
        if adm_area:
            queryset = queryset.filter(adm_area=adm_area)

        rows = []
        for stat in queryset:
            metrics = compute_metrics(stat)
            row = {
                'company_id': stat.company_id,
                'inn': stat.company.inn,
                'short_name': stat.company.short_name,
                'full_name': stat.company.full_name,
                'year': stat.year,
                'adm_area': stat.adm_area,
                'final_rating': stat.final_rating,
                'total_amount_of_scores': float(stat.total_amount_of_scores or 0),
                'problem_index': metrics.problem_index,
                'violations_per_house': metrics.violations_per_house,
                'fines_per_1000_m2': metrics.fines_per_1000_m2,
                'prescriptions_per_house': metrics.prescriptions_per_house,
            }
            rows.append(row)

        allowed_metrics = {
            'final_rating': {'reverse': True},
            'total_amount_of_scores': {'reverse': True},
            'problem_index': {'reverse': False},
            'violations_per_house': {'reverse': False},
            'fines_per_1000_m2': {'reverse': False},
            'prescriptions_per_house': {'reverse': False},
        }
        if metric not in allowed_metrics:
            metric = 'final_rating'

        reverse = allowed_metrics[metric]['reverse']
        if direction in {'asc', 'desc'}:
            reverse = direction == 'desc'

        rows.sort(key=lambda item: (item[metric] is None, item[metric]), reverse=reverse)
        return Response(
            {
                'year': year,
                'metric': metric,
                'adm_area': adm_area,
                'results': rows[:limit],
            }
        )
