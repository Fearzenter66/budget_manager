from django.urls import path

from core.web import views

app_name = 'web'

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('home/', views.home, name='home'),
    path('expenses/add/', views.add_expense_view, name='add_expense'),
    path('expenses/', views.expense_list_view, name='expense_list'),
    path('expenses/<int:pk>/edit/', views.edit_expense_view, name='edit_expense'),
    path('expenses/<int:pk>/delete/', views.delete_expense_view, name='delete_expense'),
    path('income/add/', views.add_income_view, name='add_income'),
    path('income/', views.income_list_view, name='income_list'),
    path('income/<int:pk>/edit/', views.edit_income_view, name='edit_income'),
    path('income/<int:pk>/delete/', views.delete_income_view, name='delete_income'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('settings/', views.settings_view, name='settings'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
]
