from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from apps.users.views import RegisterView, SelfView

urlpatterns = [
    path('users/register', RegisterView.as_view(), name='register'),
    path('users/self', SelfView.as_view(), name='self'),
    path('auth/token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
]