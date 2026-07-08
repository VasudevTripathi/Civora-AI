# Compliance Engine Module

## Purpose
The `compliance` module acts as a stateless, public facade that orchestrates the backend evaluation pipeline, exposing a unified interface to generate compliance plans.

## Responsibilities
* **Facade Orchestration**: Chains rule matching, condition evaluation, dependency resolution, eligibility checks, and workflow generation in a sequential pipeline.
* **Fault Isolation**: Wraps execution stages in structured try-except blocks to catch, log, and raise clean application exceptions.
* **Unified Output**: Exposes the `CompliancePlan` structure that consolidates all step and eligibility outputs.

## Public Interfaces
* `ComplianceEngine(knowledge_dir, ...)`
  * `generate_plan(profile: BusinessProfile) -> CompliancePlan`

## Dependencies
* **Internal**: `backend/app/core` (exceptions, settings), `backend/app/services` (loaders), `backend/app/decision` (sub-engines), and `backend/app/compliance/models` (`CompliancePlan`).
* **External**: `pydantic`.

## Forbidden Dependencies
* **API Layer**: Must not import routers or app main entry points.

## Fit in the Overall Architecture
This is the single entry point to the backend decision engine. The API layer (FastAPI) depends directly on `ComplianceEngine` to perform calculations, keeping the API controller thin and logic-free.
