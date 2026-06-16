from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='auth-login'),
    path('logout/', views.LogoutView.as_view(), name='auth-logout'),
    path('profile/', views.UserProfileView.as_view(), name='auth-profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='auth-change-password'),
    path('users/', views.UserListView.as_view(), name='auth-users-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='auth-users-detail'),
    path('setup/', views.SetupAdminView.as_view(), name='auth-setup'),
    path('seed-users/', views.SeedUsersView.as_view(), name='auth-seed-users'),
    path('token/', views.CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', views.CustomTokenRefreshView.as_view(), name='token-refresh'),
]
