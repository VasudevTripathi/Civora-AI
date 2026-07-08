# Domain Models Module

## Purpose
The `domain` module defines the core business and regulatory vocabulary used throughout Civora AI as strongly typed Pydantic models.

## Responsibilities
* **Regulatory Definitions**: Models authorities, licenses, permits, tax requirements, and legal acts.
* **Operational Definitions**: Models business attributes, fees, deadlines, penalties, and compliance tasks.
* **Data Decoupling**: Models use ID-based reference linking instead of direct memory graph-nesting.

## Public Interfaces
Pydantic model definitions:
* `Jurisdiction`
* `Business`
* `Authority`
* `License`
* `Permit`
* `Fee`
* `Deadline`
* `Penalty`
* `Tax`
* `ComplianceTask`

## Dependencies
* **Internal**: `backend/app/core` (settings, exceptions).
* **External**: `pydantic`.

## Forbidden Dependencies
This is a low-level leaf package:
* Must not import from `backend/app/knowledge/`.
* Must not import from `backend/app/decision/`.
* Must not import from `backend/app/compliance/`.
* Must not import from `backend/app/services/`.

## Fit in the Overall Architecture
This layer provides the shared business vocabulary for the repository. The knowledge normalizer, policy loaders, rule engines, and API layers all import and share these models.
