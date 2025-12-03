from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from estoque import views as estoque_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Autenticação
    path('accounts/login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),

    # Home → tela central de itens (US4)
    path('', estoque_views.index, name='home'),

    # App de estoque
    path('estoque/', include('estoque.urls')),
]
