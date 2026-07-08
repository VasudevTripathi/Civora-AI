import time
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from loguru import logger

from backend.app.knowledge.models import KnowledgeObject
from backend.app.knowledge.pipeline import DraftKnowledgeObject
from backend.app.knowledge.normalizer import KnowledgeNormalizer, NormalizationError
from backend.app.knowledge.validator import KnowledgeValidator
from backend.app.knowledge.repository import KnowledgeRepository


class IngestionResult(BaseModel):
    """
    Model representing the outcome of a batch knowledge ingestion run.
    """
    processed_objects: int
    successful_objects: List[str]  # IDs of successfully stored KnowledgeObjects
    failed_objects: List[str]      # Titles or identifiers of failed draft objects
    validation_errors: List[Dict[str, Any]] = Field(default_factory=list)  # Errors by section
    processing_time_ms: float
    summary: str


class KnowledgeIngestionOrchestrator:
    """
    Orchestrates the ingestion workflow for a collection of DraftKnowledgeObjects.
    Coordinates between KnowledgeNormalizer, KnowledgeValidator, and KnowledgeRepository,
    providing fault isolation so a single malformed draft doesn't abort the entire batch.
    """
    def __init__(
        self,
        normalizer: Optional[KnowledgeNormalizer] = None,
        validator: Optional[KnowledgeValidator] = None,
        repository: Optional[KnowledgeRepository] = None
    ):
        self.normalizer = normalizer or KnowledgeNormalizer()
        self.validator = validator or KnowledgeValidator()
        self.repository = repository or KnowledgeRepository()

    def ingest(
        self,
        drafts: List[DraftKnowledgeObject],
        **normalization_overrides
    ) -> IngestionResult:
        """
        Ingests a batch of DraftKnowledgeObjects by normalizing, validating, and storing them.
        
        Args:
            drafts: List of DraftKnowledgeObjects to process.
            normalization_overrides: Default value overrides to pass to the normalizer 
                                     (e.g., type, jurisdiction, authority, version, etc.).
        
        Returns:
            IngestionResult: Summary of successful and failed ingests, error details, and timing.
        """
        start_time = time.perf_counter()
        total_drafts = len(drafts)
        
        logger.info(
            "Starting batch ingestion orchestrator process",
            extra={"batch_size": total_drafts, "overrides": normalization_overrides}
        )

        successful_objects: List[str] = []
        failed_objects: List[str] = []
        validation_errors: List[Dict[str, Any]] = []

        for idx, draft in enumerate(drafts):
            draft_identifier = draft.section_title or f"Draft #{idx+1}"
            try:
                # 1. Normalize draft to a candidate KnowledgeObject
                normalized_obj = self.normalizer.normalize(draft, **normalization_overrides)

                # 2. Perform explicit validation checks
                errors = self.validator.validate([normalized_obj], [])
                if errors:
                    # Log validation errors and isolate
                    logger.warning(
                        "Validation failed for draft object during orchestration",
                        extra={"section_title": draft_identifier, "errors": errors}
                    )
                    failed_objects.append(draft_identifier)
                    validation_errors.append({
                        "section_title": draft_identifier,
                        "errors": errors
                    })
                    continue

                # 3. Store the valid KnowledgeObject in the repository
                try:
                    self.repository.store(normalized_obj)
                    successful_objects.append(normalized_obj.id)
                    logger.debug(
                        "Stored KnowledgeObject successfully",
                        extra={"id": normalized_obj.id, "section_title": draft_identifier}
                    )
                except Exception as e:
                    # Isolate repository write errors (e.g. disk write failure)
                    logger.error(
                        "Failed to store normalized object in repository",
                        extra={"section_title": draft_identifier, "error": str(e)}
                    )
                    failed_objects.append(draft_identifier)
                    validation_errors.append({
                        "section_title": draft_identifier,
                        "errors": [f"Storage failure: {str(e)}"]
                    })

            except NormalizationError as ne:
                # Catch normalizer errors (e.g. unsupported canonical types, malformed dates)
                logger.warning(
                    "Normalization failed for draft object",
                    extra={"section_title": draft_identifier, "error": str(ne)}
                )
                failed_objects.append(draft_identifier)
                validation_errors.append({
                    "section_title": draft_identifier,
                    "errors": [str(ne)]
                })
            except Exception as e:
                # Catch any other unexpected parsing or code errors
                logger.error(
                    "Unexpected processing error during orchestration",
                    extra={"section_title": draft_identifier, "error": str(e)}
                )
                failed_objects.append(draft_identifier)
                validation_errors.append({
                    "section_title": draft_identifier,
                    "errors": [f"Unexpected error: {str(e)}"]
                })

        end_time = time.perf_counter()
        processing_time_ms = round((end_time - start_time) * 1000, 2)
        
        success_count = len(successful_objects)
        failed_count = len(failed_objects)
        
        summary = (
            f"Ingested {success_count}/{total_drafts} objects successfully "
            f"in {processing_time_ms}ms. {failed_count} failed."
        )

        logger.info(
            "Batch ingestion orchestrator process completed",
            extra={
                "total_processed": total_drafts,
                "success_count": success_count,
                "failed_count": failed_count,
                "processing_time_ms": processing_time_ms
            }
        )

        return IngestionResult(
            processed_objects=total_drafts,
            successful_objects=successful_objects,
            failed_objects=failed_objects,
            validation_errors=validation_errors,
            processing_time_ms=processing_time_ms,
            summary=summary
        )
