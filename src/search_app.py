"""
DesktopAI
Semantic Search Demo

A standalone entry point for Phase 9: builds the semantic search
index from whatever files are already in the database (run
src/app.py first to scan some files), then lets you search them
using plain-language queries.

This never moves, renames, or deletes anything — it only searches.
"""

from core.logger import get_logger
from search.search_engine import build_search_index, semantic_search

logger = get_logger("app")


def main():
    print("=" * 50)
    print("🔍 DesktopAI Semantic Search")
    print("=" * 50)

    print("\nBuilding search index from scanned files...")
    indexed_count = build_search_index()

    if indexed_count == 0:
        print(
            "\nNo files were indexed. Run 'python src/app.py' first to scan\n"
            "some files with actual text content, then try again."
        )
        return

    print(f"Indexed {indexed_count} file(s).\n")
    print("Type a search query, or press Enter with nothing typed to quit.\n")

    while True:
        query = input("Search: ").strip()
        if not query:
            print("Goodbye!")
            break

        results = semantic_search(query)

        if not results:
            print("  No matches found.\n")
            continue

        for result in results:
            print(f"  {result.score:.3f}  {result.path.name}  ({result.path})")
        print()


if __name__ == "__main__":
    main()