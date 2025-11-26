# main.py

import argparse

from file_utils import load_dhis_env_config
from create_missing_values_use_case import CreateMissingValuesUseCase
from reorder_sections_use_case import ReorderSectionsUseCase
from dhis_utils import test_connection

# Default configuration (can be overridden by .env and CLI)
DEFAULT_BASE_URL = ""
DEFAULT_JSESSIONID = ""

DEFAULT_INPUT_FILE = ("teis_without_storedby.csv")    # read from input/
DEFAULT_OUTPUT_FILE = "insert_attr_fullname.sql"    # write to output/

DEFAULT_BLUEPRINT_INPUT = "Blueprint_HWF.xlsx"  # read from input/
DEFAULT_BLUEPRINT_OUTPUT = "blueprint_apvd.xlsx"  # write to output/
DEFAULT_BLUEPRINT_SHEETS = ("Module 1 - APVD", "Module 2 - APVD")
DEFAULT_SECTIONS_INPUT = "sections_order.json"  # read from input/
DEFAULT_SECTIONS_OUTPUT = "sections_order_sorted.json"  # write to output/
DEFAULT_USE_CASE = "create-missing-values"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Utilities for DHIS2 blueprints and tracked entities."
    )
    parser.add_argument(
        "--use-case",
        choices=["create-missing-values", "update-blueprint-dataelements", "reorder-sections"],
        default=DEFAULT_USE_CASE,
        help="Which workflow to run.",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="DHIS2 base URL (default from code or .env).",
    )
    parser.add_argument(
        "--jsessionid",
        default=DEFAULT_JSESSIONID,
        help="JSESSIONID cookie value (default from code or .env).",
    )
    parser.add_argument(
        "--input-file",
        default=DEFAULT_INPUT_FILE,
        help="Input CSV file name (relative to 'input/' folder).",
    )
    parser.add_argument(
        "--output-file",
        default=DEFAULT_OUTPUT_FILE,
        help="Output SQL file name (relative to 'output/' folder).",
    )
    parser.add_argument(
        "--xlsx-file",
        default=DEFAULT_BLUEPRINT_INPUT,
        help="Input XLSX file (relative to 'input/' folder) for blueprint updates.",
    )
    parser.add_argument(
        "--output-xlsx-file",
        default=DEFAULT_BLUEPRINT_OUTPUT,
        help="Output XLSX file (relative to 'output/' folder) for blueprint updates.",
    )
    parser.add_argument(
        "--sheets",
        nargs="+",
        default=list(DEFAULT_BLUEPRINT_SHEETS),
        help="Sheet names to process when updating blueprint data elements.",
    )
    parser.add_argument(
        "--name-col",
        default="3",
        help="Column (index, letter, or header text) that holds the data element name.",
    )
    parser.add_argument(
        "--uid-col",
        default="DE UID",
        help="Column (index, letter, or header text) where the UID will be written.",
    )
    parser.add_argument(
        "--code-col",
        default="DE Code",
        help="Column (index, letter, or header text) where the code will be written.",
    )
    parser.add_argument(
        "--data-start-row",
        type=int,
        default=2,
        help="Row to start reading data when headers are not used.",
    )
    parser.add_argument(
        "--sections-file",
        default=DEFAULT_SECTIONS_INPUT,
        help="Input JSON file with sections (relative to 'input/' folder).",
    )
    parser.add_argument(
        "--sections-output-file",
        default=DEFAULT_SECTIONS_OUTPUT,
        help="Output JSON file for sorted sections (relative to 'output/' folder).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Merge CLI defaults with .env (with confirmation)
    base_url, jsessionid = load_dhis_env_config(
        default_base_url=args.base_url,
        default_jsessionid=args.jsessionid,
    )

    if args.use_case == "update-blueprint-dataelements":
        # Lazy import to avoid requiring openpyxl when not using this workflow.
        from update_blueprint_dataelements_use_case import UpdateBlueprintDataElementsUseCase

        test_connection(base_url=base_url, jsessionid=jsessionid)
        use_case = UpdateBlueprintDataElementsUseCase(
            base_url=base_url,
            jsessionid=jsessionid,
            xlsx_path=args.xlsx_file,
            output_path=args.output_xlsx_file,
            sheet_names=args.sheets,
            name_column=args.name_col,
            uid_column=args.uid_col,
            code_column=args.code_col,
            data_start_row=args.data_start_row,
        )
    elif args.use_case == "reorder-sections":
        use_case = ReorderSectionsUseCase(
            input_path=args.sections_file,
            output_path=args.sections_output_file,
        )
    else:
        test_connection(base_url=base_url, jsessionid=jsessionid)
        use_case = CreateMissingValuesUseCase(
            base_url=base_url,
            jsessionid=jsessionid,
            input_path=args.input_file,
            output_path=args.output_file,
        )

    use_case.execute()


if __name__ == "__main__":
    main()
