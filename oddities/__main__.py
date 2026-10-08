"""Dependency-free research CLI: python -m oddities --help."""

import argparse
import json
from pathlib import Path

from .audit import audit_file
from .odds import expected_return, implied_probability, proportional_devig


def main() -> None:
    parser = argparse.ArgumentParser(description="Oddities research foundation")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("demo", help="Synthetic calculation example, not a prediction")
    audit = commands.add_parser("audit", help="Inspect an existing SBR NBA JSON file")
    audit.add_argument("path", type=Path)
    audit.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.command == "demo":
        result = {
            "mode": "SYNTHETIC EXAMPLE — not live data or a trained model",
            "example_model_probability": 0.58,
            "example_available_american_odds": 110,
            "break_even_probability": implied_probability(110),
            "example_model_expected_return": expected_return(0.58, 110),
            "example_same_book_devig_probabilities": proportional_devig(-120, 100),
            "devig_method": "proportional normalization",
        }
    else:
        try:
            result = audit_file(args.path)
        except (OSError, ValueError) as exc:
            parser.error(str(exc))
    rendered = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.command == "audit" and args.output:
        if args.output.resolve() == args.path.resolve():
            parser.error("Output must not overwrite the input dataset")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")


if __name__ == "__main__":
    main()
