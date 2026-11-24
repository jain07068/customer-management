from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from .models import Customer, Bill, Payment
from .forms import CustomerForm, BillForm, PaymentForm, import_customers_csv

@login_required
def dashboard(request):
    bills = Bill.objects.all()
    context = {
        "customer_count": Customer.objects.count(),
        "bill_count": bills.count(),
        "billed": bills.aggregate(v=Sum("total_amount"))["v"] or Decimal("0.00"),
        "paid": Payment.objects.aggregate(v=Sum("amount"))["v"] or Decimal("0.00"),
        "customers": Customer.objects.order_by("-created_at")[:6],
        "bills": bills[:6],
    }
    context["due"] = context["billed"] - context["paid"]
    return render(request, "customers/dashboard.html", context)

@login_required
def customer_list(request):
    q = request.GET.get("q", "").strip()
    customers = Customer.objects.all()
    if q:
        customers = customers.filter(Q(name__icontains=q)|Q(email__icontains=q)|Q(phone__icontains=q))
    return render(request, "customers/customer_list.html", {"customers": customers, "q": q})

@login_required
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if form.is_valid():
        customer = form.save(); messages.success(request, "Customer created successfully.")
        return redirect("customer_detail", pk=customer.pk)
    return render(request, "customers/customer_form.html", {"form": form, "title": "Add Customer"})

@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if form.is_valid():
        form.save(); messages.success(request, "Customer updated.")
        return redirect("customer_detail", pk=pk)
    return render(request, "customers/customer_form.html", {"form": form, "title": "Edit Customer"})

@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, "customers/customer_detail.html", {"customer": customer})

@login_required
def customer_import(request):
    if request.method == "POST":
        upload = request.FILES.get("csv_file")
        try:
            imported, skipped, errors = import_customers_csv(upload)
            messages.success(request, f"Imported: {imported}; skipped: {skipped}.")
            return render(request, "customers/import.html", {"errors": errors, "imported": imported, "skipped": skipped})
        except (ValueError, UnicodeDecodeError, AttributeError) as exc:
            messages.error(request, str(exc))
    return render(request, "customers/import.html")

@login_required
def bill_list(request):
    q = request.GET.get("q", "").strip()
    bills = Bill.objects.select_related("customer").all()
    if q: bills = bills.filter(Q(invoice_number__icontains=q)|Q(customer__name__icontains=q)|Q(customer__phone__icontains=q))
    return render(request, "customers/bill_list.html", {"bills": bills, "q": q})

@login_required
def bill_create(request):
    form = BillForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        bill = form.save(commit=False); bill.created_by = request.user; bill.save()
        messages.success(request, "Bill created."); return redirect("bill_list")
    return render(request, "customers/bill_form.html", {"form": form})

@login_required
def payment_create(request):
    form = PaymentForm(request.POST or None)
    if form.is_valid():
        payment = form.save(commit=False); payment.created_by = request.user; payment.save()
        messages.success(request, "Payment recorded."); return redirect("customer_detail", pk=payment.bill.customer_id)
    return render(request, "customers/payment_form.html", {"form": form})

@login_required
def due_list(request):
    customers = [c for c in Customer.objects.prefetch_related("bills__payments") if c.total_due > 0]
    q = request.GET.get("q", "").strip()
    if q: customers = [c for c in customers if q.lower() in c.name.lower() or q.lower() in c.email.lower() or q in c.phone]
    return render(request, "customers/due_list.html", {"customers": customers, "q": q})

@login_required
def export_customers(request):
    wb = Workbook(); ws = wb.active; ws.title = "Customers"
    headers = ["Customer ID","Name","Email","Phone","City","State","Total Billed","Paid","Outstanding"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF"); cell.fill = PatternFill("solid", fgColor="243B53")
    for c in Customer.objects.prefetch_related("bills__payments"):
        ws.append([c.id,c.name,c.email,c.phone,c.city,c.state,float(c.total_billed),float(c.total_paid),float(c.total_due)])
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = min(max(max(len(str(x.value or "")) for x in col)+2, 14), 32)
    response = HttpResponse(content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = 'attachment; filename="customer_report.xlsx"'
    wb.save(response); return response
