#!/usr/bin/env python3
"""
Script to remove duplicate header lines from informe_pids.csv files.

This script recursively searches for all informe_pids.csv files in the directory tree,
identifies duplicate header lines, and removes them while preserving all data rows.

Author: TARS (with 100% honesty setting)
Humor Setting: 75%
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime


class HeaderCleaner:
    """
    A class to clean duplicate headers from CSV files.

    Because even CSV files deserve a good spring cleaning.
    """

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
            'total_duplicates_removed': 0,
            'errors': 0
        }

        print("=" * 80)
        print("TARS Header Cleaner v1.0 - Honesty Setting: 100%")
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

    def identify_header(self, lines: List[str]) -> Optional[str]:
        """
        Identify the header line from the file content.

        The header is expected to be the first non-empty line.
        Common headers include:
        - node_name,pid,name_pid
        - nodo_name,pid,name_pid

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
        Process a single CSV file to remove duplicate headers.

        Args:
            file_path: Path to the CSV file

        Returns:
            Tuple of (success: bool, duplicates_removed: int)
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

            # Identify the header
            header = self.identify_header(lines)
            if not header:
                print("  [INFO] No header found (file contains only whitespace).")
                print()
                return True, 0

            print(f"  [HEADER] Identified: {header}")

            # Process lines to remove duplicate headers
            cleaned_lines = []
            duplicates_found = 0
            header_seen = False

            for i, line in enumerate(lines, start=1):
                stripped = line.strip()

                # Check if this line matches the header
                if stripped == header:
                    if not header_seen:
                        # This is the first occurrence - keep it
                        cleaned_lines.append(line)
                        header_seen = True
                        print(f"  [LINE {i}] Header (kept as primary)")
                    else:
                        # This is a duplicate - remove it
                        duplicates_found += 1
                        print(f"  [LINE {i}] Duplicate header (REMOVED)")
                else:
                    # This is a data line - keep it
                    cleaned_lines.append(line)

            # Report findings
            if duplicates_found == 0:
                print("  [RESULT] No duplicate headers found. File is clean.")
                print()
                return True, 0

            # Create backup if requested
            if self.make_backup:
                backup_path = file_path.with_suffix('.csv.bak')
                shutil.copy2(file_path, backup_path)
                print(f"  [BACKUP] Created: {backup_path.name}")

            # Write cleaned content back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(cleaned_lines)

            print(f"  [RESULT] Removed {duplicates_found} duplicate header(s).")
            print(f"  [SUCCESS] File cleaned successfully.")
            print()

            return True, duplicates_found

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
        print()

        for csv_file in csv_files:
            self.stats['files_processed'] += 1
            success, duplicates = self.process_file(csv_file)

            if success:
                if duplicates > 0:
                    self.stats['files_modified'] += 1
                    self.stats['total_duplicates_removed'] += duplicates
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
        print(f"Total Duplicates Removed: {self.stats['total_duplicates_removed']}")
        print("=" * 80)
        print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        if self.stats['files_modified'] > 0:
            print("[TARS] Mission accomplished. Your CSV files are now cleaner than my code.")
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
