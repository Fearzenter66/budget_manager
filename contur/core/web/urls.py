from django.urls import path

from core.web import views

app_name = 'web'

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('home/', views.home, name='home'),
    path('expenses/add/', views.add_expense_view, name='add_expense'),
    path('income/add/', views.add_income_view, name='add_income'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('settings/', views.settings_view, name='settings'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
]
