from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import CategoryViewSet, TransactionViewSet, BudgetViewSet, SummaryView, TrendsView

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('transactions', TransactionViewSet, basename='transaction')
router.register('budgets', BudgetViewSet, basename='budget')

urlpatterns = router.urls + [
    path('summary/', SummaryView.as_view(), name='summary'),
    path('trends/', TrendsView.as_view(), name='trends'),
]