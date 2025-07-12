"""
Enables:  python -m pubmed_paper_fetcher "query"
Simply forwards to the CLI entry point.
"""
from .cli import main

if __name__ == "__main__":
    main()
