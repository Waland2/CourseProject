from django.contrib import admin

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
