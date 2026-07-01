import re
from datetime import datetime
from typing import List, Set, Optional

from backend.app.knowledge.models import KnowledgeObject, KnowledgeReference

CANONICAL_TYPES = {
    "license",
    "authority",
    "document",
    "timeline",
    "fee",
    "rule",
    "business",
    "notification",
    "penalty",
    "renewal",
    "source",
    "act"
}

SEMVER_REGEX = re.compile(r"^\d+\.\d+\.\d+$")


class KnowledgeValidator:
    def validate(
        self,
        objects: List[KnowledgeObject],
        references: List[KnowledgeReference]
    ) -> List[str]:
        """
        Validates a collection of knowledge objects and references.
        Returns a list of validation error strings. An empty list means validation passed.
        """
        errors: List[str] = []
        seen_ids: Set[str] = set()

        for obj in objects:
            # 1. Duplicate ID check
            if obj.id in seen_ids:
                errors.append(f"Duplicate ID found: '{obj.id}'")
            seen_ids.add(obj.id)

            # 2. Unknown object type check
            if obj.type not in CANONICAL_TYPES:
                errors.append(f"Object '{obj.id}' has unknown type: '{obj.type}'")

            # 3. Invalid version check (SemVer MAJOR.MINOR.PATCH)
            if not SEMVER_REGEX.match(obj.version):
                errors.append(
                    f"Object '{obj.id}' has invalid version format: '{obj.version}'"
                )

            # 4. Date validation
            effective_dt = self._parse_date(obj.effective_date)
            if not effective_dt:
                errors.append(
                    f"Object '{obj.id}' has invalid effective_date format: '{obj.effective_date}'"
                )

            if obj.expiry_date:
                expiry_dt = self._parse_date(obj.expiry_date)
                if not expiry_dt:
                    errors.append(
                        f"Object '{obj.id}' has invalid expiry_date format: '{obj.expiry_date}'"
                    )
                elif effective_dt and expiry_dt < effective_dt:
                    errors.append(
                        f"Object '{obj.id}' expiry_date '{obj.expiry_date}' is before "
                        f"effective_date '{obj.effective_date}'"
                    )

        # 5. Missing references check
        for ref in references:
            if ref.from_id not in seen_ids:
                errors.append(
                    f"Reference from_id '{ref.from_id}' points to a non-existent object ID"
                )
            if ref.to_id not in seen_ids:
                errors.append(
                    f"Reference to_id '{ref.to_id}' points to a non-existent object ID"
                )

        return errors

    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """
        Parses date string using standard formats.
        """
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return None
