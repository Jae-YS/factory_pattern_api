# Mechanic Factory API

This project is a RESTful API for managing **customers, mechanics, service tickets, inventory, and service assignments** in a mechanic shop. It implements advanced features like **token-based authentication**, **rate limiting**, **caching**, and **role-based access control**.

---

### Customers API

- `POST /customers`: Register a new customer.
- `POST /customers/login`: Login as a customer and receive a JWT token.
- `GET /customers`: Retrieve paginated list of customers (supports `page`, `per_page`).
- `PUT /customers/<id>`: Update customer info (requires token).
- `DELETE /customers/<id>`: Delete customer (requires token).
- `GET /customers/my-tickets`: Retrieve service tickets for the logged-in customer (token required).

### Mechanics API

- `POST /mechanics`: Register a new mechanic.
- `POST /mechanics/login`: Login as a mechanic and receive a JWT token.
- `GET /mechanics`: Retrieve all mechanics.
- `GET /mechanics/top`: Get mechanics ordered by the number of service tickets worked on.
- Protected routes require mechanic token.

### Service Tickets API

- `POST /service_tickets`: Create a service ticket (requires customer token).
- `GET /service_tickets`: List all service tickets.
- `PUT /service_tickets/<id>/edit`: Add or remove mechanics from a ticket (requires token).

### Inventory API

- `POST /inventory`: Add a new inventory item (requires mechanic token).
- `GET /inventory`: List all inventory items (requires mechanic token).
- `GET /inventory/<id>`: Retrieve a single inventory item (requires mechanic token).
- `PUT /inventory/<id>`: Update inventory item (requires mechanic token).
- `DELETE /inventory/<id>`: Delete inventory item (requires mechanic token).

### Service Assignments API

- `POST /assignments`: Assign a mechanic to a service ticket.
- `GET /assignments`: List all mechanic-service ticket assignments.
- `DELETE /assignments`: Remove a mechanic from a service ticket.

### Advanced Features

- **Rate Limiting**: Applied globally to protect against API abuse using `Flask-Limiter`.
- **Caching**: Implemented on frequently accessed routes using `Flask-Caching`.
- **JWT Authentication**:
  - Customers and Mechanics have separate tokens with role-based access control.
  - Decorators: `@token_required` for customers, `@mechanic_token_required` for mechanics.

### Relationships

- Many-to-many between **Mechanics ↔ ServiceTickets** (via ServiceAssignment).
- Many-to-many between **Inventory ↔ ServiceTickets**.

### Testing

- Postman collection included for testing all API endpoints.
- Python test script available in `tests/api_tests.py`.

---

## Getting Started

### Prerequisites

- Python 3.10+
- MySQL or SQLite
- Virtual environment (recommended)

### Installation

1. **Clone the repository**

```bash
git clone https://github.com/Jae-YS/factory_pattern_api
cd mechanic-factory-api
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
   Create a `.env` file:

```env
SECRET_KEY=your_secret_key
DATABASE_URI=mysql+pymysql://user:password@localhost/mechanic_factory_db
```

5. **Run the app**

```bash
python3 app.py
```

---

## Folder Structure

```
app/
├── blueprints/
│   ├── customers/
│   ├── mechanics/
│   ├── inventory/
│   ├── service_tickets/
│   └── serviceassignment/
├── models.py
├── extensions.py
└── utils/
```

---

## Technologies Used

- **Flask** - API Framework
- **SQLAlchemy** - ORM for database interactions
- **Marshmallow** - Serialization & Validation
- **Flask-Limiter** - Rate Limiting
- **Flask-Caching** - Caching
- **PyJWT** & **python-jose** - JWT Authentication
- **MySQL** (or SQLite) - Database

---

## Testing

### Run Python Test Script

```bash
python tests/api_tests.py
```

### Test with Postman

1. Import the included **Postman collection**: `postman_collection.json`
2. Use the sample requests to test all endpoints.

---
