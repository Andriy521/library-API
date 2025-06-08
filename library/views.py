from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book, Borrowing, Payment, PaymentStatus, PaymentType
from .serializers import BookSerializer, BorrowingSerializer, PaymentSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    serializer_class = BorrowingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Borrowing.objects.all()
        return Borrowing.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["POST"])
    def return_book(self, request, pk=None):
        borrowing = self.get_object()

        if borrowing.actual_return_date:
            return Response({"detail": "This borrowing is already returned."}, status=400)

        borrowing.actual_return_date = timezone.now().date()
        borrowing.book.inventory += 1
        borrowing.book.save()
        borrowing.save()

        payment_amount, fine_amount = borrowing.calculate_payment_amounts()

        # PAYMENT
        Payment.objects.create(
            borrowing=borrowing,
            status=PaymentStatus.PENDING,
            type=PaymentType.PAYMENT,
            money_to_pay=payment_amount,
            session_url="https://example.com/payment",
            session_id="fake-session-id"
        )

        # FINE
        if fine_amount > 0:
            Payment.objects.create(
                borrowing=borrowing,
                status=PaymentStatus.PENDING,
                type=PaymentType.FINE,
                money_to_pay=fine_amount,
                session_url="https://example.com/payment",
                session_id="fake-session-id"
            )

        return Response({"detail": "Book returned. Payments created."}, status=status.HTTP_200_OK)


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Payment.objects.all()
        return Payment.objects.filter(borrowing__user=user)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not queryset.exists() and not request.user.is_staff:
            from rest_framework.response import Response
            return Response({"detail": "You do not have any payment"})
        return super().list(request, *args, **kwargs)
