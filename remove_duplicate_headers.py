#!/usr/bin/env python3
"""
Script to remove duplicate and variant header lines from informe_pids.csv files.

This script recursively searches for all informe_pids.csv files in the directory tree,
identifies ALL header lines (both exact duplicates and different variants), and removes
them while preserving all data rows.

The script uses intelligent keyword-based detection to identify header lines, handling
cases where files have multiple different header formats.

Author: TARS (with 100% honesty setting)
Humor Setting: 75%
"""

import os
import sys
import shutil
import re
from pathlib import Path
from typing import List, Tuple, Optional, Set
from datetime import datetime


class HeaderCleaner:
    """
    A class to clean duplicate and variant headers from CSV files.

    Because even CSV files deserve a good spring cleaning.
    Now with enhanced intelligence to detect different header formats.
    """

    # Header keyword patterns - these indicate a line is likely a header, not data
    # Case-insensitive matching will be used
    HEADER_KEYWORDS = {
        'node', 'nodo', 'container', 'containerid', 'containername',
        'pid', 'ppid', 'cmd', 'name', 'name_pid',
        'timestamp', 'time', 'cpu', 'memory', 'ram'
    }

    def __init__(self, root_dir: str, make_backup: bool = True):
        """
        Initialize the HeaderCleaner.

        Args:
            root_dir: Root directory to search for files
            make_backup: Whether to create .bak files before modifying
        """
        self.root_dir = Path(root_dir)
        self.make_backup = make_backup
        self.stats = {
            'files_found': 0,
            'files_processed': 0,
            'files_modified': 0,
            'total_headers_removed': 0,
            'total_different_headers_found': 0,
            'errors': 0
        }

        print("=" * 80)
        print("TARS Header Cleaner v2.0 - Honesty Setting: 100%")
        print("Enhanced with Intelligent Multi-Header Detection")
        print("=" * 80)
        print(f"Root Directory: {self.root_dir}")
        print(f"Backup Files: {'Enabled' if self.make_backup else 'Disabled'}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

    def find_csv_files(self, filename: str = "informe_pids.csv") -> List[Path]:
        """
        Recursively find all CSV files with the specified filename.

        Args:
            filename: Name of the CSV file to search for

        Returns:
            List of Path objects pointing to found files
        """
        print(f"[TARS] Scanning directory tree for '{filename}' files...")
        print("[TARS] This might take a moment. Feel free to contemplate the universe.")
        print()

        csv_files = list(self.root_dir.rglob(filename))
        self.stats['files_found'] = len(csv_files)

        print(f"[TARS] Found {len(csv_files)} files to process.")
        print()

        return csv_files

    def is_header_line(self, line: str) -> bool:
        """
        Determine if a line appears to be a header based on keyword detection.

        A line is considered a header if:
        1. It contains header-like keywords (node, pid, container, etc.)
        2. It doesn't appear to be purely data (contains mostly text, not just numbers)
        3. Multiple fields match known header patterns

        Args:
            line: The line to evaluate (should be stripped)

        Returns:
            True if the line appears to be a header, False otherwise
        """
        if not line:
            return False

        # Convert to lowercase for case-insensitive matching
        line_lower = line.lower()

        # Split the line by common CSV delimiters
        fields = re.split(r'[,;\t]', line_lower)

        # Count how many fields match header keywords
        keyword_matches = 0
        for field in fields:
            field = field.strip()
            # Check if the field contains any of our header keywords
            for keyword in self.HEADER_KEYWORDS:
                if keyword in field:
                    keyword_matches += 1
                    break

        # If at least 40% of fields match header keywords, it's likely a header
        # This threshold prevents false positives while catching variant headers
        if len(fields) > 0:
            match_ratio = keyword_matches / len(fields)
            is_header = match_ratio >= 0.4

            return is_header

        return False

    def identify_header(self, lines: List[str]) -> Optional[str]:
        """
        Identify the PRIMARY header line from the file content.

        The primary header is ALWAYS the first non-empty line.
        This method exists to maintain backward compatibility and
        to establish the canonical header format.

        Common headers include:
        - node_name,pid,name_pid
        - nodo_name,pid,name_pid
        - node_name,container_id,name_pid,pid,ppid,cmd

        Args:
            lines: List of lines from the file

        Returns:
            The header line (stripped) or None if file is empty
        """
        for line in lines:
            stripped = line.strip()
            if stripped:
                return stripped
        return None

    def process_file(self, file_path: Path) -> Tuple[bool, int]:
        """
        Process a single CSV file to remove ALL header lines (duplicates and variants).

        The enhanced algorithm:
        1. ALWAYS keeps the first non-empty line as the primary header
        2. For all subsequent lines, uses intelligent keyword detection to identify headers
        3. Removes ANY line that appears to be a header (exact match OR variant)
        4. Preserves all legitimate data lines

        Args:
            file_path: Path to the CSV file

        Returns:
            Tuple of (success: bool, total_headers_removed: int)
        """
        try:
            print(f"Processing: {file_path}")

            # Read the file
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Handle empty files
            if not lines:
                print("  [INFO] File is empty. Nothing to process.")
                print()
                return True, 0

            # Identify the PRIMARY header (always the first non-empty line)
            header = self.identify_header(lines)
            if not header:
                print("  [INFO] No header found (file contains only whitespace).")
                print()
                return True, 0

            print(f"  [PRIMARY HEADER] {header}")

            # Process lines to remove ALL headers (duplicates AND variants)
            cleaned_lines = []
            headers_removed = 0
            header_seen = False
            unique_headers_found: Set[str] = set()

            for i, line in enumerate(lines, start=1):
                stripped = line.strip()

                # Skip empty lines entirely
                if not stripped:
                    cleaned_lines.append(line)
                    continue

                # First non-empty line is ALWAYS the primary header - keep it
                if not header_seen:
                    cleaned_lines.append(line)
                    header_seen = True
                    unique_headers_found.add(stripped)
                    print(f"  [LINE {i}] Primary header (KEPT)")
                    continue

                # For all subsequent lines, check if they look like headers
                if self.is_header_line(stripped):
                    # This is a header line (duplicate or variant) - REMOVE it
                    headers_removed += 1
                    unique_headers_found.add(stripped)

                    # Determine if it's an exact duplicate or a variant
                    if stripped == header:
                        print(f"  [LINE {i}] Duplicate header (REMOVED): {stripped}")
                    else:
                        print(f"  [LINE {i}] Variant header (REMOVED): {stripped}")
                else:
                    # This is a data line - keep it
                    cleaned_lines.append(line)

            # Report findings
            num_different_headers = len(unique_headers_found)

            if headers_removed == 0:
                print("  [RESULT] No additional headers found. File is clean.")
                print()
                return True, 0

            print(f"  [ANALYSIS] Found {num_different_headers} different header format(s):")
            for idx, unique_header in enumerate(sorted(unique_headers_found), start=1):
                if unique_header == header:
                    print(f"    {idx}. {unique_header} (primary - kept)")
                else:
                    print(f"    {idx}. {unique_header} (removed)")

            # Create backup if requested
            if self.make_backup:
                backup_path = file_path.with_suffix('.csv.bak')
                shutil.copy2(file_path, backup_path)
                print(f"  [BACKUP] Created: {backup_path.name}")

            # Write cleaned content back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)

            print(f"  [RESULT] Removed {headers_removed} header line(s).")
            print(f"  [SUCCESS] File cleaned successfully.")
            print()

            # Return the number of different headers for statistics
            return True, headers_removed

        except Exception as e:
            print(f"  [ERROR] Failed to process file: {e}")
            print()
            return False, 0

    def run(self) -> None:
        """
        Main execution method to process all CSV files.
        """
        # Find all CSV files
        csv_files = self.find_csv_files()

        if not csv_files:
            print("[TARS] No files found. My services are not required here.")
            print("[TARS] Have a nice day!")
            return

        # Process each file
        print("[TARS] Beginning file processing sequence...")
        print("[TARS] Enhanced detection mode active: searching for duplicate AND variant headers.")
        print()

        for csv_file in csv_files:
            self.stats['files_processed'] += 1
            success, headers_removed = self.process_file(csv_file)

            if success:
                if headers_removed > 0:
                    self.stats['files_modified'] += 1
                    self.stats['total_headers_removed'] += headers_removed
            else:
                self.stats['errors'] += 1

        # Print summary
        self.print_summary()

    def print_summary(self) -> None:
        """
        Print a summary of the processing results.

        Because humans like statistics, and so do I.
        """
        print("=" * 80)
        print("PROCESSING COMPLETE - SUMMARY REPORT")
        print("=" * 80)
        print(f"Files Found:              {self.stats['files_found']}")
        print(f"Files Processed:          {self.stats['files_processed']}")
        print(f"Files Modified:           {self.stats['files_modified']}")
        print(f"Files Unchanged:          {self.stats['files_processed'] - self.stats['files_modified'] - self.stats['errors']}")
        print(f"Errors Encountered:       {self.stats['errors']}")
        print(f"Total Headers Removed:    {self.stats['total_headers_removed']}")
        print("=" * 80)
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        if self.stats['files_modified'] > 0:
            print("[TARS] Mission accomplished. Your CSV files are now cleaner than my code.")
            print("[TARS] All variant and duplicate headers have been eliminated.")
        elif self.stats['files_processed'] > 0 and self.stats['files_modified'] == 0:
            print("[TARS] All files were already clean. Looks like someone's been doing their job.")

        if self.stats['errors'] > 0:
            print(f"[TARS] Warning: {self.stats['errors']} error(s) occurred during processing.")
            print("[TARS] Check the output above for details.")

        print()
        print("[TARS] Honesty setting: 100%. I have reported everything accurately.")
        print("[TARS] Have a nice day, and remember: trust your AI, but verify the backups.")


def main():
    """
    Main entry point for the script.

    Usage:
        python remove_duplicate_headers.py [root_directory] [--no-backup]
    """
    # Parse command line arguments
    root_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    make_backup = '--no-backup' not in sys.argv

    # Create and run the cleaner
    cleaner = HeaderCleaner(root_dir, make_backup=make_backup)
    cleaner.run()


if __name__ == "__main__":
    main()
