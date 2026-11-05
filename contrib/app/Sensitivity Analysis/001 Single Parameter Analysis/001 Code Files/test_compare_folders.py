import pytest
import filecmp
from pathlib import Path
import os


def compare_directories(dir1, dir2, extensions=None):
    """
    Recursively compare two directories.

    Parameters
    ----------
    dir1 : str or Path
    dir2 : str or Path
    extensions : set[str] or None
        If provided, only compare files with these suffixes, e.g. {".h5"}.

    Returns
    -------
    result : str
        Statement indicating if all files match or listing mismatches.
    """
    dir1 = Path(dir1)
    dir2 = Path(dir2)
    mismatches = []

    files1 = {
        p.relative_to(dir1) for p in dir1.rglob("*") if p.is_file() and (extensions is None or p.suffix in extensions)
    }

    files2 = {
        p.relative_to(dir2) for p in dir2.rglob("*") if p.is_file() and (extensions is None or p.suffix in extensions)
    }

    only_in_dir1 = sorted(files1 - files2)
    only_in_dir2 = sorted(files2 - files1)
    common_files = sorted(files1 & files2)

    for rel_path in only_in_dir1:
        mismatches.append(f"Missing in second folder: {rel_path}")

    for rel_path in only_in_dir2:
        mismatches.append(f"Extra in second folder: {rel_path}")

    for rel_path in common_files:
        file1 = dir1 / rel_path
        file2 = dir2 / rel_path

        if not filecmp.cmp(file1, file2, shallow=False):
            mismatches.append(f"Different content: {rel_path}")

    if mismatches:
        print("Mismatches found:\n" + "\n".join(mismatches))
        return False
    else:
        return True


def test_compare_expected_and_actual_output(base_dir):
    expected_folder = os.path.join(base_dir, "002_output_expected")
    actual_folder = os.path.join(base_dir, "003_output")
    assert compare_directories(expected_folder, actual_folder), "Folders do not match!"


# pytest -v test_compare_folders.py -d=C:\Users/nichowd/Desktop/Experiments/2026_11_5_single_param_sa_driver_combined
