from __future__ import annotations

from rest_framework import serializers

from .models import ManagingCompany, ManagingCompanyYearStat
from .services import (
    build_insights,
    compute_metrics,
    compute_stability_index,
    get_service_rank,
    risk_level,
    stat_for_year,
)

class MetricBundleSerializer(serializers.Serializer):
    violations_per_house = serializers.FloatField()
    fines_per_house = serializers.FloatField()
    fines_per_1000_m2 = serializers.FloatField()
    prescriptions_per_house = serializers.FloatField()
    protocols_per_house = serializers.FloatField()
    overdue_events_rate = serializers.FloatField()
    problem_index = serializers.FloatField()


class CompanySuggestionSerializer(serializers.ModelSerializer):
    adm_area = serializers.SerializerMethodField()

    class Meta:
        model = ManagingCompany
        fields = ('id', 'inn', 'short_name', 'full_name', 'adm_area')

    def get_adm_area(self, obj: ManagingCompany) -> str | None:
        year = self.context.get('year')
        stat = stat_for_year(obj, year)
        return stat.adm_area if stat else None


class CompanyListSerializer(serializers.ModelSerializer):
    year = serializers.SerializerMethodField()
    adm_area = serializers.SerializerMethodField()
    houses_quantity = serializers.SerializerMethodField()
    houses_area = serializers.SerializerMethodField()
    final_rating = serializers.SerializerMethodField()
    official_rating = serializers.SerializerMethodField()
    total_amount_of_scores = serializers.SerializerMethodField()
    risk_level = serializers.SerializerMethodField()
    problem_index = serializers.SerializerMethodField()

    class Meta:
        model = ManagingCompany
        fields = (
            'id',
            'inn',
            'short_name',
            'full_name',
            'year',
            'adm_area',
            'houses_quantity',
            'houses_area',
            'final_rating',
            'official_rating',
            'total_amount_of_scores',
            'problem_index',
            'risk_level',
        )

    def _get_stat(self, obj: ManagingCompany) -> ManagingCompanyYearStat | None:
        return stat_for_year(obj, self.context.get('year'))

    def get_year(self, obj: ManagingCompany) -> int | None:
        stat = self._get_stat(obj)
        return stat.year if stat else None

    def get_adm_area(self, obj: ManagingCompany) -> str | None:
        stat = self._get_stat(obj)
        return stat.adm_area if stat else None

    def get_houses_quantity(self, obj: ManagingCompany) -> int:
        stat = self._get_stat(obj)
        return stat.houses_quantity if stat else 0

    def get_houses_area(self, obj: ManagingCompany) -> int:
        stat = self._get_stat(obj)
        return stat.houses_area if stat else 0

    def get_final_rating(self, obj: ManagingCompany) -> int | None:
        stat = self._get_stat(obj)
        return get_service_rank(stat)

    def get_official_rating(self, obj: ManagingCompany) -> int | None:
        stat = self._get_stat(obj)
        return stat.final_rating if stat else None

    def get_total_amount_of_scores(self, obj: ManagingCompany) -> float | None:
        stat = self._get_stat(obj)
        return float(stat.total_amount_of_scores) if stat and stat.total_amount_of_scores is not None else None

    def get_problem_index(self, obj: ManagingCompany) -> float | None:
        stat = self._get_stat(obj)
        return compute_metrics(stat).problem_index if stat else None

    def get_risk_level(self, obj: ManagingCompany) -> str | None:
        stat = self._get_stat(obj)
        if not stat:
            return None
        return risk_level(compute_metrics(stat).problem_index)


class CompanyYearStatHistorySerializer(serializers.ModelSerializer):
    final_rating = serializers.SerializerMethodField()
    official_rating = serializers.SerializerMethodField()
    metrics = serializers.SerializerMethodField()

    class Meta:
        model = ManagingCompanyYearStat
        fields = (
            'year',
            'adm_area',
            'houses_quantity',
            'houses_area',
            'final_rating',
            'official_rating',
            'total_amount_of_scores',
            'issued_prescriptions',
            'violations_amount',
            'protocols_composed',
            'protocols_composed_for_failure',
            'events_executed',
            'events_not_executed_in_time',
            'sum_of_fine',
            'cancelled_contracts_amount',
            'violations_punished',
            'metrics',
        )

    def get_final_rating(self, obj: ManagingCompanyYearStat) -> int | None:
        return get_service_rank(obj)

    def get_official_rating(self, obj: ManagingCompanyYearStat) -> int | None:
        return obj.final_rating

    def get_metrics(self, obj: ManagingCompanyYearStat) -> dict:
        return compute_metrics(obj).__dict__


class CompanyDetailSerializer(serializers.ModelSerializer):
    year = serializers.SerializerMethodField()
    adm_area = serializers.SerializerMethodField()
    adm_areas = serializers.SerializerMethodField()
    selected_year_data = serializers.SerializerMethodField()
    metrics = serializers.SerializerMethodField()
    risk_level = serializers.SerializerMethodField()
    stability_index = serializers.SerializerMethodField()

    class Meta:
        model = ManagingCompany
        fields = (
            'id',
            'inn',
            'short_name',
            'full_name',
            'year',
            'adm_area',
            'adm_areas',
            'selected_year_data',
            'metrics',
            'risk_level',
            'stability_index',
        )

    def _get_selected_stat(self, obj: ManagingCompany) -> ManagingCompanyYearStat | None:
        return stat_for_year(obj, self.context.get('year'))

    def get_year(self, obj: ManagingCompany) -> int | None:
        stat = self._get_selected_stat(obj)
        return stat.year if stat else None

    def get_adm_area(self, obj: ManagingCompany) -> str | None:
        stat = self._get_selected_stat(obj)
        return stat.adm_area if stat else None

    def get_adm_areas(self, obj: ManagingCompany) -> list[str]:
        stat = self._get_selected_stat(obj)
        return stat.adm_areas if stat else []

    def get_selected_year_data(self, obj: ManagingCompany) -> dict | None:
        stat = self._get_selected_stat(obj)
        if not stat:
            return None
        return {
            'houses_quantity': stat.houses_quantity,
            'houses_area': stat.houses_area,
            'total_area': stat.total_area,
            'final_rating': get_service_rank(stat),
            'official_rating': stat.final_rating,
            'total_amount_of_scores': float(stat.total_amount_of_scores) if stat.total_amount_of_scores is not None else None,
            'public_satisfaction': {
                'scores_sum': float(stat.public_satisfaction_scores_sum) if stat.public_satisfaction_scores_sum is not None else None,
                'appeals_score': float(stat.public_satisfaction_appeals_score) if stat.public_satisfaction_appeals_score is not None else None,
                'responses_score': float(stat.public_satisfaction_responses_score) if stat.public_satisfaction_responses_score is not None else None,
                'coefficient_value': float(stat.public_satisfaction_coefficient_value) if stat.public_satisfaction_coefficient_value is not None else None,
                'intermediate_rating': float(stat.public_satisfaction_intermediate_rating) if stat.public_satisfaction_intermediate_rating is not None else None,
            },
            'reliability': {
                'scores_sum': float(stat.reliability_scores_sum) if stat.reliability_scores_sum is not None else None,
                'scores_by_standard': float(stat.reliability_scores_by_standard) if stat.reliability_scores_by_standard is not None else None,
                'intermediate_rating': float(stat.reliability_intermediate_rating) if stat.reliability_intermediate_rating is not None else None,
            },
            'violations': {
                'issued_prescriptions': stat.issued_prescriptions,
                'violations_amount': stat.violations_amount,
                'protocols_composed': stat.protocols_composed,
                'protocols_composed_for_failure': stat.protocols_composed_for_failure,
                'events_executed': stat.events_executed,
                'events_not_executed_in_time': stat.events_not_executed_in_time,
                'sum_of_fine': float(stat.sum_of_fine),
                'cancelled_contracts_amount': stat.cancelled_contracts_amount,
                'violations_punished': stat.violations_punished,
                'violation_scores_sum': float(stat.violation_scores_sum) if stat.violation_scores_sum is not None else None,
                'elimination_violations_scores': float(stat.elimination_violations_scores) if stat.elimination_violations_scores is not None else None,
                'detected_violations_scores': float(stat.detected_violations_scores) if stat.detected_violations_scores is not None else None,
                'penalty_scores': float(stat.penalty_scores) if stat.penalty_scores is not None else None,
                'intermediate_rating': float(stat.violation_intermediate_rating) if stat.violation_intermediate_rating is not None else None,
            },
        }

    def get_metrics(self, obj: ManagingCompany) -> dict | None:
        stat = self._get_selected_stat(obj)
        return compute_metrics(stat).__dict__ if stat else None

    def get_risk_level(self, obj: ManagingCompany) -> str | None:
        stat = self._get_selected_stat(obj)
        if not stat:
            return None
        return risk_level(compute_metrics(stat).problem_index)

    def get_stability_index(self, obj: ManagingCompany) -> float:
        history = list(obj.year_stats.order_by('year'))
        return compute_stability_index(history)


class SimilarCompanySerializer(serializers.ModelSerializer):
    similarity_score = serializers.FloatField(read_only=True)
    company_id = serializers.IntegerField(source='company.id', read_only=True)
    inn = serializers.CharField(source='company.inn', read_only=True)
    short_name = serializers.CharField(source='company.short_name', read_only=True)
    full_name = serializers.CharField(source='company.full_name', read_only=True)
    final_rating = serializers.SerializerMethodField()
    official_rating = serializers.SerializerMethodField()
    metrics = serializers.SerializerMethodField()

    class Meta:
        model = ManagingCompanyYearStat
        fields = (
            'company_id',
            'inn',
            'short_name',
            'full_name',
            'year',
            'adm_area',
            'houses_quantity',
            'houses_area',
            'final_rating',
            'official_rating',
            'similarity_score',
            'metrics',
        )

    def get_final_rating(self, obj: ManagingCompanyYearStat) -> int | None:
        return get_service_rank(obj)

    def get_official_rating(self, obj: ManagingCompanyYearStat) -> int | None:
        return obj.final_rating

    def get_metrics(self, obj: ManagingCompanyYearStat) -> dict:
        return compute_metrics(obj).__dict__


class ComparisonRequestSerializer(serializers.Serializer):
    company_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        min_length=2,
        max_length=5,
    )
    year = serializers.IntegerField(required=False)


class ComparisonCompanySerializer(serializers.ModelSerializer):
    metrics = serializers.SerializerMethodField()
    company_id = serializers.IntegerField(source='company.id')
    inn = serializers.CharField(source='company.inn')
    short_name = serializers.CharField(source='company.short_name')
    full_name = serializers.CharField(source='company.full_name')
    final_rating = serializers.SerializerMethodField()
    official_rating = serializers.SerializerMethodField()

    class Meta:
        model = ManagingCompanyYearStat
        fields = (
            'company_id',
            'inn',
            'short_name',
            'full_name',
            'year',
            'adm_area',
            'houses_quantity',
            'houses_area',
            'final_rating',
            'official_rating',
            'total_amount_of_scores',
            'issued_prescriptions',
            'violations_amount',
            'protocols_composed',
            'sum_of_fine',
            'cancelled_contracts_amount',
            'violations_punished',
            'metrics',
        )

    def get_final_rating(self, obj: ManagingCompanyYearStat) -> int | None:
        return get_service_rank(obj)

    def get_official_rating(self, obj: ManagingCompanyYearStat) -> int | None:
        return obj.final_rating

    def get_metrics(self, obj: ManagingCompanyYearStat) -> dict:
        return compute_metrics(obj).__dict__


class InsightsSerializer(serializers.Serializer):
    risk_level = serializers.CharField()
    signals = serializers.ListField(child=serializers.CharField())
    strengths = serializers.ListField(child=serializers.CharField())
    weaknesses = serializers.ListField(child=serializers.CharField())
    stability_index = serializers.FloatField()
    summary = serializers.CharField()
