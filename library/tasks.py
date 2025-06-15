from celery import shared_task


@shared_task
def notify_borrowings_ending_tomorrow():
    from django.utils.timezone import now, timedelta
    from .utils.telegram import send_telegram_message
    from .models import Borrowing

    tomorrow = now().date() + timedelta(days=1)
    borrowings = Borrowing.objects.filter(
        expected_return_date=tomorrow, actual_return_date__isnull=True
    )

    if not borrowings.exists():
        return

    message = f"📚 Borrowings that are due tomorrow ({tomorrow}):\n\n"

    for borrow in borrowings:
        message += (
            f'— Book: "{borrow.book.title}"\n'
            f"  User: {borrow.user.email}\n"
            f"  Borrow date: {borrow.borrow_date}\n\n"
        )

    send_telegram_message(message)
