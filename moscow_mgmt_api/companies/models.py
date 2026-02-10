from __future__ import annotations

from decimal import Decimal

from django.db import models


class ManagingCompany(models.Model):
    inn = models.CharField(max_length=32, unique=True, db_index=True)
    full_name = models.CharField(max_length=512)
    short_name = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['short_name', 'full_name']
        verbose_name = 'Управляющая организация'
        verbose_name_plural = 'Управляющие организации'

    def __str__(self) -> str:
        return self.short_name or self.full_name


class ManagingCompanyYearStat(models.Model):
    company = models.ForeignKey(ManagingCompany, related_name='year_stats', on_delete=models.CASCADE)
    year = models.PositiveIntegerField(db_index=True)
    adm_area = models.CharField(max_length=255, blank=True, db_index=True)
    adm_areas = models.JSONField(default=list, blank=True)

    houses_quantity = models.PositiveIntegerField(default=0)
    houses_area = models.PositiveIntegerField(default=0)
    total_area = models.PositiveIntegerField(default=0)

    final_rating = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    total_amount_of_scores = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    public_satisfaction_scores_sum = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    public_satisfaction_appeals_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    public_satisfaction_responses_score = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    public_satisfaction_coefficient_value = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    public_satisfaction_intermediate_rating = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    reliability_scores_sum = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    reliability_scores_by_standard = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    reliability_intermediate_rating = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    violation_scores_sum = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    elimination_violations_scores = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    detected_violations_scores = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    penalty_scores = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    violation_intermediate_rating = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    issued_prescriptions = models.PositiveIntegerField(default=0)
    violations_amount = models.PositiveIntegerField(default=0)
    protocols_composed = models.PositiveIntegerField(default=0)
    protocols_composed_for_failure = models.PositiveIntegerField(default=0)
    events_executed = models.PositiveIntegerField(default=0)
    events_not_executed_in_time = models.PositiveIntegerField(default=0)
    sum_of_fine = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal('0.00'))

    cancelled_contracts_amount = models.PositiveIntegerField(default=0)
    violations_punished = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['year', 'company_id']
        unique_together = ('company', 'year')
        indexes = [
            models.Index(fields=['year', 'adm_area']),
            models.Index(fields=['year', 'final_rating']),
        ]
        verbose_name = 'Статистика управляющей организации по году'
        verbose_name_plural = 'Годовая статистика управляющих организаций'

    def __str__(self) -> str:
        return f'{self.company} ({self.year})'
