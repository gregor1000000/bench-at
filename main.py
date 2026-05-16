import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent


def main():
    args = sys.argv[1:]

    if not args or args[0] == "numbers":
        from solve_numbers import main as numbers_main
        numbers_main()
    elif args[0] == "figures":
        from solve_figures import main as figures_main
        figures_main()
    elif args[0] == "words":
        from solve_words import main as words_main
        words_main()
    elif args[0] == "extract":
        from extract_numbers import main as extract_main
        extract_main()
    elif args[0] == "extract-words":
        from extract_words import main as extract_words_main
        extract_words_main()
    else:
        print("Usage: uv run python main.py [numbers|figures|words|extract|extract-words]")
        print("  numbers       — Solve number sequence problems (Zahlenfolgen)")
        print("  figures       — Solve geometric figures problems (3000 Figuren Medium)")
        print("  words         — Solve word fluency problems (Wortflüssigkeit)")
        print("  extract       — Extract CSV from Zahlenfolgen.pdf")
        print("  extract-words — Extract CSV from Wortflüssigkeit.pdf")


if __name__ == "__main__":
    main()
