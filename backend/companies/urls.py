from django.urls import path

from .views import (
    AdmAreaReferenceView,
    ComparisonView,
    ManagingCompanyBenchmarkView,
    ManagingCompanyDetailView,
    ManagingCompanyHistoryView,
    ManagingCompanyInsightsView,
    ManagingCompanyListView,
    ManagingCompanySimilarView,
    ManagingCompanySuggestionsView,
    YearsReferenceView,
)

urlpatterns = [
    path('managing-companies/', ManagingCompanyListView.as_view(), name='managing-company-list'),
    path('managing-companies/suggestions/', ManagingCompanySuggestionsView.as_view(), name='managing-company-suggestions'),
    path('managing-companies/<int:id>/', ManagingCompanyDetailView.as_view(), name='managing-company-detail'),
    path('managing-companies/<int:id>/history/', ManagingCompanyHistoryView.as_view(), name='managing-company-history'),
    path('managing-companies/<int:id>/similar/', ManagingCompanySimilarView.as_view(), name='managing-company-similar'),
    path('managing-companies/<int:id>/benchmark/', ManagingCompanyBenchmarkView.as_view(), name='managing-company-benchmark'),
    path('managing-companies/<int:id>/insights/', ManagingCompanyInsightsView.as_view(), name='managing-company-insights'),
    path('comparisons/', ComparisonView.as_view(), name='comparison-create'),
    path('reference/adm-areas/', AdmAreaReferenceView.as_view(), name='reference-adm-areas'),
    path('reference/years/', YearsReferenceView.as_view(), name='reference-years'),
]
