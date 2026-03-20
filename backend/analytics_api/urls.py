from django.urls import path

from .views import DistrictAnalyticsView, RankingAnalyticsView

urlpatterns = [
    path('analytics/districts/', DistrictAnalyticsView.as_view(), name='analytics-districts'),
    path('analytics/ranking/', RankingAnalyticsView.as_view(), name='analytics-ranking'),
]
