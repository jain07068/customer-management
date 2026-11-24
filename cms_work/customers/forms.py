import csv
from decimal import Decimal
from django import forms
from django.db import transaction
from django.db.models import Sum
from .models import Customer, Bill, Payment


class BootstrapModelForm(forms.ModelForm):
    """Apply consistent Bootstrap styling to generated form controls."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault("class", "form-check-input")
            elif isinstance(widget, forms.Select):
                widget.attrs.setdefault("class", "form-select")
            elif isinstance(widget, (forms.FileInput,)):
                widget.attrs.setdefault("class", "form-control")
            else:
                widget.attrs.setdefault("class", "form-control")
            widget.attrs.setdefault("placeholder", f"Enter {field.label.lower()}")


class CustomerForm(BootstrapModelForm):
    class Meta:
        model = Customer
        fields = ["name", "email", "phone", "alternate_phone", "address", "city", "state", "pincode", "is_active"]
        widgets = {"address": forms.Textarea(attrs={"rows": 2})}


class BillForm(BootstrapModelForm):
    class Meta:
        model = Bill
        fields = ["customer", "invoice_number", "bill_date", "description", "total_amount", "attachment", "notes"]
        widgets = {
            "bill_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 2}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }


class BillChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, bill):
        return f"{bill.invoice_number}  |  {bill.customer.name} ({bill.customer.phone})  |  Due: ₹{bill.due_amount:,.2f}"


class PaymentForm(BootstrapModelForm):
    bill = BillChoiceField(
        queryset=Bill.objects.none(),
        label="Bill Number / Customer Name",
        empty_label="Select bill and customer",
        help_text="Each option shows the invoice number, customer name, mobile number and current due amount.",
    )

    class Meta:
        model = Payment
        fields = ["bill", "payment_date", "amount", "mode", "reference", "notes"]
        widgets = {
            "payment_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only bills with a remaining balance can receive a payment.
        open_bill_ids = [bill.id for bill in Bill.objects.select_related("customer").prefetch_related("payments").all() if bill.due_amount > 0]
        self.fields["bill"].queryset = Bill.objects.filter(id__in=open_bill_ids).select_related("customer").order_by("-bill_date", "invoice_number")
        self.fields["bill"].widget.attrs.update({"class": "form-select", "data-placeholder": "Choose a bill"})
        self.fields["amount"].widget.attrs.update({"min": "0.01", "step": "0.01"})

    def clean(self):
        cleaned = super().clean()
        bill, amount = cleaned.get("bill"), cleaned.get("amount")
        if bill and amount is not None and amount > bill.due_amount:
            self.add_error("amount", f"Payment exceeds current due (₹{bill.due_amount:,.2f}).")
        return cleaned


def import_customers_csv(upload):
    decoded = upload.read().decode("utf-8-sig").splitlines()
    reader = csv.DictReader(decoded)
    required = {"name", "phone"}
    if not reader.fieldnames or not required.issubset(set(reader.fieldnames)):
        raise ValueError("CSV must contain at least these headers: name, phone. Optional: email,address,city,state,pincode")
    imported, skipped, errors = 0, 0, []
    with transaction.atomic():
        for line, row in enumerate(reader, start=2):
            name, phone = (row.get("name") or "").strip(), (row.get("phone") or "").strip()
            if not name or not phone:
                skipped += 1
                errors.append(f"Row {line}: name and phone are required.")
                continue
            if Customer.objects.filter(phone=phone).exists():
                skipped += 1
                errors.append(f"Row {line}: phone {phone} already exists.")
                continue
            Customer.objects.create(
                name=name, phone=phone, email=(row.get("email") or "").strip(),
                address=(row.get("address") or "").strip(), city=(row.get("city") or "").strip(),
                state=(row.get("state") or "").strip(), pincode=(row.get("pincode") or "").strip()
            )
            imported += 1
    return imported, skipped, errors
