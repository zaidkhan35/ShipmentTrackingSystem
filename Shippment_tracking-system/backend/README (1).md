# 🚚 ShipTrack — Shipment Tracking System

## Group Information

| Field | Details |
|-------|---------|
| **Group Number** | 20 |
| **Project Title** | Shipment Tracking System |

### Group Members

| Name | Roll Number |
|------|------------|
| Muhammad Zaid | 24P-0534 |
| Abdul Rehman | 24P-0601 |
| Muhammad Bilal | 24P-0738 |

---

## Project Description

ShipTrack is a web-based **Shipment Tracking System** that allows admins, logistics staff, and customers to manage and track shipments in real time. The system supports role-based access control where:

- **Admin** registers customers and supervises logistics staff
- **Logistics Staff** creates, updates, and manages shipments and tracking updates
- **Customers** can view and track their own shipments

---

## GitHub Repository

🔗 **https://github.com/zaidkhan35/ShipmentTrackingSystem**
---

## Technologies Used

| Layer | Technology |
|-------|-----------|
| **Database** | SQLite 3 (file-based, no server required) |
| **ORM** | SQLAlchemy 2.0 |
| **Backend** | Python 3.11, FastAPI, Uvicorn |
| **Authentication** | JWT (JSON Web Tokens) via `python-jose` |
| **Password Hashing** | bcrypt via `passlib` |
| **Data Validation** | Pydantic v2 |
| **Frontend** | Pure HTML5, CSS3, Vanilla JavaScript |
| **Version Control** | Git & GitHub |

---

## Database Schema (7 Tables)

```
User ──── Admin          (Is-A relationship)
User ──── Customer       (Is-A relationship)
User ──── Logistics_Staff (Is-A relationship)

Admin    ──[Registers]──► Customer
Admin    ──[Supervises]──► Logistics_Staff
Customer ──[Tracks]──────► Shipment
LogisticsStaff ─[Manages]► Shipment
Shipment ──[Contains]───► Product      (1 to Many)
Shipment ──[Has]─────────► Tracking_Info (1 to Many)
```

---

## CRUD Operations Implemented

| Operation | Endpoint | Description |
|-----------|----------|-------------|
| **CREATE** | `POST /api/shipments/` | Create a new shipment with products |
| **CREATE** | `POST /api/tracking/{id}` | Add a tracking update to a shipment |
| **CREATE** | `POST /api/auth/register` | Register a new user |
| **READ** | `GET /api/shipments/` | View all shipments (filtered by role) |
| **READ** | `GET /api/tracking/{id}` | View tracking history for a shipment |
| **READ** | `GET /api/dashboard/stats` | View live system statistics |
| **UPDATE** | `PATCH /api/shipments/{id}` | Update shipment status/details |
| **UPDATE** | `PATCH /api/users/customers/{id}` | Update customer information |
| **DELETE** | `DELETE /api/shipments/{id}` | Delete a shipment (staff only) |
| **DELETE** | `DELETE /api/tracking/{id}` | Delete a tracking entry (staff only) |
| **DELETE** | `DELETE /api/products/{id}` | Remove a product from a shipment |
| **DELETE** | `DELETE /api/users/staff/{id}` | Remove a staff member (admin only) |

---

## Installation & Running the Application

### Prerequisites
- Python 3.9 or higher installed
- Git installed

### Step 1 — Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/shiptrack-group20.git
cd shiptrack-group20
```

### Step 2 — Set Up the Backend
```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install all dependencies
pip install -r requirements.txt
```

### Step 3 — Run the Backend Server
```bash
uvicorn main:app --reload --port 8000
```

The server will start at **http://localhost:8000**

> ✅ The SQLite database (`shiptrack.db`) is created **automatically** on first run.
> ✅ Demo data is **seeded automatically** — no manual SQL needed.

### Step 4 — Open the Frontend
Open `frontend/index.html` in any web browser.

Or visit: **http://localhost:8000** (served automatically by FastAPI)

---

## Demo Login Credentials

| Role | Email | Password |
|------|-------|----------|
| 👑 Admin | admin@shiptrack.com | admin123 |
| 🧑‍💼 Staff | ali@shiptrack.com | staff123 |
| 👤 Customer | zaid@example.com | customer123 |

---

## API Documentation

Interactive API docs available at: **http://localhost:8000/docs**

---

## SQL Injection Security

This application is **protected against SQL Injection** because:

1. **SQLAlchemy ORM** is used for all database queries — user input is never directly concatenated into SQL strings
2. All queries use **parameterized statements** automatically handled by SQLAlchemy
3. **Pydantic v2** validates and sanitizes all incoming request data before it reaches the database layer

Example of safe query in our code:
```python
# SAFE — SQLAlchemy parameterizes this automatically
user = db.query(models.User).filter(models.User.email == payload.email).first()

# What SQLAlchemy generates internally:
# SELECT * FROM User WHERE email = ?  -- with payload.email as a safe parameter
# The ? is never replaced by raw string concatenation
```

---

## Project Structure

```
shiptrack-group20/
├── backend/
│   ├── main.py              ← App entry point + auto seed data
│   ├── database.py          ← SQLite connection (SQLAlchemy)
│   ├── models.py            ← ORM models (7 tables)
│   ├── schemas.py           ← Pydantic request/response validation
│   ├── auth.py              ← JWT authentication + bcrypt hashing
│   ├── requirements.txt     ← Python dependencies
│   └── routers/
│       ├── auth_router.py   ← Login & Register endpoints
│       ├── shipments.py     ← Shipment CRUD (Staff manages)
│       └── other_routers.py ← Tracking, Users, Products, Dashboard
│
└── frontend/
    └── index.html           ← Complete single-page application
```
