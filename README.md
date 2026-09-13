# Cloud Expense Management System - Backend

Backend service for a cloud-based expense management system with AI-powered expense analysis.

## Project Overview

The backend provides REST APIs for:
- User registration and authentication
- JWT-based authorization
- Role-based access control
- User profile and password management
- Expense CRUD operations
- Monthly financial calculations
- Future/planned expense analysis
- AI-powered spending analysis
- Administrative user management
- Cloud database communication

## Architecture

```text
                         +----------------------+
                         |        User          |
                         +----------+-----------+
                                    |
                                  HTTPS
                                    |
                                    v
                         +----------------------+
                         |   React Frontend     |
                         |       Vercel         |
                         +----------+-----------+
                                    |
                                 REST API
                                    |
                                    v
                    +-----------------------------+
                    |      FastAPI Backend        |
                    |          Render             |
                    +-------------+---------------+
                                  |
                    +-------------+-------------+
                    |                           |
                    v                           v
          +------------------+        +------------------+
          | Supabase         |        | OpenRouter       |
          | PostgreSQL       |        | Nemotron Model   |
          +------------------+        +------------------+
```

## Technology Stack

### Backend
- Python
- FastAPI
- SQLAlchemy
- Pydantic
- JWT Authentication
- bcrypt
- PostgreSQL
- Docker

### Cloud Services
- Render - Backend deployment
- Supabase - Cloud PostgreSQL database
- OpenRouter - AI model API

### AI
The backend uses an OpenRouter-hosted Nemotron model for expense analysis. The backend performs authoritative financial calculations, while AI provides analysis and recommendations.

## Features

### Authentication
- User registration
- User login
- JWT access tokens
- bcrypt password hashing
- Authenticated API access
- Role-based authorization

### User Management
Users can:
- View their profile
- Update name
- Update email
- Update monthly salary
- Change their password

Account roles cannot be changed by users.

### Expense Management
Authenticated users can:
- Create an expense
- View all personal expenses
- View a specific expense
- Update an expense
- Delete an expense

Each expense contains:
- Title
- Amount
- Category
- Description
- Expense date

Users can only access their own expenses.

### Financial Analysis
The backend calculates:
- Current month's total spending
- Remaining monthly balance
- Days remaining in the month
- Daily spending limit
- Future/planned expenses
- Future expense total
- Projected balance
- Category-wise spending totals

Future-dated expenses are treated separately from already-incurred expenses.

### AI Expense Analysis
When an expense is created, relevant financial information is sent to the AI analysis service.

The AI can provide:
- Spending summary
- Spending patterns
- Related expense analysis
- Risk level
- Expense assessment
- Spending recommendation

If AI analysis fails, the expense remains successfully saved.

### Negative Balance Handling
When spending exceeds the available monthly budget:
- The system identifies an existing budget shortfall.
- A new expense increases the existing shortfall.
- Percentage-based consumption of a negative balance is avoided.
- The projected balance is used for future expense analysis.

### Admin Access
Administrators can view basic registered-user information:
- User ID
- Name
- Email
- Role

The admin user-list endpoint does not expose users' salary or expense information.

## Database

The application uses PostgreSQL hosted on Supabase.

### `users`

| Column | Description |
|---|---|
| `user_id` | Primary key |
| `name` | User name |
| `email` | Unique email address |
| `password` | Hashed password |
| `salary` | Monthly salary |
| `role` | `user` or `admin` |

### `expenses`

| Column | Description |
|---|---|
| `expense_id` | Primary key |
| `user_id` | Foreign key referencing `users` |
| `title` | Expense title |
| `amount` | Expense amount |
| `category` | Expense category |
| `description` | Optional description |
| `expense_date` | Date of expense |

### Relationship

```text
users
  |
  | 1
  |
  | N
  v
expenses
```

One user can have multiple expenses.

## REST API

Production Base URL:

```text
https://expense-manager-api-kysg.onrender.com
```

### Authentication

```http
POST /auth/register
POST /auth/login
```

### User Profile

```http
GET /users/me
PUT /users/me
PUT /users/me/password
```

### Expenses

```http
GET /expenses
GET /expenses/{expense_id}
POST /expenses
PUT /expenses/{expense_id}
DELETE /expenses/{expense_id}
```

### AI Analysis

```http
GET /ai/analyze
```

### Admin

```http
GET /admin/users
```

Admin endpoint requires administrator authorization.

## Authentication

The backend uses JSON Web Tokens (JWT).

```text
User Login
    |
    v
FastAPI verifies credentials
    |
    v
JWT access token generated
    |
    v
Frontend stores token
    |
    v
Authorization: Bearer <token>
    |
    v
Protected API endpoint
```

Passwords are hashed using bcrypt before being stored.

## Project Structure

```text
Expense Manager/
|
+-- main.py
+-- models.py
+-- schemas.py
+-- auth.py
+-- database.py
+-- ai_service.py
|
+-- requirements.txt
+-- Dockerfile
+-- .dockerignore
+-- .gitignore
|
+-- .env
+-- test_ai.py
```

| File | Purpose |
|---|---|
| `main.py` | FastAPI application and REST endpoints |
| `models.py` | SQLAlchemy database models |
| `schemas.py` | Pydantic request/response schemas |
| `auth.py` | JWT authentication and password handling |
| `database.py` | PostgreSQL database connection |
| `ai_service.py` | AI/OpenRouter integration |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Container configuration |

## Environment Variables

Example:

```env
DIRECT_URL=your_supabase_postgresql_connection_string
OPENROUTER_API_KEY=your_openrouter_api_key
SECRET_KEY=your_jwt_secret_key
```

Do not commit `.env` files or API keys to GitHub.

## Local Development

### 1. Clone the repository

```bash
git clone <your-backend-repository-url>
cd Expense-Manager
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Windows:

```cmd
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file with the required values.

### 5. Run the backend

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

## API Documentation

FastAPI automatically provides interactive documentation.

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

ReDoc:

```text
http://127.0.0.1:8000/redoc
```

The deployed backend also provides these documentation pages through its Render URL.

## Docker

Build the Docker image:

```bash
docker build -t expense-manager-backend .
```

Run the container:

```bash
docker run -p 8000:8000 expense-manager-backend
```

The container runs the FastAPI application using Uvicorn.

## Cloud Deployment

The backend is deployed on Render.

```text
GitHub
   |
   v
Render
   |
   v
Docker Container
   |
   v
FastAPI Application
   |
   +------------------> Supabase PostgreSQL
   |
   +------------------> OpenRouter AI
```

Production backend:

```text
https://expense-manager-api-kysg.onrender.com
```

## Security

The backend implements:
- JWT-based authentication
- bcrypt password hashing
- Protected API endpoints
- Role-based authorization
- User-specific expense access
- Admin-only endpoints
- Environment variables for secrets
- CORS configuration for frontend communication

Users cannot access another user's expenses by changing an expense ID because the backend validates both the expense ID and authenticated user's ID.

## Error Handling

Common HTTP status codes:

```text
400 - Invalid request / duplicate email
401 - Invalid authentication
403 - Insufficient permissions
404 - Resource not found
500 - Internal server error
```

AI failures do not prevent a successfully created expense from being saved.

## Cloud Computing Components

| Component | Cloud Service |
|---|---|
| Frontend | Vercel |
| Backend | Render |
| Database | Supabase PostgreSQL |
| AI Service | OpenRouter |
| Source Control | GitHub |

The project demonstrates a distributed cloud architecture where the client, application server, database, and AI service are independently hosted.

## Frontend

The backend is consumed by a separate React frontend:

```text
https://expense-manager-gilt-ten.vercel.app/
```

The frontend communicates with the backend using HTTPS REST APIs.

## License

This project was developed as an academic cloud computing project.

## Author

Developed as part of the Cloud Infrastructure and Architecture Digital Assignment.

**Cloud-Based Expense Management System with AI Expense Analysis**

**Sanjeev Prasad R**  
Computer Science and Engineering
