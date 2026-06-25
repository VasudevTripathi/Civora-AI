# Civora AI — Government Compliance Operating System

Civora AI is an enterprise-grade, AI-powered Government Compliance Operating System designed to help entrepreneurs understand, navigate, and execute business registration and ongoing corporate compliance procedures seamlessly.

---

## 🏗️ Directory Structure

This project uses a decoupled monorepo architecture:

```
├── backend/                       # Python FastAPI Backend
│   ├── app/
│   │   ├── api/                   # REST API Routers and Route Endpoints
│   │   ├── core/                  # Security (JWT), Config (Pydantic), DB Connection
│   │   ├── integrations/          # External services: Google Gemini, Qdrant Vector DB
│   │   ├── models/                # SQLAlchemy/SQLModel database entities
│   │   ├── repository/            # Database transactions & queries (Repository pattern)
│   │   ├── schemas/               # Request/Response data models (Pydantic)
│   │   └── services/              # Core business logic (Compliance engines)
│   └── tests/                     # Backend pytest suite
│
├── frontend/                      # React / Next.js / Vite Frontend Application
│   ├── public/                    # Static UI resources
│   └── src/                       # React components, hooks, assets
│
├── docs/                          # System Architecture & Technical Specifications
│   └── architecture.md
│
├── .gitignore                     # Git tracking exclusions
├── package.json                   # Root NPM run scripts and tooling
└── requirements.txt               # Pinned Python backend dependencies
```

---

## 🚀 Getting Started

### Prerequisites
* Python 3.10 or higher
* Node.js v18 or higher
* npm or yarn

### 1. Installation & Environment Setup
To install both frontend and backend dependencies, you can run the helper script in the root directory:
```bash
npm run install:all
```
Alternatively, configure them individually:

#### Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

#### Frontend Setup
```bash
cd frontend
npm install
```

### 2. Running the Application locally

To start both the frontend development server and the FastAPI backend concurrently:
```bash
npm run dev
```

* **FastAPI Backend Server**: runs at [http://localhost:8000](http://localhost:8000)
* **Interactive API Documentation**: runs at [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
* **Frontend Application**: runs at [http://localhost:5173](http://localhost:5173) (or the port defined by Vite)

---

## 🛠️ Code Styling and Standards

We strictly adhere to enterprise-level linting and formatting rules:

### Python (Backend)
* **Formatter**: `black`
* **Linter & Type Checker**: `flake8` and `mypy`
* Run checks using:
  ```bash
  npm run format:py
  npm run lint:py
  ```

### JavaScript/TypeScript (Frontend)
* Run checks using:
  ```bash
  npm run format:js
  npm run lint:js
  ```
