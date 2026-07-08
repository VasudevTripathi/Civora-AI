# Knowledge Engineering Module

## Purpose
The `knowledge` module manages the extraction, sanitization, parsing, normalization, validation, and storage of regulatory requirements from raw source formats (e.g. PDFs) into canonical JSON schemas.

## Responsibilities
* **PDF Ingestion**: Parses PDFs page-by-page (`pdf_parser.py`) and cleans metadata and page layout text (`text_cleaner.py`).
* **Section Extraction**: Segment text streams into distinct, hierarchically indexed draft sections (`section_extractor.py`).
* **Normalization**: Coerces dates, jurisdictions, authorities, and tags into canonical snake_case formats (`normalizer.py`).
* **Validation**: Validates normalized objects against strict schema files (`validator.py`).
* **Storage & Indexing**: Persists structured objects locally and manages file reads/writes (`repository.py`).
* **Ingestion Orchestration**: Controls the execution pipeline, guaranteeing fault isolation and batch resilience (`orchestrator.py` & `pipeline.py`).

## Public Interfaces
* `KnowledgeIngestionOrchestrator(knowledge_dir)`
  * `ingest(draft_objects: List[DraftKnowledgeObject]) -> IngestionResult`
* `KnowledgeNormalizer(validator)`
  * `normalize(draft: DraftKnowledgeObject) -> KnowledgeObject`
* `KnowledgeRepository(knowledge_dir)`
  * `store(obj: KnowledgeObject) -> None`
  * `get_by_id(obj_type: str, obj_id: str) -> Optional[Dict[str, Any]]`

## Dependencies
* **Internal**: `backend/app/core` (exceptions, logging) and `backend/app/services` (loaders).
* **External**: `pypdf`, `pydantic`.

## Forbidden Dependencies
* **Decision Engine**: Must not depend on the rule engine, condition evaluator, or eligibility engine.
* **Compliance Facade**: Must not import the compliance engine or models.
* **API Layer**: Must not import API endpoints.

## Fit in the Overall Architecture
This module sits at the bottom of the business layers, serving as the source-of-truth knowledge base. Outputs from this layer are consumed by loaders to feed facts and rules into the Decision layer.
