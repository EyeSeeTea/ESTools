# reorder_sections_use_case.py
#
# Source data fetched via:
# https://server/api/sections?filter=dataSet.id:in:[NnhyjiUbcJN]&fields=*&paging=false

from __future__ import annotations

from typing import Any, Tuple

from file_utils import read_json, write_json


class ReorderSectionsUseCase:
    """
    Sort sections alphabetically and rewrite sortOrder starting at 1.
    Input: JSON list of sections, or an object with a 'sections' array.
    Output: JSON in the same shape, written under output/.
    """

    def __init__(
        self,
        input_path: str,
        output_path: str,
    ):
        self.input_path = input_path
        self.output_path = output_path

    @staticmethod
    def _extract_sections(payload: Any) -> Tuple[list[dict], Any, bool]:
        """
        Returns (sections, container, has_container)
        - If payload is a dict with 'sections', container is the dict.
        - If payload is already a list, container is None.
        """
        if isinstance(payload, dict) and "sections" in payload:
            sections = payload.get("sections")
            container = payload
            has_container = True
        else:
            sections = payload
            container = None
            has_container = False

        if not isinstance(sections, list):
            raise ValueError("Input JSON must be a list of sections or an object with a 'sections' array.")

        return sections, container, has_container

    @staticmethod
    def _sort_key(section: dict) -> Tuple[str, str]:
        name = (section.get("name") or section.get("displayName") or "").strip().lower()
        fallback = (section.get("id") or "").strip()
        return name, fallback

    def execute(self):
        payload = read_json(self.input_path)
        sections, container, has_container = self._extract_sections(payload)

        print(f"Loaded {len(sections)} sections from input/{self.input_path}")

        sorted_sections = sorted(sections, key=self._sort_key)
        for idx, section in enumerate(sorted_sections, start=1):
            section["sortOrder"] = idx

        if has_container:
            container["sections"] = sorted_sections
            output_payload = container
        else:
            output_payload = sorted_sections

        final_path = write_json(self.output_path, output_payload, indent=2)
        print(f"Sorted sections written to: {final_path}")
