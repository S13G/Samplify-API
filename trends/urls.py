from django.urls import path
from .views import AnalyzeMarketTrendsView, AnalyzeRedditDataView

urlpatterns = [
    path('analyze-market-trends/', AnalyzeMarketTrendsView.as_view(), name='analyze_market_trends'),
    path('analyze-reddit-data/', AnalyzeRedditDataView.as_view(), name='analyze_reddit_data'),
]
