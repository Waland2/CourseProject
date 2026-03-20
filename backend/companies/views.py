from __future__ import annotations

from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ManagingCompany, ManagingCompanyYearStat
from .serializers import (
    CompanyDetailSerializer,
    CompanyListSerializer,
    CompanySuggestionSerializer,
    CompanyYearStatHistorySerializer,
    ComparisonCompanySerializer,
    ComparisonRequestSerializer,
    InsightsSerializer,
    SimilarCompanySerializer,
)
from .services import (
    build_company_queryset,
    build_insights,
    compute_metrics,
    filter_company_queryset,
    get_latest_year,
    get_similar_stats,
    resolve_year,
    stat_for_year,
    summarize_against_peers,
    get_service_rank
)


class ManagingCompanyListView(generics.ListAPIView):
    serializer_class = CompanyListSerializer

    def get_queryset(self):
        requested_year = self.request.query_params.get('year')
        year = resolve_year(int(requested_year) if requested_year else None)
        queryset = build_company_queryset(year)
        return filter_company_queryset(queryset, self.request.query_params, year)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        requested_year = self.request.query_params.get('year')
        context['year'] = resolve_year(int(requested_year) if requested_year else None)
        return context


class ManagingCompanySuggestionsView(generics.ListAPIView):
    serializer_class = CompanySuggestionSerializer
    pagination_class = None

    def get_queryset(self):
        query = self.request.query_params.get('query', '').strip()
        requested_year = self.request.query_params.get('year')
        year = resolve_year(int(requested_year) if requested_year else None)
        queryset = build_company_queryset(year)
        queryset = queryset.filter(year_stats__year=year)
        if query:
            queryset = queryset.filter(Q(inn__icontains=query) | Q(full_name__icontains=query) | Q(short_name__icontains=query))
        return queryset.order_by('short_name', 'id')[:10]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        requested_year = self.request.query_params.get('year')
        context['year'] = resolve_year(int(requested_year) if requested_year else None)
        return context


class ManagingCompanyDetailView(generics.RetrieveAPIView):
    serializer_class = CompanyDetailSerializer
    lookup_url_kwarg = 'id'

    def get_queryset(self):
        return ManagingCompany.objects.prefetch_related('year_stats')

    def get_serializer_context(self):
        context = super().get_serializer_context()

        company = self.get_object()
        requested_year = self.request.query_params.get('year')

        if requested_year:
            year = int(requested_year)
        else:
            latest_stat = company.year_stats.order_by('-year').first()
            year = latest_stat.year if latest_stat else None

        context['year'] = year
        return context


class ManagingCompanyHistoryView(APIView):
    def get(self, request, id: int):
        company = get_object_or_404(ManagingCompany.objects.prefetch_related('year_stats'), pk=id)
        history = company.year_stats.order_by('year')
        serializer = CompanyYearStatHistorySerializer(history, many=True)
        return Response(
            {
                'company': {
                    'id': company.id,
                    'inn': company.inn,
                    'short_name': company.short_name,
                    'full_name': company.full_name,
                },
                'history': serializer.data,
            }
        )


class ManagingCompanySimilarView(APIView):
    def get(self, request, id: int):
        company = get_object_or_404(ManagingCompany.objects.prefetch_related('year_stats'), pk=id)
        requested_year = request.query_params.get('year')
        year = resolve_year(int(requested_year) if requested_year else None)
        stat = stat_for_year(company, year)
        if not stat:
            return Response({'detail': 'Нет данных по выбранной организации за указанный год.'}, status=status.HTTP_404_NOT_FOUND)

        limit = int(request.query_params.get('limit', 5))
        similar_stats = get_similar_stats(stat, limit=limit)
        serializer = SimilarCompanySerializer(similar_stats, many=True)
        return Response(
            {
                'target_company_id': company.id,
                'year': stat.year,
                'similar_companies': serializer.data,
            }
        )


class ManagingCompanyBenchmarkView(APIView):
    def get(self, request, id: int):
        company = get_object_or_404(ManagingCompany.objects.prefetch_related('year_stats'), pk=id)
        requested_year = request.query_params.get('year')
        year = resolve_year(int(requested_year) if requested_year else None)
        stat = stat_for_year(company, year)
        if not stat:
            return Response({'detail': 'Нет данных по выбранной организации за указанный год.'}, status=status.HTTP_404_NOT_FOUND)

        peers = get_similar_stats(stat, limit=int(request.query_params.get('limit', 10)))
        benchmark = summarize_against_peers(stat, peers)
        return Response(
            {
                'target_company_id': company.id,
                'year': stat.year,
                **benchmark,
            }
        )


class ManagingCompanyInsightsView(APIView):
    def get(self, request, id: int):
        company = get_object_or_404(ManagingCompany.objects.prefetch_related('year_stats'), pk=id)
        requested_year = request.query_params.get('year')
        year = resolve_year(int(requested_year) if requested_year else None)
        stat = stat_for_year(company, year)
        if not stat:
            return Response({'detail': 'Нет данных по выбранной организации за указанный год.'}, status=status.HTTP_404_NOT_FOUND)

        history = list(company.year_stats.order_by('year'))
        peers = get_similar_stats(stat, limit=int(request.query_params.get('limit', 10)))
        insights = build_insights(stat, history, peers)
        serializer = InsightsSerializer(insights)
        return Response(
            {
                'target_company_id': company.id,
                'year': stat.year,
                **serializer.data,
            }
        )


class ComparisonView(APIView):
    def post(self, request):
        request_serializer = ComparisonRequestSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)

        year = resolve_year(request_serializer.validated_data.get('year'))
        company_ids = request_serializer.validated_data['company_ids']

        stats = list(
            ManagingCompanyYearStat.objects.filter(company_id__in=company_ids, year=year)
            .select_related('company')
            .order_by('company__short_name', 'company_id')
        )
        if len(stats) < 2:
            return Response({'detail': 'Для сравнения необходимо минимум две организации с данными за выбранный год.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ComparisonCompanySerializer(stats, many=True)

        best_by_metric: dict[str, dict] = {}
        metric_names = ['problem_index', 'violations_per_house', 'fines_per_1000_m2', 'prescriptions_per_house']
        computed = [(stat, compute_metrics(stat).__dict__) for stat in stats]
        for metric_name in metric_names:
            best_stat, best_metrics = min(computed, key=lambda item: item[1][metric_name])
            best_by_metric[metric_name] = {
                'company_id': best_stat.company_id,
                'company_name': best_stat.company.short_name or best_stat.company.full_name,
                'value': best_metrics[metric_name],
            }

        stats_with_service_rank = [(stat, get_service_rank(stat)) for stat in stats]
        stats_with_service_rank = [(stat, rank) for stat, rank in stats_with_service_rank if rank is not None]

        best_rating_stat, best_rating_value = min(stats_with_service_rank, key=lambda item: item[1]) if stats_with_service_rank else (None, None)
        worst_rating_stat, worst_rating_value = max(stats_with_service_rank, key=lambda item: item[1]) if stats_with_service_rank else (None, None)

        return Response(
            {
                'year': year,
                'companies': serializer.data,
                'best_by_metric': best_by_metric,
                'best_final_rating': {
                    'company_id': best_rating_stat.company_id,
                    'company_name': best_rating_stat.company.short_name or best_rating_stat.company.full_name,
                    'value': best_rating_value,
                    'official_rating': best_rating_stat.final_rating,
                } if best_rating_stat else None,

                'lowest_final_rating': {
                    'company_id': worst_rating_stat.company_id,
                    'company_name': worst_rating_stat.company.short_name or worst_rating_stat.company.full_name,
                    'value': worst_rating_value,
                    'official_rating': worst_rating_stat.final_rating,
                } if worst_rating_stat else None,
            }
        )


class AdmAreaReferenceView(APIView):
    def get(self, request):
        requested_year = request.query_params.get('year')
        year = resolve_year(int(requested_year) if requested_year else None)
        queryset = ManagingCompanyYearStat.objects.exclude(adm_area='')
        if year is not None:
            queryset = queryset.filter(year=year)
        areas = list(queryset.values_list('adm_area', flat=True).distinct().order_by('adm_area'))
        return Response(areas)


class YearsReferenceView(APIView):
    def get(self, request):
        years = list(ManagingCompanyYearStat.objects.values_list('year', flat=True).distinct().order_by('year'))
        return Response(years)
