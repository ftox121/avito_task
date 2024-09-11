from django.urls import path
from .serializers import PingView
from .views import TenderListView, TenderCreateView, UserTenderListView, TenderUpdateView, TenderRollbackView, \
    BidCreateView, UserBidsListView, TenderBidsListView, BidUpdateView, BidRollbackView, BidReviewsView

urlpatterns = [
    path('ping/', PingView.as_view(), name='ping'),
    path('tenders/', TenderListView.as_view(), name='tender-list'),
    path('tenders/new/', TenderCreateView.as_view(), name='tender-create'),
    path('tenders/my/', UserTenderListView.as_view(), name='user-tenders-list'),
    path('tenders/<uuid:pk>/edit/', TenderUpdateView.as_view(), name='tender-edit'),
    path('tenders/<uuid:tenderId>/rollback/<int:version>/', TenderRollbackView.as_view(), name='tender-rollback'),
    path('bids/new/', BidCreateView.as_view(), name='bid-create'),
    path('bids/my/', UserBidsListView.as_view(), name='user-bids-list'),
    path('bids/<uuid:tenderId>/list/', TenderBidsListView.as_view(), name='tender-bids-list'),
    path('bids/<uuid:bidId>/edit/', BidUpdateView.as_view(), name='bid-update'),
    path('bids/<uuid:bidId>/rollback/<int:version>/', BidRollbackView.as_view(), name='bid-rollback'),
    path('bids/<uuid:tenderId>/reviews/', BidReviewsView.as_view(), name='bid-reviews'),
]