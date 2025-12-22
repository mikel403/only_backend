from django.urls import path,include
from django.views.generic import TemplateView
from . import views


from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("reset-password/",views.ResetPassword),
    
    # path("", views.UserView.as_view())
    # path("", views.NoduleList.as_view()),
    # path("<int:pk>/", views.NoduleDetail.as_view()),
    # path("", views.NoduleDetail),
]