from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser
from .serializers import TelegramLoginSerializer, UserMeSerializer


class TelegramLogin(APIView):
    """
    Авторизация через Telegram WebApp.

    Принимает `telegramData`, валидирует его и возвращает JWT-токены.
    """

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = TelegramLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: CustomUser = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me(request: Request) -> Response:
    """
    Данные о текущем пользователе.
    """

    serializer = UserMeSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)