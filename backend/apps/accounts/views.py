from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.accounts.permissions import IsTenantMember
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import ChangePasswordSerializer, TenantTokenObtainPairSerializer
class TenantTokenObtainPairView(TokenObtainPairView):
    serializer_class=TenantTokenObtainPairSerializer


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated, IsTenantMember]

    @extend_schema(
        summary="Changer mon mot de passe",
        request=ChangePasswordSerializer,
        responses={200: None},
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Mot de passe modifié."}, status=status.HTTP_200_OK)
