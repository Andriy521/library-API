from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import stripe
from library_service.settings import STRIPE_SECRET_KEY

from .models import Book, Borrowing, Payment, PaymentStatus, PaymentType
from .serializers import BookSerializer, BorrowingSerializer, PaymentSerializer


stripe.api_key = STRIPE_SECRET_KEY


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

    @action(detail=True, methods=["POST", "GET"])
    def return_book(self, request, pk=None):
        borrowing = self.get_object()

        if borrowing.actual_return_date:
            return Response({"detail": "This borrowing is already returned."}, status=400)

        borrowing.actual_return_date = timezone.now().date()
        borrowing.book.inventory += 1
        borrowing.book.save()
        borrowing.save()

        payment_amount, fine_amount = borrowing.calculate_payment_amounts()

        def create_stripe_session(amount, payment_type):
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': f'{payment_type} for borrowing #{borrowing.id}',
                        },
                        'unit_amount': int(amount * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=request.build_absolute_uri('/payment-success/'),
                cancel_url=request.build_absolute_uri('/payment-cancel/'),
            )
            return session

        if payment_amount > 0:
            session = create_stripe_session(payment_amount, 'Payment')
            Payment.objects.create(
                borrowing=borrowing,
                status=PaymentStatus.PENDING,
                type=PaymentType.PAYMENT,
                money_to_pay=payment_amount,
                session_url=session.url,
                session_id=session.id
            )

        if fine_amount > 0:
            session = create_stripe_session(fine_amount, 'Fine')
            Payment.objects.create(
                borrowing=borrowing,
                status=PaymentStatus.PENDING,
                type=PaymentType.FINE,
                money_to_pay=fine_amount,
                session_url=session.url,
                session_id=session.id
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
