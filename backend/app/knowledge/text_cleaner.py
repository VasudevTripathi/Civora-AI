import re
import unicodedata
from typing import List, Dict, Any, Set


class TextCleaner:
    """
    Cleans extracted text deterministically:
    - Unicode normalization (NFKC)
    - Line ending normalization
    - Redundant whitespace removal
    - Automatic header and footer removal
    - Page number line elimination
    """
    def __init__(self):
        # Regular expressions for common page number structures at the top or bottom of a page
        self.page_number_patterns = [
            re.compile(r"^\s*\d+\s*$"),  # Just digits (e.g. "12")
            re.compile(r"^\s*page\s+\d+\s*$", re.IGNORECASE),  # "Page 12"
            re.compile(r"^\s*page\s+\d+\s+of\s+\d+\s*$", re.IGNORECASE),  # "Page 12 of 34"
            re.compile(r"^\s*-\s*\d+\s*-\s*$"),  # "- 12 -"
            re.compile(r"^\s*\[\s*\d+\s*\]\s*$")  # "[12]"
        ]

    def normalize_text(self, text: str) -> str:
        """
        Cleans whitespaces and line endings, and normalizes Unicode representation.
        """
        if not text:
            return ""

        # Normalize Unicode (compatibility decomposition NFKC)
        text = unicodedata.normalize("NFKC", text)

        # Normalize line endings to LF (\n)
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            # Strip trailing/leading spaces and collapse multiple spaces/tabs into one
            cleaned_line = " ".join(line.split())
            cleaned_lines.append(cleaned_line)

        # Collapse multiple empty lines: at most one consecutive empty line (to separate paragraphs)
        result_lines = []
        for line in cleaned_lines:
            if line == "":
                if not result_lines or result_lines[-1] != "":
                    result_lines.append("")
            else:
                result_lines.append(line)

        # Strip starting/ending blank lines
        while result_lines and result_lines[0] == "":
            result_lines.pop(0)
        while result_lines and result_lines[-1] == "":
            result_lines.pop()

        return "\n".join(result_lines)

    def is_page_number_line(self, line: str) -> bool:
        """
        Checks if a line of text matches common page number patterns.
        """
        line_stripped = line.strip()
        for pattern in self.page_number_patterns:
            if pattern.match(line_stripped):
                return True
        return False

    def remove_headers_footers(self, pages_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detects repeating headers/footers in multi-page documents and filters them,
        along with any page number lines.

        Args:
            pages_data: List of dicts with keys "page_number" (int) and "text" (str)

        Returns:
            List[Dict[str, Any]]: Cleaned page texts
        """
        if not pages_data:
            return []

        num_pages = len(pages_data)

        # First, pre-normalize and split the page text into lines
        pages_lines: List[List[str]] = []
        for page in pages_data:
            norm_text = self.normalize_text(page["text"])
            pages_lines.append(norm_text.split("\n") if norm_text else [])

        header_candidates: Set[str] = set()
        footer_candidates: Set[str] = set()

        # We can detect repeating headers/footers if there are at least 2 pages.
        if num_pages >= 2:
            first_line_counts: Dict[str, int] = {}
            second_line_counts: Dict[str, int] = {}
            last_line_counts: Dict[str, int] = {}
            second_last_line_counts: Dict[str, int] = {}

            for lines in pages_lines:
                if len(lines) > 0 and lines[0].strip():
                    first = lines[0].strip()
                    first_line_counts[first] = first_line_counts.get(first, 0) + 1
                if len(lines) > 1 and lines[1].strip():
                    second = lines[1].strip()
                    second_line_counts[second] = second_line_counts.get(second, 0) + 1
                if len(lines) > 0 and lines[-1].strip():
                    last = lines[-1].strip()
                    last_line_counts[last] = last_line_counts.get(last, 0) + 1
                if len(lines) > 1 and lines[-2].strip():
                    second_last = lines[-2].strip()
                    second_last_line_counts[second_last] = second_last_line_counts.get(second_last, 0) + 1

            # A header or footer must repeat on at least max(2, num_pages // 2) pages
            threshold = max(2, num_pages // 2)

            for line, count in first_line_counts.items():
                if count >= threshold:
                    header_candidates.add(line)
            for line, count in second_line_counts.items():
                if count >= threshold:
                    header_candidates.add(line)
            for line, count in last_line_counts.items():
                if count >= threshold:
                    footer_candidates.add(line)
            for line, count in second_last_line_counts.items():
                if count >= threshold:
                    footer_candidates.add(line)

        cleaned_pages = []
        for idx, page in enumerate(pages_data):
            lines = pages_lines[idx]
            if not lines:
                cleaned_pages.append({
                    "page_number": page["page_number"],
                    "text": ""
                })
                continue

            # Process from the start (top lines)
            start_idx = 0
            end_idx = len(lines)

            # Look at up to top 2 lines for headers / page numbers
            while start_idx < end_idx and start_idx < 2:
                line = lines[start_idx].strip()
                if line in header_candidates or self.is_page_number_line(line):
                    start_idx += 1
                else:
                    break

            # Look at up to bottom 2 lines for footers / page numbers
            while end_idx > start_idx and end_idx > len(lines) - 2:
                line = lines[end_idx - 1].strip()
                if line in footer_candidates or self.is_page_number_line(line):
                    end_idx -= 1
                else:
                    break

            cleaned_lines = lines[start_idx:end_idx]
            cleaned_text = "\n".join(cleaned_lines)

            # Re-normalize to ensure there are no lingering leading/trailing empty lines
            cleaned_pages.append({
                "page_number": page["page_number"],
                "text": self.normalize_text(cleaned_text)
            })

        return cleaned_pages
