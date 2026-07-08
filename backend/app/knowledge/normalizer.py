import re
import unicodedata
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from backend.app.knowledge.models import KnowledgeObject
from backend.app.knowledge.validator import KnowledgeValidator, CANONICAL_TYPES
from backend.app.knowledge.pipeline import DraftKnowledgeObject


class NormalizationError(Exception):
    """Exception raised when normalization fails or produces an invalid KnowledgeObject."""
    pass


# Standard mappings for common state/federal jurisdictions
JURISDICTION_MAP = {
    "california": "CA",
    "karnataka": "KA",
    "new york": "NY",
    "texas": "TX",
    "maharashtra": "MH",
    "delhi": "DL",
    "india": "IN",
    "united states": "US",
    "usa": "US",
    "federal": "FED"
}

# Authority abbreviations expansion map
AUTHORITY_ABBREVIATIONS = {
    "dept": "Department",
    "dept.": "Department",
    "div": "Division",
    "div.": "Division",
    "govt": "Government",
    "govt.": "Government",
    "sec": "Secretary",
    "sec.": "Secretary",
    "admin": "Administration",
    "admin.": "Administration",
    "auth": "Authority",
    "auth.": "Authority"
}


def slugify(text: str) -> str:
    """Helper to convert string to a clean, lowercase slug with dashes."""
    text = text.lower()
    # Replace non-alphanumeric with a dash
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Collapse multiple dashes and strip boundary dashes
    return re.sub(r"-+", "-", text).strip("-")


def to_snake_case(key: str) -> str:
    """Converts camelCase, dot.separated or space separated names into snake_case."""
    # Replace spaces, dots, dashes with underscore
    s = re.sub(r"[\s\.\-]+", "_", key)
    # Insert underscore between camel case boundaries
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s)
    s = s.lower()
    # Collapse duplicate underscores and strip boundary underscores
    return re.sub(r"_+", "_", s).strip("_")


def normalize_metadata_keys(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively converts all metadata keys to snake_case, ignoring traceability."""
    normalized = {}
    for k, v in metadata.items():
        if k == "traceability":
            normalized[k] = v
            continue
        snake_key = to_snake_case(k)
        if isinstance(v, dict):
            normalized[snake_key] = normalize_metadata_keys(v)
        else:
            normalized[snake_key] = v
    return normalized


def normalize_authority(text: str) -> str:
    """Standardizes spacing, expands common abbreviations, and applies Title Case."""
    # Strip spaces
    text = " ".join(text.split())
    words = text.split()
    normalized_words = []
    
    for word in words:
        lookup = word.lower().rstrip(".,")
        replacement = AUTHORITY_ABBREVIATIONS.get(lookup)
        if replacement:
            normalized_words.append(replacement)
        else:
            normalized_words.append(word)
            
    result = " ".join(normalized_words)
    return result.title()


def normalize_title(title: str) -> str:
    """Cleans title spacing and strips trailing/leading format characters."""
    title = " ".join(title.split())
    return title.strip(" :-.,;")


def normalize_description_text(text: str) -> str:
    """Normalizes whitespace on a line-by-line basis to retain paragraphs (new lines)."""
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    cleaned_lines = []
    
    for line in lines:
        cleaned_lines.append(" ".join(line.split()))
        
    # Collapse consecutive blank lines
    result_lines = []
    for line in cleaned_lines:
        if line == "":
            if not result_lines or result_lines[-1] != "":
                result_lines.append("")
        else:
            result_lines.append(line)
            
    while result_lines and result_lines[0] == "":
        result_lines.pop(0)
    while result_lines and result_lines[-1] == "":
        result_lines.pop()
        
    return "\n".join(result_lines)


def normalize_version(version: str) -> str:
    """Coerces versions into standard SemVer X.Y.Z formatting."""
    version = version.strip().lower()
    if version.startswith("v"):
        version = version[1:]
        
    match = re.match(r"^(\d+)(?:\.(\d+))?(?:\.(\d+))?$", version)
    if match:
        major = match.group(1)
        minor = match.group(2) or "0"
        patch = match.group(3) or "0"
        return f"{major}.{minor}.{patch}"
        
    return "1.0.0"


def normalize_date(date_str: str) -> str:
    """Converts various date formats into YYYY-MM-DD standard format."""
    date_str = date_str.strip()
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S"
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    # Try parsing iso format with timezone offsets
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        pass
        
    raise ValueError(f"Unsupported date format: '{date_str}'")


class KnowledgeNormalizer:
    """
    Translates non-canonical DraftKnowledgeObjects into fully normalized
    and valid canonical KnowledgeObjects.
    """
    def __init__(self, validator: Optional[KnowledgeValidator] = None):
        self.validator = validator or KnowledgeValidator()

    def normalize(
        self,
        draft: DraftKnowledgeObject,
        type: Optional[str] = None,
        jurisdiction: Optional[str] = None,
        authority: Optional[str] = None,
        version: Optional[str] = None,
        effective_date: Optional[str] = None,
        expiry_date: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> KnowledgeObject:
        """
        Transforms a DraftKnowledgeObject into a validated KnowledgeObject.

        Raises:
            NormalizationError: If type is invalid, dates are malformed,
                                or the resulting object fails validation.
        """
        # 1. Resolve type
        raw_type = type or draft.metadata.get("type") or "document"
        resolved_type = raw_type.strip().lower()
        
        # Map common plurals to singular canonical types
        plural_to_singular = {
            "licenses": "license",
            "authorities": "authority",
            "documents": "document",
            "timelines": "timeline",
            "fees": "fee",
            "rules": "rule",
            "businesses": "business",
            "notifications": "notification",
            "penalties": "penalty",
            "renewals": "renewal",
            "sources": "source",
            "acts": "act"
        }
        resolved_type = plural_to_singular.get(resolved_type, resolved_type)
        if resolved_type not in CANONICAL_TYPES:
            raise NormalizationError(f"Unsupported canonical type: '{resolved_type}'")

        # 2. Resolve jurisdiction
        raw_jurisdiction = jurisdiction or draft.metadata.get("jurisdiction") or "FED"
        clean_jur = raw_jurisdiction.strip().lower()
        norm_jurisdiction = JURISDICTION_MAP.get(clean_jur, raw_jurisdiction.strip().upper())

        # 3. Resolve authority
        raw_authority = authority or draft.metadata.get("authority") or "Unknown Authority"
        norm_authority = normalize_authority(raw_authority)

        # 4. Resolve version
        raw_version = version or draft.metadata.get("version") or "1.0.0"
        norm_version = normalize_version(raw_version)

        # 5. Resolve dates
        raw_effective = effective_date or draft.metadata.get("effective_date") or datetime.now().strftime("%Y-%m-%d")
        try:
            norm_effective = normalize_date(raw_effective)
        except ValueError as e:
            raise NormalizationError(f"Invalid effective_date format: {e}")

        norm_expiry = None
        raw_expiry = expiry_date or draft.metadata.get("expiry_date")
        if raw_expiry:
            try:
                norm_expiry = normalize_date(raw_expiry)
            except ValueError as e:
                raise NormalizationError(f"Invalid expiry_date format: {e}")

        # 6. Resolve tags
        raw_tags = tags or draft.metadata.get("tags") or []
        if isinstance(raw_tags, str):
            raw_tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        norm_tags = [t.strip().lower() for t in raw_tags if t.strip()]

        # 7. Normalize titles and raw text (description)
        norm_title = normalize_title(draft.section_title)
        norm_description = normalize_description_text(draft.raw_text)

        # 8. Deterministic ID generation
        slug_type = slugify(resolved_type)
        slug_jur = slugify(norm_jurisdiction)
        slug_auth = slugify(norm_authority)
        slug_sec = slugify(draft.section_number)
        generated_id = "-".join([parts for parts in [slug_type, slug_jur, slug_auth, slug_sec] if parts])
        if not generated_id:
            generated_id = f"object-{abs(hash(norm_title))}"

        # 9. Clean custom metadata and inject traceability
        cleaned_custom_metadata = normalize_metadata_keys(draft.metadata)
        # Remove core fields that were resolved/normalized from the custom metadata dict to keep it clean
        for field in ["type", "jurisdiction", "authority", "version", "effective_date", "expiry_date", "tags"]:
            cleaned_custom_metadata.pop(field, None)
            
        cleaned_custom_metadata["traceability"] = {
            "original_source": draft.source_document,
            "original_section_title": draft.section_title,
            "original_section_number": draft.section_number,
            "original_page": draft.page_number,
            "original_metadata": draft.metadata.copy()
        }

        # 10. Construct canonical KnowledgeObject
        obj = KnowledgeObject(
            id=generated_id,
            type=resolved_type,
            jurisdiction=norm_jurisdiction,
            authority=norm_authority,
            title=norm_title,
            description=norm_description,
            effective_date=norm_effective,
            expiry_date=norm_expiry,
            version=norm_version,
            source=draft.source_document,
            tags=norm_tags,
            metadata=cleaned_custom_metadata
        )

        # 11. Validate against validator
        validation_errors = self.validator.validate([obj], [])
        if validation_errors:
            raise NormalizationError(f"Validation failed for normalized object: {validation_errors}")

        return obj
