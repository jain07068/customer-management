from django.contrib import admin
from .models import Customer, Bill, Payment
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("name","phone","email","city","is_active","created_at")
    search_fields = ("name","phone","email")
    list_filter = ("is_active","state")
@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ("invoice_number","customer","bill_date","total_amount")
    search_fields = ("invoice_number","customer__name","customer__phone")
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("bill","payment_date","amount","mode")
