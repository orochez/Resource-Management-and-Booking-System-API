
from django.contrib.auth import get_user_model

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .permissions import IsAdminRole
from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    CustomTokenObtainPairSerializer,
    AdminUserSerializer,
)


User = get_user_model()


# ==========================================
# REGISTER
# ==========================================

class RegisterView(generics.CreateAPIView):

    queryset = User.objects.all()

    serializer_class = UserRegistrationSerializer

    permission_classes = [AllowAny]

    authentication_classes = []


# ==========================================
# LOGIN
# ==========================================

class LoginView(TokenObtainPairView):

    serializer_class = CustomTokenObtainPairSerializer

    permission_classes = [AllowAny]

    authentication_classes = []


# ==========================================
# PROFILE
# ==========================================

class ProfileView(generics.RetrieveUpdateAPIView):

    serializer_class = UserProfileSerializer

    permission_classes = [IsAuthenticated]

    http_method_names = [
        "get",
        "patch",
        "head",
        "options",
    ]

    def get_object(self):
        return self.request.user


# ==========================================
# LOGOUT
# ==========================================

class LogoutView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        refresh_token = request.data.get(
            "refresh"
        )

        if not refresh_token:
            return Response(
                {
                    "detail": "Refresh token is required."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)

            token_user_id = token.payload.get(
                "user_id"
            )

            if str(token_user_id) != str(request.user.pk):
                return Response(
                    {
                        "detail": (
                            "This refresh token does not "
                            "belong to the authenticated user."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token.blacklist()

        except TokenError:
            return Response(
                {
                    "detail": "Invalid or expired refresh token."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "detail": "Logged out successfully."
            },
            status=status.HTTP_200_OK,
        )


# ==========================================
# ADMIN: LIST USERS
# ==========================================

class UserListView(generics.ListAPIView):

    queryset = User.objects.all().order_by(
        "-date_joined"
    )

    serializer_class = AdminUserSerializer

    permission_classes = [IsAdminRole]

    filterset_fields = [
        "role",
        "is_active",
    ]

    search_fields = [
        "username",
        "email",
        "first_name",
        "last_name",
    ]


# ==========================================
# ADMIN: VIEW / UPDATE USER
# ==========================================

class UserDetailView(
    generics.RetrieveUpdateAPIView
):

    queryset = User.objects.all()

    serializer_class = AdminUserSerializer

    permission_classes = [IsAdminRole]

    http_method_names = [
        "get",
        "patch",
        "head",
        "options",
    ]
