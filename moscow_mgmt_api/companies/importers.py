from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, BinaryIO, Iterable

from django.core.files.uploadedfile import UploadedFile
from django.db import transaction

from companies.models import ManagingCompany, ManagingCompanyYearStat


@dataclass
class ImportResult:
    created_companies: int
    updated_companies: int
    created_stats: int
    updated_stats: int
    processed_dataset_2_records: int
    processed_dataset_3_records: int
    merged_rows: int


def import_open_data(
    dataset_2_sources: Iterable[Path | UploadedFile],
    dataset_3_sources: Iterable[Path | UploadedFile],
    *,
    clear: bool = False,
) -> ImportResult:
    dataset_2: list[dict[str, Any]] = []
    dataset_3: list[dict[str, Any]] = []

    for source in dataset_2_sources:
        dataset_2.extend(load_records(source))

    for source in dataset_3_sources:
        dataset_3.extend(load_records(source))

    if clear:
        ManagingCompanyYearStat.objects.all().delete()
        ManagingCompany.objects.all().delete()

    merged: dict[tuple[str, int], dict[str, Any]] = {}

    for row in dataset_2:
        inn = clean_inn(row.get('INN'))
        year = to_int(row.get('Year'))
        if not inn or year is None:
            continue

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

        bucket = merged[key]
        bucket['full_name'] = bucket['full_name'] or row.get('NameOfManagingOrg', '')
        bucket['issued_prescriptions'] = to_int(row.get('IssuedPrescriptions')) or 0
        bucket['violations_amount'] = to_int(row.get('ViolationsAmount')) or 0
        bucket['protocols_composed'] = to_int(row.get('ProtocolsComposed')) or 0
        bucket['protocols_composed_for_failure'] = to_int(row.get('ProtocolsComposedForFailure')) or 0
        bucket['events_executed'] = to_int(row.get('EventsExecuted')) or 0
        bucket['events_not_executed_in_time'] = to_int(row.get('EventsNotExecutedInTime')) or 0
        bucket['sum_of_fine'] = to_decimal(row.get('SumOfFine')) or Decimal('0.00')

    for row in dataset_3:
        inn = clean_inn(row.get('INN'))
        year = to_int(row.get('Year'))
        if not inn or year is None:
            continue

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

        bucket = merged[key]
        bucket['full_name'] = row.get('Name') or bucket['full_name']
        bucket['short_name'] = bucket['short_name'] or row.get('Name', '')

        adm_areas = row.get('AdmArea') or []
        if isinstance(adm_areas, str):
            adm_areas = [adm_areas]

        bucket['adm_areas'] = adm_areas
        bucket['adm_area'] = adm_areas[0] if adm_areas else ''
        bucket['houses_quantity'] = bucket.get('houses_quantity') or to_int(row.get('HousesQuantity')) or 0
        bucket['houses_area'] = bucket.get('houses_area') or to_int(row.get('HousesArea')) or 0
        bucket['final_rating'] = to_int(row.get('FinalRating'))
        bucket['total_amount_of_scores'] = to_decimal(row.get('TotalAmountOfScores'))

        public_satisfaction = first_nested(row.get('PublicSatisfactionLevel'))
        reliability = first_nested(row.get('ReliabilityLevel'))
        violation_level = first_nested(row.get('ViolationLevel'))

        bucket['public_satisfaction_scores_sum'] = to_decimal(public_satisfaction.get('ScoresSum'))
        bucket['public_satisfaction_appeals_score'] = to_decimal(public_satisfaction.get('ScoresOfAppeals'))
        bucket['public_satisfaction_responses_score'] = to_decimal(public_satisfaction.get('ScoresOfResponses'))
        bucket['public_satisfaction_coefficient_value'] = to_decimal(public_satisfaction.get('CoefficientValue'))
        bucket['public_satisfaction_intermediate_rating'] = to_decimal(public_satisfaction.get('IntermediateRatingZ1'))

        bucket['reliability_scores_sum'] = to_decimal(reliability.get('ScoresSumK3'))
        bucket['reliability_scores_by_standard'] = to_decimal(reliability.get('ScoresByStandart'))
        bucket['reliability_intermediate_rating'] = to_decimal(reliability.get('IntermediateRatingZ2'))

        bucket['violation_scores_sum'] = to_decimal(violation_level.get('ScoresSumK4'))
        bucket['elimination_violations_scores'] = to_decimal(violation_level.get('EliminationViolationsScores'))
        bucket['detected_violations_scores'] = to_decimal(violation_level.get('DetectedViolationsScores'))
        bucket['penalty_scores'] = to_decimal(violation_level.get('PenaltyScores'))
        bucket['violation_intermediate_rating'] = to_decimal(violation_level.get('IntermediateRatingZ3'))

    created_companies = 0
    updated_companies = 0
    created_stats = 0
    updated_stats = 0

    with transaction.atomic():
        for row in merged.values():
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
                    updated_companies += 1

            stat_defaults = {}
            for key, value in row.items():
                if key not in {'inn', 'year', 'full_name', 'short_name'}:
                    stat_defaults[key] = value

            stat_exists = ManagingCompanyYearStat.objects.filter(company=company, year=row['year']).exists()

            _, stat_created = ManagingCompanyYearStat.objects.update_or_create(
                company=company,
                year=row['year'],
                defaults=stat_defaults,
            )

            if stat_created:
                created_stats += 1
            elif stat_exists:
                updated_stats += 1

    return ImportResult(
        created_companies=created_companies,
        updated_companies=updated_companies,
        created_stats=created_stats,
        updated_stats=updated_stats,
        processed_dataset_2_records=len(dataset_2),
        processed_dataset_3_records=len(dataset_3),
        merged_rows=len(merged),
    )


def load_records(source: Path | UploadedFile) -> list[dict[str, Any]]:
    if isinstance(source, Path):
        if not source.exists():
            return []
        content = source.read_text(encoding='utf-8').strip()
        return parse_json_content(content)

    if isinstance(source, UploadedFile):
        content = read_uploaded_text(source)
        return parse_json_content(content)

    return []


def read_uploaded_text(uploaded_file: UploadedFile) -> str:
    uploaded_file.seek(0)
    raw = uploaded_file.read()
    if isinstance(raw, bytes):
        return raw.decode('utf-8-sig').strip()
    return str(raw).strip()


def parse_json_content(content: str) -> list[dict[str, Any]]:
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
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
        return rows

    return []


def clean_inn(value: Any) -> str:
    if value is None:
        return ''
    return str(value).strip()


def to_int(value: Any) -> int | None:
    if value in (None, ''):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def to_decimal(value: Any) -> Decimal | None:
    if value in (None, ''):
        return None
    try:
        if isinstance(value, Decimal):
            return value
        if isinstance(value, str):
            normalized = value.replace(' ', '').replace(',', '.')
            return Decimal(normalized)
        return Decimal(str(value))
    except Exception:
        return None


def first_nested(value: Any) -> dict[str, Any]:
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return first
        return {}

    if isinstance(value, dict):
        return value

    return {}   