# 🎓 CGPA Calculator with Email OTP & Admin Dashboard

This is a web-based CGPA Calculator built using **Django (backend)** and **Streamlit (frontend)**. Users can:
- Calculate semester-wise CGPA
- Receive OTP verification via email
- View their history logs
- Admins can view all user logs in a secure dashboard with pagination

---

## 🚀 Features

- 🔐 Email OTP Verification (FastAPI-based API)
- 📚 Semester & Department-wise Subject Management
- 📊 Streamlit Frontend for CGPA Calculation
- 🧾 Save Results to Database
- 📂 View Personal CGPA History
- 🛡️ Admin-only Paginated Dashboard for Viewing All Logs

---

## 🛠 Tech Stack

| Layer       | Tech             |
|------------|------------------|
| Backend     | Django + DRF     |
| Frontend    | Streamlit        |
| Database    | SQLite (default) |
| Email OTP   | Django Email     |
| Docs        | drf-yasg (Swagger) |

---

## 📝 Requirements


```bash
python -m venv .venv
source .venv/bin/activate   Or .\.venv\Scripts\activate on Windows
pip install -r requirements.txt


## Backend server code

cd backend_or_project_root
python manage.py makemigrations
python manage.py migrate
python manage.py runserver

## Front-End server code

cd front_end
streamlit run cgpa_app.py
