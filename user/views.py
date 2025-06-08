from rest_framework import generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import RegisterSerializer, UserSerializer, CustomTokenObtainPairSerializer
from django.contrib.auth import get_user_model


@api_view(['GET'])
def api_root(request, format=None):
    return Response({
        "register": reverse("users:register", request=request, format=format),
        "token_obtain": reverse("users:token_obtain_pair", request=request, format=format),
        "token_refresh": reverse("users:token_refresh", request=request, format=format),
        "me": reverse("users:user_me", request=request, format=format),
    })


class RegisterView(generics.CreateAPIView):
    queryset = get_user_model().objects.all()
    serializer_class = RegisterSerializer


class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
