import re
from typing import List, Dict, Any, Tuple, Optional


class SectionExtractor:
    """
    Strips and segments pages of a document into logical sections using deterministic heuristics.
    Supports:
    - Article I / Article 1
    - Section 3.1 / Section II / Section A
    - Chapter 5 / Chapter II
    - Roman numerals (e.g., I. Introduction)
    - Hierarchical numbering (e.g., 3.1.2 Scope)
    """
    def __init__(self):
        # Deterministic regular expressions for section headers
        self.patterns = [
            # 1. Article: "Article I", "ARTICLE 1", "Article II - Definitions"
            {
                "name": "article",
                "regex": re.compile(
                    r"^\s*(Article|ARTICLE)\s+([IVXLCDM\d]+)(?:\b|:|-|\.|\s+)(.*)$",
                    re.IGNORECASE
                )
            },
            # 2. Section: "Section 3.1", "SECTION II", "Section A - Scope"
            {
                "name": "section",
                "regex": re.compile(
                    r"^\s*(Section|SECTION|Sec\.)\s+(\d+(?:\.\d+)*|[IVXLCDM\d]+|[A-Z])(?:\b|:|-|\.|\s+)(.*)$",
                    re.IGNORECASE
                )
            },
            # 3. Chapter: "Chapter 5", "CHAPTER II"
            {
                "name": "chapter",
                "regex": re.compile(
                    r"^\s*(Chapter|CHAPTER)\s+([IVXLCDM\d]+)(?:\b|:|-|\.|\s+)(.*)$",
                    re.IGNORECASE
                )
            },
            # 4. Roman Numeral Header: "I. INTRODUCTION", "IV. GENERAL PROVISIONS"
            {
                "name": "roman",
                "regex": re.compile(
                    r"^\s*([IVXLCDM]+)\.\s+([A-Z].*)$"
                )
            },
            # 5. Hierarchical numbered section: "3.1.2 Scope of Application" (excludes plain lists like "1. Item")
            {
                "name": "hierarchical",
                "regex": re.compile(
                    r"^\s*(\d+(?:\.\d+)+)\s+([A-Z].*)$"
                )
            }
        ]

    def _match_header(self, line: str) -> Optional[Tuple[str, str]]:
        """
        Attempts to match a line against all heading patterns.
        Returns a tuple of (section_number, section_title) if a match is found, else None.
        """
        stripped_line = line.strip()
        for pattern in self.patterns:
            match = pattern["regex"].match(stripped_line)
            if match:
                if pattern["name"] in ("article", "section", "chapter"):
                    keyword = match.group(1)
                    num = match.group(2)
                    suffix = match.group(3).strip(" :-.")
                    
                    section_number = num
                    if suffix:
                        section_title = f"{keyword} {num}: {suffix}"
                    else:
                        section_title = f"{keyword} {num}"
                    return section_number, section_title
                
                elif pattern["name"] == "roman":
                    num = match.group(1)
                    suffix = match.group(2).strip(" :-.")
                    section_number = num
                    section_title = f"{num}. {suffix}"
                    return section_number, section_title
                    
                elif pattern["name"] == "hierarchical":
                    num = match.group(1)
                    suffix = match.group(2).strip(" :-.")
                    section_number = num
                    section_title = f"{num} {suffix}"
                    return section_number, section_title

        return None

    def extract_sections(self, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Processes a list of page dicts, splitting text into logical sections.
        Returns a list of dicts:
            [
                {
                    "section_title": "Preamble",
                    "section_number": "0",
                    "raw_text": "...",
                    "page_number": 1
                },
                ...
            ]
        """
        if not pages_data:
            return []

        # Flatten lines, tracking their source page number
        flat_lines: List[Tuple[str, int]] = []
        for page in pages_data:
            page_num = page["page_number"]
            text = page["text"]
            lines = text.split("\n") if text else []
            for line in lines:
                flat_lines.append((line, page_num))

        sections: List[Dict[str, Any]] = []

        current_title = "Preamble"
        current_number = "0"
        current_page = pages_data[0]["page_number"]
        current_lines: List[str] = []

        for line, page_num in flat_lines:
            header_match = self._match_header(line)
            if header_match:
                # Save previous section if it has content or is not the initial empty preamble
                raw_text = "\n".join(current_lines).strip()
                if raw_text or len(sections) > 0 or current_title != "Preamble":
                    sections.append({
                        "section_title": current_title,
                        "section_number": current_number,
                        "raw_text": raw_text,
                        "page_number": current_page
                    })
                
                # Start new section
                current_number, current_title = header_match
                current_page = page_num
                current_lines = []
            else:
                current_lines.append(line)

        # Append last section
        raw_text = "\n".join(current_lines).strip()
        if raw_text or len(sections) > 0 or current_title != "Preamble":
            sections.append({
                "section_title": current_title,
                "section_number": current_number,
                "raw_text": raw_text,
                "page_number": current_page
            })

        return sections
