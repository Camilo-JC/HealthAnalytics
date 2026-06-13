import os
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from .serializers import (
    LoginSerializer, UserSerializer, UserCreateSerializer,
    UserUpdateSerializer, ChangePasswordSerializer, LogoutSerializer
)
from core.permissions import IsAdmin, CanManageUsers
from core.audit import log_audit

User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        log_audit(user, 'login', 'authentication', description=f"Inicio de sesión: {user.email}", request=request)
        return Response({
            'success': True,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })


class LogoutView(APIView):
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data['refresh'])
            token.blacklist()
            log_audit(request.user, 'logout', 'authentication', description="Cierre de sesión", request=request)
            return Response({'success': True, 'message': 'Sesión cerrada exitosamente'})
        except Exception:
            return Response(
                {'success': False, 'message': 'Error al cerrar sesión'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, CanManageUsers]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        log_audit(self.request.user, 'create', 'users', resource_type='user',
                  resource_id=user.id, description=f"Usuario creado: {user.email}",
                  request=self.request)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, CanManageUsers]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserSerializer

    def perform_destroy(self, instance):
        log_audit(self.request.user, 'delete', 'users', resource_type='user',
                  resource_id=instance.id, description=f"Usuario eliminado: {instance.email}",
                  request=self.request)
        instance.delete()

    def perform_update(self, serializer):
        old_role = serializer.instance.role
        user = serializer.save()
        if old_role != user.role:
            log_audit(self.request.user, 'update', 'users', resource_type='user',
                      resource_id=user.id,
                      description=f"Rol cambiado: {old_role} -> {user.role}",
                      request=self.request)


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response({'success': True, 'message': 'Contraseña actualizada exitosamente'})


class SetupAdminView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from django.conf import settings
        email = getattr(settings, 'ADMIN_EMAIL', os.environ.get('ADMIN_EMAIL', ''))
        password = getattr(settings, 'ADMIN_PASSWORD', os.environ.get('ADMIN_PASSWORD', ''))
        if not email or not password:
            return Response({'error': 'ADMIN_EMAIL and ADMIN_PASSWORD not configured'}, status=400)
        user, created = User.objects.get_or_create(
            email=email,
            defaults={'full_name': 'Administrador', 'role': 'admin', 'is_staff': True, 'is_superuser': True}
        )
        if created:
            user.set_password(password)
            user.save()
            return Response({'message': f'Superuser {email} created'})
        return Response({'message': f'Superuser {email} already exists', 'user_id': user.id})


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = get_object_or_404(User, email=request.data.get('email'))
            response.data['user'] = UserSerializer(user).data
            response.data['success'] = True
        return response


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            response.data['success'] = True
        return response
