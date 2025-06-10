from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import BookViewSet, BorrowingViewSet, PaymentViewSet, payment_success, payment_cancel

router = DefaultRouter()
router.register("books", BookViewSet, basename="book")
router.register("borrowings", BorrowingViewSet, basename="borrowing")
router.register("payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path('payment-success/', payment_success, name='payment_success'),
    path('payment-cancel/', payment_cancel, name='payment_cancel'),
    path("", include(router.urls)),
]

app_name = "library"