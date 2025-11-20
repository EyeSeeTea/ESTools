# create_missing_values_use_case.py

from typing import Optional, Tuple

import requests

from dhis_utils import dhis_get
from file_utils import read_csv, escape_sql_literal, write_text


# Numeric ID of the attribute in trackedentityattributevalue table
TRACKED_ENTITY_ATTRIBUTE_ID = 11364749
# Optional: UID of the attribute, for documentation/reference
TRACKED_ENTITY_ATTRIBUTE_UID = "Nf2VUgxqhmi"


class CreateMissingValuesUseCase:
    """
    Use case to generate INSERT statements for missing attribute values
    based on existing TEI metadata (created, lastUpdated, storedBy).
    """

    def __init__(
        self,
        base_url: str,
        jsessionid: str,
        input_path: str,
        output_path: str,
    ):
        """
        Args:
            base_url: DHIS2 base URL (without trailing slash).
            jsessionid: JSESSIONID cookie value.
            input_path: CSV file name (relative to 'input/' folder).
            output_path: Output SQL file name (relative to 'output/' folder).
        """
        self.base_url = base_url
        self.jsessionid = jsessionid
        self.input_path = input_path
        self.output_path = output_path

    @staticmethod
    def normalize_timestamp(raw_timestamp: Optional[str]) -> Optional[str]:
        """
        Normalize a DHIS2 timestamp into a format that Postgres accepts.
        Example:
            '2025-07-18T13:48:12.502' -> '2025-07-18 13:48:12.502'
        """
        if not raw_timestamp:
            return None

        timestamp = raw_timestamp.rstrip("Z")
        timestamp = timestamp.replace("T", " ")
        return timestamp

    @classmethod
    def _get_attribute_template_from_tei_level(
        cls,
        tei_data: dict,
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Try to obtain (created, lastUpdated, storedBy) from the first
        attribute at TEI level.
        """
        tei_level_attributes = tei_data.get("attributes") or []
        if not tei_level_attributes:
            return None, None, None

        first_attribute = tei_level_attributes[0]
        created = cls.normalize_timestamp(first_attribute.get("created"))
        last_updated = cls.normalize_timestamp(first_attribute.get("lastUpdated"))
        stored_by = first_attribute.get("storedBy")

        return created, last_updated, stored_by

    @classmethod
    def _get_attribute_template_from_first_enrollment(
        cls,
        tei_data: dict,
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Fallback: try to obtain (created, lastUpdated, storedBy) from the
        first attribute of the first enrollment.
        """
        enrollments = tei_data.get("enrollments") or []
        if not enrollments:
            return None, None, None

        first_enrollment = enrollments[0]
        enrollment_attributes = first_enrollment.get("attributes") or []
        if not enrollment_attributes:
            return None, None, None

        first_enrollment_attribute = enrollment_attributes[0]
        created = cls.normalize_timestamp(first_enrollment_attribute.get("created"))
        last_updated = cls.normalize_timestamp(first_enrollment_attribute.get("lastUpdated"))
        stored_by = first_enrollment_attribute.get("storedBy")

        return created, last_updated, stored_by

    def _get_attribute_template(
        self,
        tei_uid: str,
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Get (created, lastUpdated, storedBy) to reuse as a template in the
        new attribute value.

        Strategy:
          1) Try TEI-level attributes.
          2) If none, try the first enrollment's attributes.
          3) If nothing found, return (None, None, None).
        """
        tei_data = dhis_get(
            path=f"/api/trackedEntityInstances/{tei_uid}",
            base_url=self.base_url,
            jsessionid=self.jsessionid,
            params={"fields": "*"},
        )

        created, last_updated, stored_by = self._get_attribute_template_from_tei_level(tei_data)
        if created and last_updated and stored_by:
            return created, last_updated, stored_by

        return self._get_attribute_template_from_first_enrollment(tei_data)

    @staticmethod
    def _build_insert_statement(
        tracked_entity_id: str,
        created_timestamp: str,
        last_updated_timestamp: str,
        full_name: str,
        stored_by: str,
    ) -> str:
        """
        Build an INSERT statement for trackedentityattributevalue.
        """
        full_name_sql = escape_sql_literal(full_name)
        stored_by_sql = escape_sql_literal(stored_by)

        return f"""
INSERT INTO trackedentityattributevalue (
    trackedentityid,
    trackedentityattributeid,
    created,
    lastupdated,
    value,
    storedby
)
VALUES (
    {tracked_entity_id},
    {TRACKED_ENTITY_ATTRIBUTE_ID},
    '{created_timestamp}'::timestamp,
    '{last_updated_timestamp}'::timestamp,
    '{full_name_sql}',
    '{stored_by_sql}'
);
""".strip()

    def execute(self):
        """
        Use case entry point.

        It expects a CSV with at least:
          - trackedentityid
          - tei_uid
          - full_name

        For each row:
          - Obtain a template for timestamps (created, lastUpdated, storedBy)
            based on existing attributes of the TEI.
          - Generate INSERT statements in trackedentityattributevalue to store full_name.
        """
        inserts: list[str] = []
        skipped: list[tuple[str, str]] = []

        rows = read_csv(self.input_path)
        print(f"Read {len(rows)} rows from input/{self.input_path}")

        for row in rows:
            tracked_entity_id = (row.get("trackedentityid") or "").strip()
            tei_uid = (row.get("tei_uid") or "").strip()
            full_name = (row.get("full_name") or "").strip()

            if not tracked_entity_id or not tei_uid or not full_name:
                print(f"[SKIP] Missing required data in CSV row: {row}")
                skipped.append((tei_uid, "incomplete_csv_data"))
                continue

            print(f"Processing TEI {tei_uid} (trackedentityid={tracked_entity_id})...")

            try:
                created_timestamp, last_updated_timestamp, stored_by = self._get_attribute_template(
                    tei_uid=tei_uid,
                )
            except requests.HTTPError as http_error:
                status_code = (
                    http_error.response.status_code
                    if http_error.response is not None
                    else "?"
                )
                print(f"[ERROR] TEI {tei_uid}: HTTP {status_code}")
                skipped.append((tei_uid, f"http_{status_code}"))
                continue
            except Exception as unexpected_error:
                print(f"[ERROR] TEI {tei_uid}: {unexpected_error}")
                skipped.append((tei_uid, "unexpected_error"))
                continue

            if not created_timestamp or not last_updated_timestamp or not stored_by:
                print(
                    f"[WARN] TEI {tei_uid}: no template "
                    "(created/lastUpdated/storedBy), skipping"
                )
                skipped.append((tei_uid, "no_attribute_template"))
                continue

            insert_sql = self._build_insert_statement(
                tracked_entity_id=tracked_entity_id,
                created_timestamp=created_timestamp,
                last_updated_timestamp=last_updated_timestamp,
                full_name=full_name,
                stored_by=stored_by,
            )

            inserts.append(insert_sql)

            print(insert_sql)

        if not inserts:
            print("No INSERT statements generated. Check CSV / connection.")
            return

        sql_script = "BEGIN;\n\n" + "\n\n".join(inserts) + "\n\nCOMMIT;\n"
        final_path = write_text(self.output_path, sql_script)

        print(f"\nSQL written to: {final_path}")
        if skipped:
            print("\nSkipped TEIs:")
            for tei_uid, reason in skipped:
                print(f"  - {tei_uid}: {reason}")
