from decimal import Decimal
from django.db import models
from user.models import User


class CoverType(models.TextChoices):
    HARD = "HARD", "Hard"
    SOFT = "SOFT", "Soft"


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PAID = "PAID", "Paid"


class PaymentType(models.TextChoices):
    PAYMENT = "PAYMENT", "Payment"
    FINE = "FINE", "Fine"


class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    cover = models.CharField(
        max_length=4,
        choices=CoverType.choices,
        default=CoverType.SOFT,
    )
    inventory = models.PositiveIntegerField(default=0)
    daily_fee = models.DecimalField(max_digits=10, decimal_places=2)


class Borrowing(models.Model):
    borrow_date = models.DateField(auto_now_add=True)
    expected_return_date = models.DateField()
    actual_return_date = models.DateField(null=True, blank=True)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.email} - {self.book.title}"

    def calculate_payment_amounts(self):
        """Повертає кортеж (payment_amount, fine_amount)"""
        days_borrowed = (self.expected_return_date - self.borrow_date).days
        payment_amount = Decimal(days_borrowed * self.book.daily_fee)

        fine_amount = Decimal(0)
        if (
            self.actual_return_date
            and self.actual_return_date > self.expected_return_date
        ):
            late_days = (self.actual_return_date - self.expected_return_date).days
            fine_amount = Decimal(late_days * self.book.daily_fee * 2)

        return payment_amount, fine_amount


class Payment(models.Model):
    status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )
    type = models.CharField(max_length=10, choices=PaymentType.choices)
    borrowing = models.ForeignKey(
        Borrowing, on_delete=models.CASCADE, related_name="payments"
    )
    session_url = models.URLField(max_length=1000, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    money_to_pay = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"Payment for Borrowing #{self.borrowing.id} - {self.status}"
