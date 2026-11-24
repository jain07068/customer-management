from decimal import Decimal
from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator, MinValueValidator

class Customer(models.Model):
    name = models.CharField(max_length=180)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, db_index=True)
    alternate_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=12, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["phone"], name="unique_customer_phone")
        ]

    def __str__(self):
        return f"{self.name} ({self.phone})"

    @property
    def total_billed(self):
        return sum((b.total_amount for b in self.bills.all()), Decimal("0.00"))

    @property
    def total_paid(self):
        return sum((p.amount for b in self.bills.all() for p in b.payments.all()), Decimal("0.00"))

    @property
    def total_due(self):
        return self.total_billed - self.total_paid

class Bill(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="bills")
    invoice_number = models.CharField(max_length=40, unique=True)
    bill_date = models.DateField()
    description = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    attachment = models.FileField(upload_to="bill_copies/%Y/%m/", blank=True,
        validators=[FileExtensionValidator(["pdf", "jpg", "jpeg", "png"])])
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-bill_date", "-id"]

    @property
    def paid_amount(self):
        return self.payments.aggregate(total=models.Sum("amount"))["total"] or Decimal("0.00")

    @property
    def due_amount(self):
        return self.total_amount - self.paid_amount

    @property
    def payment_status(self):
        if self.paid_amount == 0: return "Unpaid"
        if self.due_amount <= 0: return "Paid"
        return "Partial"

class Payment(models.Model):
    MODES = [("Cash","Cash"),("UPI","UPI"),("Bank Transfer","Bank Transfer"),("Cheque","Cheque"),("Other","Other")]
    bill = models.ForeignKey(Bill, on_delete=models.PROTECT, related_name="payments")
    payment_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    mode = models.CharField(max_length=20, choices=MODES, default="Cash")
    reference = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-payment_date", "-id"]

    def __str__(self):
        return f"{self.bill.invoice_number} - {self.amount}"
