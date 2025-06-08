from rest_framework import serializers
from .models import Book, Borrowing


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"

class BorrowingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Borrowing
        fields = "__all__"

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