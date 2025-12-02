from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('estoque', include('estoque.urls')),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('item/lista', TemplateView.as_view(template_name='estoque/item_list.html'), name='item_list'),
    path('item/formulario', TemplateView.as_view(template_name='estoque/item_form.html'), name='item_form'),
    path('movimentacao/formulario', TemplateView.as_view(template_name='estoque/movimentacao_form.html'), name='movimentacao_form'),
    path('relatorio/cmv', TemplateView.as_view(template_name='estoque/relatorio_cmv.html'), name='relatorio_cmv'),
]
