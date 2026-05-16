#!/usr/bin/env python3
"""Run all extractors: raw → canonical JSONL + cached assets."""
from data.extract.extract_numbers import main as extract_numbers
from data.extract.extract_words import main as extract_words
from data.extract.extract_figures import main as extract_figures


def main():
    print("=" * 50)
    print("BENCH-AT Extraction Pipeline")
    print("=" * 50)

    extract_numbers()
    extract_words()
    extract_figures()

    print("\nDone. All tasks extracted to data/canonical/")


if __name__ == "__main__":
    main()
