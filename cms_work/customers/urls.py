from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.dashboard, name="dashboard"),
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/add/", views.customer_create, name="customer_create"),
    path("customers/<int:pk>/", views.customer_detail, name="customer_detail"),
    path("customers/<int:pk>/edit/", views.customer_edit, name="customer_edit"),
    path("customers/import/", views.customer_import, name="customer_import"),
    path("bills/", views.bill_list, name="bill_list"),
    path("bills/add/", views.bill_create, name="bill_create"),
    path("payments/add/", views.payment_create, name="payment_create"),
    path("dues/", views.due_list, name="due_list"),
    path("reports/customers.xlsx", views.export_customers, name="export_customers"),
]
