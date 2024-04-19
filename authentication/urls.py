from django.urls import path
from .import views
from django.contrib.auth.views import LogoutView

app_name = "authentication"
urlpatterns = [
    path('login/', views.login_view, name="login"),
    path('register/', views.register_user, name="register"),
    path("logout/", views.user_logout, name="logout"),
    path('profile/', views.profile_edit, name='profile'),
]
