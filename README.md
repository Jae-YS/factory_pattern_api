# Mechanic Factory API

This project is a RESTful API for managing **customers, mechanics, service tickets, inventory, inventory assignments, and service assignments** in a mechanic shop. It features **token-based authentication**, **rate limiting**, **caching**, and **role-based access control**, and is **deployed with CI/CD using GitHub Actions and Render**.

---

## Live API

- **Swagger Docs**: [`https://mechanic-api-uwqv.onrender.com/api/docs`](https://mechanic-api-uwqv.onrender.com/api/docs)

---

## Features

### Customers API

- `POST /customers`: Register a new customer.
- `POST /customers/login`: Login as a customer (returns JWT token).
- `GET /customers`: Retrieve paginated list of customers.
- `PUT /customers/<id>`: Update customer info (requires token).
- `DELETE /customers/<id>`: Delete customer (requires token).
- `GET /customers/my-tickets`: Retrieve tickets for logged-in customer.

### Mechanics API

- `POST /mechanics`: Register a new mechanic.
- `POST /mechanics/login`: Login as a mechanic (returns JWT token).
- `GET /mechanics`: Retrieve all mechanics.
- `GET /mechanics/top`: Get mechanics ranked by tickets worked on.

### Service Tickets API

- `POST /service_tickets`: Create a service ticket (customer token required).
- `GET /service_tickets`: List all service tickets.
- `PUT /service_tickets/<id>/edit`: Add/remove mechanics (token required).

### Inventory API

- `POST /inventory`: Add a new inventory item (mechanic token required).
- `GET /inventory`: List all inventory items.
- `GET /inventory/<id>`: Retrieve a single inventory item.
- `PUT /inventory/<id>`: Update inventory item.
- `DELETE /inventory/<id>`: Delete inventory item.

### Inventory Assignments API

- `POST /inventory_assignment`: Assign inventory to a service ticket.
- `GET /inventory_assignment`: List all assignments.
- `PUT /inventory_assignment`: Update assignment quantity.
- `DELETE /inventory_assignment`: Remove inventory from a ticket.

### Service Assignments API

- `POST /service_assignment`: Assign mechanic to a service ticket.
- `GET /service_assignment`: List all service assignments.
- `DELETE /service_assignment`: Remove mechanic from a service ticket.

---

## Advanced Features

- **JWT Authentication**:
  - Customers and mechanics have role-based JWT tokens.
- **Rate Limiting**: Prevents abuse using `Flask-Limiter`.
- **Caching**: Frequently accessed routes use `Flask-Caching`.
- **Swagger Docs**: Full API documentation with example requests/responses.

---

## Technologies Used

- **Flask** - API Framework
- **SQLAlchemy** - ORM
- **Marshmallow** - Serialization
- **Flask-Limiter** - Rate Limiting
- **Flask-Caching** - Caching
- **PyJWT** / **python-jose** - JWT
- **PostgreSQL** (Production DB hosted on Render)

---

### Prerequisites

- Python 3.10+
- MySQL (Local Dev) or PostgreSQL (Production)
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
   DATABASE_URI=mysql+pymysql://user:password@localhost:3306/mechanic_factory_db
   SQLALCHEMY_DATABASE_URI=postgresql+psycopg2://user:password@host:port/db_name
   ```

4. **Run the app locally**

   ```bash
   python3 flask_app.py
   ```

5. Visit **Swagger Docs** locally: [http://127.0.0.1:5000/api/docs](http://127.0.0.1:5000/api/docs)

---

## Testing

### un Python Unit Tests

```bash
python -m unittest discover tests
```

---

## Deployment (CI/CD)

This API uses **GitHub Actions** and **Render** for continuous deployment.

1. Every push to the `main` branch:
   - Runs unit tests.
   - If tests pass, auto-deploys to Render.

2. Environment variables for deployment:
   - `SECRET_KEY`
   - `SQLALCHEMY_DATABASE_URI`
   - `RENDER_SERVICE_ID`
   - `RENDER_API_KEY`

3. **Workflow File**: See `.github/workflows/main.yaml`

---

## Folder Structure

```
app/
├── blueprints/
│   ├── customers/
│   ├── mechanics/
│   ├── inventory/
│   ├── service_tickets/
│   ├── serviceassignment/
│   └── inventoryassignment/
├── models.py
├── extensions.py
├── utils/
├── static/
│   └── bundled.yaml  <-- Swagger Docs
```

---

## Postman Collection

1. Import `postman_collection.json`
2. Use preconfigured requests to test endpoints.

---

## API Docs

View interactive API docs at:  
[https://mechanic-api-uwqv.onrender.com/api/docs](https://mechanic-api-uwqv.onrender.com/api/docs)

---

## CI/CD Status

![CI/CD](https://github.com/Jae-YS/factory_pattern_api/actions/workflows/main.yaml/badge.svg)
