from rest_framework import serializers
from .models import Book, Borrowing, Payment


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"

class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = ["id", "borrow_date", "expected_return_date", "book", "user"]
        read_only_fields = ["id", "borrow_date"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")

        if request and not request.user.is_staff:
            self.fields.pop("user")

    def validate(self, attrs):
        book = attrs["book"]
        if book.inventory < 1:
            raise serializers.ValidationError("This book is currently not available.")
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")

        if not request.user.is_staff:
            validated_data["user"] = request.user

        book = validated_data["book"]
        book.inventory -= 1
        book.save()

        return Borrowing.objects.create(**validated_data)


class PaymentSerializer(serializers.ModelSerializer):
    borrowing_id = serializers.IntegerField(source="borrowing.id", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "status",
            "type",
            "borrowing_id",
            "session_url",
            "session_id",
            "money_to_pay",
        ]
        read_only_fields = fields
