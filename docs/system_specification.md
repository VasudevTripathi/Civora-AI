# Civora AI — System & Product Specification Document

This document serves as the formal specification and product definition for **Civora AI**, an AI-powered Government Compliance Operating System.

---

## 1. Problem Statement

Starting and operating a business requires navigating a complex web of local, state, and federal regulatory procedures. Entrepreneurs face several critical roadblocks:
* **Information Fragmentation**: Compliance guidelines, fee schedules, and required documentation are spread across numerous disparate government portals (e.g., Secretary of State, Department of Revenue, IRS).
* **Legal and Regulatory Complexity**: Statutes are written in dense legal terminology, leading to high errors in filing, delays in approval, and costly compliance violations.
* **Prohibitive Advisory Costs**: Professional legal and accounting compliance services are prohibitively expensive for early-stage startup founders and micro-businesses.
* **Lack of Ongoing Compliance Tracking**: Once a business is registered, founders struggle to track annual report filings, tax deadlines, and license renewals, risking dissolution or fines.

---

## 2. Objectives

The primary goals of Civora AI are:
* **Democratize Business Registration**: Provide clear, jargon-free, and personalized step-by-step guidance for incorporating and licensing businesses.
* **Automate Document Generation**: Generate ready-to-file incorporation documents, operating agreements, and compliance forms based on simple interactive user inputs.
* **Ensure Multi-Jurisdictional Coverage**: Map and abstract the specific regulatory compliance pathways across different state and local jurisdictions.
* **Deliver AI-Driven Compliance Advisory**: Offer an intelligent, RAG-enabled chatbot helper capable of answering regulatory and compliance queries with high accuracy and citation of source materials.
* **Prevent Regulatory Drift**: Proactively track, alert, and manage deadlines for annual filings, tax filings, and license renewals.

---

## 3. Target Users

Civora AI is engineered for:
* **First-Time Entrepreneurs & Small Business Owners**: Individuals with limited legal/financial background who require end-to-end guidance.
* **Side-Hustlers & Freelancers**: Solopreneurs transitioning to formal LLC or corporate business structures.
* **Foreign Founders**: International entrepreneurs seeking to establish US-based entities (e.g., Delaware/Wyoming LLCs) without physical presence.
* **Startup Incubators & Accelerators**: Program managers who want to streamline the legal setup phase for cohort companies.

---

## 4. Scope

### In-Scope (Initial Release)
1. **Interactive Incorporation Wizard**: Dynamic questionnaires that recommend the optimal entity type (LLC, S-Corp, C-Corp) and state of incorporation.
2. **AI Compliance Assistant**: A conversational AI interface backed by Retrieval-Augmented Generation (RAG) that answers incorporation and license queries.
3. **Structured Document Assembly**: Automated generation of Articles of Organization, Operating Agreements, and EIN applications (Form SS-4).
4. **Jurisdiction Mapping**: Local database mapping the registration steps, filing fees, and processing times for key initial states (e.g., Delaware, Wyoming, California, Texas).
5. **Dashboard Compliance Calendar**: A centralized dashboard tracking key recurring compliance deadlines based on business entity parameters.

### Out-of-Scope (Excluded from Current Phase)
1. **Direct API Filing Submission**: Automatic submission of filings directly to Secretary of State APIs (due to state-level authentication and API availability limits).
2. **Legal and Tax Representation**: Provision of active legal counsel or accounting advice (Civora AI acts as an operational system, not a law firm or CPA).
3. **Foreign Registered Agent Services**: Acting directly as a registered agent (this will rely on third-party service provider integrations).

---

## 5. Future Scope

* **Automatic State Filing Integrations**: Direct integration with Secretary of State portals via robotic process automation (RPA) or public APIs to file documents on behalf of users.
* **Automated Corporate Actions**: Workflows for processing equity grants, stock option issuances, board consents, and cap table updates.
* **Multi-State Tax Compliance**: Calculating and filing state sales tax, franchise tax, and local business taxes directly within the platform.
* **Global Entity Expansion**: Extending scope beyond the US to encompass international hubs (e.g., UK Ltd, Canadian Corporations, Singapore Private Limited Companies).
* **Predictive Regulatory Intelligence**: AI models that monitor state and federal legislative changes and notify founders if upcoming laws affect their operating compliance.

---

## 6. Functional Requirements

### 6.1 Onboarding & Profile Setup
* **FR-1.1**: The system must allow users to register, authenticate (via email/password or OAuth2), and manage profile details securely.
* **FR-1.2**: The system must guide users through a structured onboarding flow to capture industry type, target state, estimated employee count, and business model.

### 6.2 Entity Recommendation Engine
* **FR-2.1**: The system must analyze user responses (e.g., funding goals, liability concerns) to recommend a business entity structure (e.g., C-Corp vs. LLC).
* **FR-2.2**: The system must provide a side-by-side cost and feature comparison of incorporation states.

### 6.3 Compliance Document Assembly
* **FR-3.1**: The system must construct customizable templates for Articles of Organization, bylaws, and operating agreements based on state regulations.
* **FR-3.2**: The system must export generated documents in PDF and DOCX formats.

### 6.4 AI RAG Chat Assistant
* **FR-4.1**: The system must search and retrieve relevant context from verified state compliance documents stored in the vector database.
* **FR-4.2**: The system must generate natural language explanations citing source law or government portals.
* **FR-4.3**: The system must sanitize user inputs to reject prompt injection and block non-compliance-related queries.

### 6.5 Deadline & Reminder Engine
* **FR-5.1**: The system must auto-populate the compliance calendar with annual reports, franchise tax, and filing deadlines based on entity type and state.
* **FR-5.2**: The system must trigger email/dashboard notifications before compliance deadlines.

---

## 7. Non-Functional Requirements

### 7.1 Security & Data Privacy
* **NFR-1.1 (Encryption)**: All sensitive user data (EIN, SSN, home addresses) must be encrypted at rest using AES-256 and in transit using TLS 1.3.
* **NFR-1.2 (Access Control)**: Implement Role-Based Access Control (RBAC) to ensure users can only view entities they own or are authorized to manage.
* **NFR-1.3 (Compliance)**: Follow SOC2 type II guidelines for data governance and handling of PII.

### 7.2 Performance & Latency
* **NFR-2.1 (API Response)**: Core API endpoints must respond within < 200ms under normal load (excluding heavy AI generation).
* **NFR-2.2 (AI Latency)**: RAG chat responses must stream to the client or return in < 3 seconds using asynchronous chunk-retrieval pipelines.

### 7.3 Scalability & Availability
* **NFR-3.1 (Uptime)**: The system must target a 99.9% uptime availability, excluding scheduled maintenance.
* **NFR-3.2 (Elasticity)**: The architecture must run in containers (e.g., Docker) allowing horizontal scaling of stateless API nodes and Celery workers during high-traffic tax/filing seasons.

### 7.4 Maintainability
* **NFR-4.1 (Clean Code)**: Strictly adhere to Clean Architecture standards, separating external database libraries from business rules.
* **NFR-4.2 (Test Coverage)**: Maintain a minimum of 80% test coverage across core business services and schema validation layers.

---

## 8. Technology Stack

* **Frontend**: React.js with TypeScript, TailwindCSS for styling, and Vite as the build tool.
* **Backend Framework**: Python FastAPI for high-performance, asynchronous REST API serving and automatic OpenAPI specification generation.
* **Database (Relational)**: PostgreSQL for transactional data (Users, Companies, Compliance Calendars).
* **Database (Vector)**: Qdrant for semantic search vector embeddings.
* **ORM/ODM**: SQLModel (unifying SQLAlchemy and Pydantic) for typed data access.
* **AI Engine**: Google Gemini API via the official `google-genai` Python SDK.
* **Task Queue & Broker**: Celery with Redis for asynchronous document generation and background email reminder jobs.
* **Testing Suite**: `pytest` and `pytest-asyncio` for unit and integration testing.

---

## 9. System Architecture

Civora AI is designed on a **Decoupled Service-Oriented Architecture** using a clean, layered folder structure:

```
                  +--------------------------------+
                  |      Frontend (React UI)       |
                  +--------------------------------+
                                  |
                                  | HTTPS (JSON)
                                  v
                  +--------------------------------+
                  |  FastAPI Presentation Layer    |
                  +--------------------------------+
                     |                          |
                     | Direct                   | Async Tasks
                     v                          v
  +---------------------------+       +---------------------+
  |   Business Service Layer  |       | Celery Task Worker  |
  +---------------------------+       +---------------------+
     |                     |                     |
     v                     v                     v
+------------+       +------------+        +------------+
| Repository |       | AI Service |        | PDF/Docx   |
|   Layer    |       |   (RAG)    |        | Generator  |
+------------+       +------------+        +------------+
     |                  |       |                |
     v SQL              v API   v Query          | Write to Disk
+------------+       +--------+ +----------+     v
| PostgreSQL |       | Gemini | | Qdrant   |   +------------+
|  Database  |       |  API   | | Vector DB|   | File Store |
+------------+       +--------+ +----------+   +------------+
```

### Architectural Principles
1. **Single Responsibility**: Each endpoint, service, and repository performs one business action.
2. **Dependency Inversion**: High-level modules do not depend on low-level database libraries; both depend on abstractions (interfaces).
3. **Event-Driven Asynchrony**: Any operation that takes longer than 500ms (e.g., PDF generation, RAG document indexing, outbound email dispatching) is offloaded to the Redis broker and executed asynchronously by Celery workers to keep the API server responsive.
