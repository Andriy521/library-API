from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import stripe
from library_service.settings import STRIPE_SECRET_KEY

from .models import Book, Borrowing, Payment, PaymentStatus, PaymentType
from .serializers import BookSerializer, BorrowingSerializer, PaymentSerializer
from .utils.telegram import send_telegram_message

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
        borrowing = serializer.save(user=self.request.user)

        message = (
            f"📚 New Borrowing Created:\n"
            f"User: {borrowing.user.email}\n"
            f"Book: {borrowing.book.title}\n"
            f"Borrow date: {borrowing.borrow_date}\n"
            f"Expected return: {borrowing.expected_return_date}"
        )
        send_telegram_message(message)

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
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"{payment_type} for borrowing #{borrowing.id}",
                        },
                        "unit_amount": int(amount * 100),
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url = request.build_absolute_uri(
                    reverse("payment_success")
                ) + "?session_id={CHECKOUT_SESSION_ID}",
                cancel_url = request.build_absolute_uri(
                    reverse("payment-cancel")
                ),
            )
            return session

        if payment_amount > 0:
            session = create_stripe_session(payment_amount, "Payment")
            Payment.objects.create(
                borrowing=borrowing,
                status=PaymentStatus.PENDING,
                type=PaymentType.PAYMENT,
                money_to_pay=payment_amount,
                session_url=session.url,
                session_id=session.id
            )

        if fine_amount > 0:
            session = create_stripe_session(fine_amount, "Fine")
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

def payment_success(request):
    session_id = request.GET.get("session_id")

    if not session_id:
        return HttpResponse("Missing session_id", status=400)

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as e:
        return HttpResponse(f"Stripe error: {str(e)}", status=400)

    try:
        payment = Payment.objects.get(session_id=session.id)
    except Payment.DoesNotExist:
        return HttpResponse("Payment not found.", status=404)

    if session.payment_status == "paid" and payment.status != PaymentStatus.PAID:
        payment.status = PaymentStatus.PAID
        payment.save()

    return HttpResponse("✅ Payment confirmed successfully!")

def payment_cancel(request):
    session_id = request.GET.get("session_id")

    if not session_id:
        return HttpResponse("Missing session_id", status=400)

    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError as e:
        return HttpResponse(f"Stripe error: {str(e)}", status=400)

    payment_exists = Payment.objects.filter(session_id=session_id).exists()

    if payment_exists:
        return HttpResponse("❌ Payment was cancelled. You can try again.")

    return HttpResponse("⚠️ Payment session not found. Maybe it was never created.")