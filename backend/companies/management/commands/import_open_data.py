from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from companies.importers import import_open_data


class Command(BaseCommand):
    help = 'Импортирует датасеты по управляющим организациям Москвы и объединяет их по INN и году.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dataset-2',
            required=True,
            nargs='+',
        )
        parser.add_argument(
            '--dataset-3',
            required=True,
            nargs='+',
        )
        parser.add_argument('--clear', action='store_true')

    def handle(self, *args, **options):
        path_list_2 = [Path(path) for path in options['dataset_2']]
        path_list_3 = [Path(path) for path in options['dataset_3']]

        for path in path_list_2 + path_list_3:
            if not path.exists():
                raise CommandError(f'Файл не найден: {path}')

        result = import_open_data(
            dataset_2_sources=path_list_2,
            dataset_3_sources=path_list_3,
            clear=options['clear'],
        )

        self.stdout.write(
            self.style.SUCCESS(
                'Импорт завершен. '
                f'Компаний создано: {result.created_companies}, '
                f'компаний обновлено: {result.updated_companies}, '
                f'годовых записей создано: {result.created_stats}, '
                f'годовых записей обновлено: {result.updated_stats}, '
                f'обработано dataset-2 записей: {result.processed_dataset_2_records}, '
                f'обработано dataset-3 записей: {result.processed_dataset_3_records}, '
                f'объединено строк: {result.merged_rows}.'
            )
        )