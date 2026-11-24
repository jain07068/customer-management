# Customer Management System (Django)

A starter Django CMS for admin-managed customers, bills, payments, outstanding dues, CSV import and XLSX export.

## Run locally

```bash
python -m venv venv
# Windows: venv\\Scripts\\activate
# macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations customers
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open http://127.0.0.1:8000/ and sign in with the superuser account.

## CSV format

Required headers: `name,phone`
Optional headers: `email,address,city,state,pincode`

Example:

```csv
name,phone,email,address,city,state,pincode
Amit Sharma,9876543210,amit@example.com,Main Road,Indore,MP,452001
```

## Notes before production

- This is an MVP starter, not yet a production-hardened accounting system.
- Configure PostgreSQL, a strong `DJANGO_SECRET_KEY`, `DEBUG=False`, allowed hosts, HTTPS, backups and private media access before deployment.
- Validate uploaded file content and size at the server/proxy level; extension validation alone is not sufficient.
- Add pagination, audit trails, role permissions, invoice PDF generation, automated tests and robust ledger export before production.
- Customer phone is currently unique. Adjust the constraint if the business allows shared phone numbers.
