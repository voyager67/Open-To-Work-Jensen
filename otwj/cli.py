"""Preview-only command line interface for the fictional generators."""

from __future__ import annotations

import argparse
import json

from . import __version__
from .generator import FOCUS_MODIFIERS, SCENARIOS, SATIRE, build_cuda_roadmap, generate_satire


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="otwj",
        description="Preview fictional CUDA roadmap ideas and satire. This CLI never posts or contacts anyone.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="required safety switch; print a local preview only (no network or external actions)",
    )
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="engineering_led")
    parser.add_argument(
        "--focus",
        choices=sorted(FOCUS_MODIFIERS),
        default="Developer experience",
    )
    parser.add_argument("--satire", choices=sorted(SATIRE), default="Open-to-work card")
    parser.add_argument("--json", action="store_true", help="print structured JSON output")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.dry_run:
        parser.error("preview-only CLI: pass --dry-run to confirm local output only")

    roadmap = build_cuda_roadmap(args.scenario, args.focus)
    satire = generate_satire(args.satire)
    result = {"roadmap": roadmap, "satire": satire, "mode": "dry-run / local preview only"}

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("OPEN TO WORK JENSEN — DRY RUN (LOCAL PREVIEW ONLY)")
        print(f"Scenario: {roadmap['scenario']} | Focus: {roadmap['focus']}")
        print("\nHYPOTHETICAL CUDA FEATURES")
        for index, feature in enumerate(roadmap["features"], start=1):
            print(f"{index}. {feature['name']} — {feature['pitch']}")
        print("\nSATIRE PREVIEW")
        print(satire)
        print("\nDISCLAIMER: " + str(roadmap["disclaimer"]))
        print("No posts, messages, network requests, or external actions were made.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
