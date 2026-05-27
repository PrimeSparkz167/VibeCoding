"""
mega_diff.py
Reads two pasted Pokémon stat files (one at a time via stdin),
stores all Pokémon with a numeric value, normalises Mega names so
'Charizard-Mega-Y' and 'Mega Charizard Y' match across files,
then prints a sorted difference table.

Format 1:  "Charizard-Mega-Y\t20"  (name TAB value, one per line)
Format 2:  "15\t\t\tMega Charizard Y"  (leading value, lots of whitespace, then name)
"""

import re
import sys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MEGA_RE = re.compile(r'Mega[- ]', re.IGNORECASE)


def is_mega(name: str) -> bool:
    """Return True if the name contains 'Mega ' or 'Mega-'."""
    return bool(MEGA_RE.search(name))


def normalize(name: str) -> str:
    """
    Canonical form for Mega names only: replace all dashes with spaces,
    collapse multiple spaces, strip whitespace.
    Non-Mega names are returned as-is (dashes are meaningful in e.g. 'Mr-Mime').

    e.g. 'Charizard-Mega-Y' -> 'Charizard Mega Y'
         'Mega Charizard Y' -> 'Mega Charizard Y'
         'Mr-Mime'          -> 'Mr-Mime'
    """
    if MEGA_RE.search(name):
        name = re.sub(r'-', ' ', name)
        name = re.sub(r'\s+', ' ', name)
    return name.strip()


def read_paste(prompt: str) -> list[str]:
    """
    Print a prompt then read lines from stdin until an empty line or EOF.
    Returns a list of raw (non-empty) lines.
    """
    print(prompt)
    lines = []
    try:
        for line in sys.stdin:
            stripped = line.rstrip('\n')
            if stripped == '':      # blank line signals end of paste
                break
            lines.append(stripped)
    except EOFError:
        pass
    return lines


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def parse_format1(lines: list[str]) -> dict[str, int]:
    """
    Format 1: each line is  "<name>\t<value>"
    e.g.  "Charizard-Mega-Y\t20"  or  "Bulbasaur\t45"

    Steps:
      1. Split on the first tab only.
      2. Strip whitespace from both parts.
      3. Parse value as int; skip non-numeric lines.
      4. Normalize the name (dashes → spaces for Mega names only).
    """
    result: dict[str, int] = {}
    for line in lines:
        parts = line.split('\t', 1)
        if len(parts) != 2:
            continue                        # skip malformed lines
        name_raw, value_raw = parts[0].strip(), parts[1].strip()
        if not name_raw or not value_raw:
            continue
        try:
            value = int(value_raw)
        except ValueError:
            continue
        result[normalize(name_raw)] = value
    return result


def parse_format2(lines: list[str]) -> dict[str, int]:
    """
    Format 2: each line may look like:
        "  \t\t\tBulbasaur"          (no leading number → skip)
        "11\t\t\tMega Venusaur"      (leading number, then name)
        "-\t\t\t-"                   (separator → skip)

    Steps:
      1. Split each line on whitespace tokens.
      2. First token must be a bare integer; skip if '-' or non-numeric.
      3. Join remaining tokens as the name.
      4. Normalize the name (dashes → spaces for Mega names only).
    """
    result: dict[str, int] = {}
    for line in lines:
        tokens = line.split()
        if len(tokens) < 2:
            continue                        # blank or separator-only line
        value_token = tokens[0]
        if not value_token.lstrip('-').isdigit():
            continue                        # non-numeric first token
        if value_token.startswith('-'):
            continue                        # negative / dash sentinel
        try:
            value = int(value_token)
        except ValueError:
            continue
        name_raw = ' '.join(tokens[1:])
        result[normalize(name_raw)] = value
    return result


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def collect_input() -> tuple[dict[str, int], dict[str, int]]:
    """
    Ask the user to paste each file (type 1 or 2) until both are provided.
    Returns (dict_from_file1, dict_from_file2).
    """
    collected: dict[int, dict[str, int]] = {}

    while len(collected) < 2:
        missing = [k for k in (1, 2) if k not in collected]
        print(f"\nStill need file(s): {missing}")
        choice = input("Enter file type to paste (1 or 2): ").strip()

        if choice not in ('1', '2'):
            print("  → Please enter 1 or 2.")
            continue

        file_type = int(choice)
        if file_type in collected:
            print(f"  → File {file_type} already provided. Skipping.")
            continue

        lines = read_paste(
            f"Paste file {file_type} content now (finish with a blank line):"
        )

        if not lines:
            print("  → No content detected, try again.")
            continue

        if file_type == 1:
            parsed = parse_format1(lines)
        else:
            parsed = parse_format2(lines)

        if not parsed:
            print(f"  → No entries found in file {file_type}. Check the format.")
            continue

        collected[file_type] = parsed
        print(f"  → Loaded {len(parsed)} entries from file {file_type}.")

    return collected[1], collected[2]


def compute_diff(
    d1: dict[str, int],
    d2: dict[str, int]
) -> list[tuple[str, int]]:
    """
    Intersect keys of d1 and d2.
    For each shared Pokémon, compute diff = d1[name] - d2[name].
    Return a list of (name, diff) sorted ascending by diff.
    """
    shared = d1.keys() & d2.keys()
    diffs = [(name, d1[name] - d2[name]) for name in shared]
    diffs.sort(key=lambda t: t[1])
    return diffs


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Pokémon Difference Calculator ===")
    d1, d2 = collect_input()

    diffs = compute_diff(d1, d2)

    if not diffs:
        print("\nNo Mega Pokémon names matched between the two files.")
        return

    print(f"\n{'Pokémon':<35} {'File1':>6} {'File2':>6} {'Diff':>6}")
    print("-" * 57)
    for name, diff in diffs:
        v1 = d1[name]
        v2 = d2[name]
        print(f"{name:<35} {v1:>6} {v2:>6} {diff:>+6}")

    print(f"\n{len(diffs)} Mega Pokémon compared.")


if __name__ == '__main__':
    main()