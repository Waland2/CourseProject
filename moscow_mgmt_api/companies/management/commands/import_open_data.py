from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from companies.models import ManagingCompany, ManagingCompanyYearStat


class Command(BaseCommand):
    help = 'Импортирует три датасета по управляющим организациям Москвы и объединяет их по INN и году.'

    def add_arguments(self, parser):
        parser.add_argument('--dataset-1', required=True, help='Путь к файлу с данными по домам/площади/расторгнутым договорам.')
        parser.add_argument('--dataset-2', required=True, help='Путь к файлу с данными по предписаниям/нарушениям/штрафам.')
        parser.add_argument('--dataset-3', required=True, help='Путь к файлу с рейтингом управляющих организаций.')
        parser.add_argument('--clear', action='store_true', help='Очистить таблицы перед импортом.')

    def handle(self, *args, **options):
        path_1 = Path(options['dataset_1'])
        path_2 = Path(options['dataset_2'])
        path_3 = Path(options['dataset_3'])

        for path in (path_1, path_2, path_3):
            if not path.exists():
                raise CommandError(f'Файл не найден: {path}')

        dataset_1 = self._load_records(path_1)
        dataset_2 = self._load_records(path_2)
        dataset_3 = self._load_records(path_3)

        if options['clear']:
            self.stdout.write(self.style.WARNING('Очистка таблиц...'))
            ManagingCompanyYearStat.objects.all().delete()
            ManagingCompany.objects.all().delete()

        merged: dict[tuple[str, int], dict[str, Any]] = {}

        def get_bucket(inn: str, year: int) -> dict[str, Any]:
            key = (inn, year)
            if key not in merged:
                merged[key] = {
                    'inn': inn,
                    'year': year,
                    'full_name': '',
                    'short_name': '',
                    'adm_area': '',
                    'adm_areas': [],
                }
            return merged[key]

        for row in dataset_1:
            inn = self._clean_inn(row.get('INN'))
            year = self._to_int(row.get('Year'))
            if not inn or year is None:
                continue
            bucket = get_bucket(inn, year)
            bucket['full_name'] = row.get('FullName') or bucket['full_name']
            bucket['short_name'] = row.get('ShortName') or bucket['short_name']
            bucket['houses_quantity'] = self._to_int(row.get('HousesNumber')) or 0
            bucket['houses_area'] = self._to_int(row.get('TotalArea')) or 0
            bucket['total_area'] = self._to_int(row.get('TotalArea')) or 0
            bucket['cancelled_contracts_amount'] = self._to_int(row.get('CancelledContractsAmount')) or 0
            bucket['violations_punished'] = self._to_int(row.get('ViolationsPunished')) or 0

        for row in dataset_2:
            inn = self._clean_inn(row.get('INN'))
            year = self._to_int(row.get('Year'))
            if not inn or year is None:
                continue
            bucket = get_bucket(inn, year)
            bucket['full_name'] = bucket['full_name'] or row.get('NameOfManagingOrg', '')
            bucket['issued_prescriptions'] = self._to_int(row.get('IssuedPrescriptions')) or 0
            bucket['violations_amount'] = self._to_int(row.get('ViolationsAmount')) or 0
            bucket['protocols_composed'] = self._to_int(row.get('ProtocolsComposed')) or 0
            bucket['protocols_composed_for_failure'] = self._to_int(row.get('ProtocolsComposedForFailure')) or 0
            bucket['events_executed'] = self._to_int(row.get('EventsExecuted')) or 0
            bucket['events_not_executed_in_time'] = self._to_int(row.get('EventsNotExecutedInTime')) or 0
            bucket['sum_of_fine'] = self._to_decimal(row.get('SumOfFine'))

        for row in dataset_3:
            inn = self._clean_inn(row.get('INN'))
            year = self._to_int(row.get('Year'))
            if not inn or year is None:
                continue
            bucket = get_bucket(inn, year)
            bucket['full_name'] = row.get('Name') or bucket['full_name']
            bucket['short_name'] = bucket['short_name'] or row.get('Name', '')
            adm_areas = row.get('AdmArea') or []
            if isinstance(adm_areas, str):
                adm_areas = [adm_areas]
            bucket['adm_areas'] = adm_areas
            bucket['adm_area'] = adm_areas[0] if adm_areas else ''
            bucket['houses_quantity'] = bucket.get('houses_quantity') or self._to_int(row.get('HousesQuantity')) or 0
            bucket['houses_area'] = bucket.get('houses_area') or self._to_int(row.get('HousesArea')) or 0
            bucket['final_rating'] = self._to_int(row.get('FinalRating'))
            bucket['total_amount_of_scores'] = self._to_decimal(row.get('TotalAmountOfScores'))

            public_satisfaction = self._first_nested(row.get('PublicSatisfactionLevel'))
            reliability = self._first_nested(row.get('ReliabilityLevel'))
            violation_level = self._first_nested(row.get('ViolationLevel'))

            bucket['public_satisfaction_scores_sum'] = self._to_decimal(public_satisfaction.get('ScoresSum'))
            bucket['public_satisfaction_appeals_score'] = self._to_decimal(public_satisfaction.get('ScoresOfAppeals'))
            bucket['public_satisfaction_responses_score'] = self._to_decimal(public_satisfaction.get('ScoresOfResponses'))
            bucket['public_satisfaction_coefficient_value'] = self._to_decimal(public_satisfaction.get('CoefficientValue'))
            bucket['public_satisfaction_intermediate_rating'] = self._to_decimal(public_satisfaction.get('IntermediateRatingZ1'))

            bucket['reliability_scores_sum'] = self._to_decimal(reliability.get('ScoresSumK3'))
            bucket['reliability_scores_by_standard'] = self._to_decimal(reliability.get('ScoresByStandart'))
            bucket['reliability_intermediate_rating'] = self._to_decimal(reliability.get('IntermediateRatingZ2'))

            bucket['violation_scores_sum'] = self._to_decimal(violation_level.get('ScoresSumK4'))
            bucket['elimination_violations_scores'] = self._to_decimal(violation_level.get('EliminationViolationsScores'))
            bucket['detected_violations_scores'] = self._to_decimal(violation_level.get('DetectedViolationsScores'))
            bucket['penalty_scores'] = self._to_decimal(violation_level.get('PenaltyScores'))
            bucket['violation_intermediate_rating'] = self._to_decimal(violation_level.get('IntermediateRatingZ3'))

        created_companies = 0
        created_stats = 0

        with transaction.atomic():
            for (_, _), row in merged.items():
                company, company_created = ManagingCompany.objects.get_or_create(
                    inn=row['inn'],
                    defaults={
                        'full_name': row.get('full_name') or row.get('short_name') or row['inn'],
                        'short_name': row.get('short_name') or row.get('full_name') or row['inn'],
                    },
                )
                if company_created:
                    created_companies += 1
                else:
                    updates = []
                    if row.get('full_name') and company.full_name != row['full_name']:
                        company.full_name = row['full_name']
                        updates.append('full_name')
                    if row.get('short_name') and company.short_name != row['short_name']:
                        company.short_name = row['short_name']
                        updates.append('short_name')
                    if updates:
                        company.save(update_fields=updates + ['updated_at'])

                stat_defaults = {k: v for k, v in row.items() if k not in {'inn', 'year', 'full_name', 'short_name'}}
                _, stat_created = ManagingCompanyYearStat.objects.update_or_create(
                    company=company,
                    year=row['year'],
                    defaults=stat_defaults,
                )
                if stat_created:
                    created_stats += 1

        self.stdout.write(self.style.SUCCESS(f'Импорт завершен. Компаний создано: {created_companies}, годовых записей создано: {created_stats}.'))

    @staticmethod
    def _load_records(path: Path) -> list[dict[str, Any]]:
        content = path.read_text(encoding='utf-8').strip()
        if not content:
            return []
        try:
            payload = json.loads(content)
            if isinstance(payload, list):
                return [item for item in payload if isinstance(item, dict)]
            if isinstance(payload, dict):
                if 'data' in payload and isinstance(payload['data'], list):
                    return [item for item in payload['data'] if isinstance(item, dict)]
                return [payload]
        except json.JSONDecodeError:
            rows = []
            for line in content.splitlines():
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
            return rows
        return []

    @staticmethod
    def _clean_inn(value: Any) -> str:
        if value is None:
            return ''
        return str(value).strip()

    @staticmethod
    def _to_int(value: Any) -> int | None:
        if value in (None, ''):
            return None
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_decimal(value: Any):
        if value in (None, ''):
            return None
        try:
            return value if isinstance(value, str) else float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _first_nested(value: Any) -> dict[str, Any]:
        if isinstance(value, list) and value:
            first = value[0]
            return first if isinstance(first, dict) else {}
        if isinstance(value, dict):
            return value
        return {}
