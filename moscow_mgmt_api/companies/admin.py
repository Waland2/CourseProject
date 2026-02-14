from __future__ import annotations

from django.contrib import admin, messages
from django.http import HttpRequest, HttpResponse
from django.template.response import TemplateResponse
from django.urls import path, reverse

from .forms import AdminOpenDataImportForm
from .importers import import_open_data
from .models import ManagingCompany, ManagingCompanyYearStat


@admin.register(ManagingCompany)
class ManagingCompanyAdmin(admin.ModelAdmin):
    list_display = ('id', 'inn', 'short_name', 'full_name')
    search_fields = ('inn', 'short_name', 'full_name')


@admin.register(ManagingCompanyYearStat)
class ManagingCompanyYearStatAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'year', 'adm_area', 'final_rating', 'houses_quantity', 'houses_area')
    list_filter = ('year', 'adm_area', 'final_rating')
    search_fields = ('company__inn', 'company__short_name', 'company__full_name')
    change_list_template = 'admin/companies/managingcompanyyearstat/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'import-open-data/',
                self.admin_site.admin_view(self.import_open_data_view),
                name='companies_managingcompanyyearstat_import_open_data',
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request: HttpRequest, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_open_data_url'] = reverse(
            'admin:companies_managingcompanyyearstat_import_open_data'
        )
        return super().changelist_view(request, extra_context=extra_context)

    def import_open_data_view(self, request: HttpRequest) -> HttpResponse:
        if request.method == 'POST':
            form = AdminOpenDataImportForm(request.POST, request.FILES)
            if form.is_valid():
                dataset_2_files = form.cleaned_data['dataset_2']
                dataset_3_files = form.cleaned_data['dataset_3']
                clear = form.cleaned_data['clear']

                try:
                    result = import_open_data(
                        dataset_2_sources=dataset_2_files,
                        dataset_3_sources=dataset_3_files,
                        clear=clear,
                    )
                except Exception as exc:
                    self.message_user(
                        request,
                        f'Ошибка импорта: {exc}',
                        level=messages.ERROR,
                    )
                else:
                    self.message_user(
                        request,
                        (
                            'Импорт завершён. '
                            f'Создано компаний: {result.created_companies}, '
                            f'обновлено компаний: {result.updated_companies}, '
                            f'создано записей статистики: {result.created_stats}, '
                            f'обновлено записей статистики: {result.updated_stats}, '
                            f'обработано записей dataset-2: {result.processed_dataset_2_records}, '
                            f'обработано записей dataset-3: {result.processed_dataset_3_records}, '
                            f'объединено строк по ключу (INN, year): {result.merged_rows}.'
                        ),
                        level=messages.SUCCESS,
                    )
            else:
                self.message_user(
                    request,
                    'Проверьте форму импорта.',
                    level=messages.ERROR,
                )
        else:
            form = AdminOpenDataImportForm()

        context = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': 'Импорт открытых данных',
            'form': form,
            'has_view_permission': self.has_view_permission(request),
            'has_change_permission': self.has_change_permission(request),
            'has_add_permission': self.has_add_permission(request),
            'has_delete_permission': self.has_delete_permission(request),
        }
        return TemplateResponse(request, 'admin/companies/import_open_data.html', context)