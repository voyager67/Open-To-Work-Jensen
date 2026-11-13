"""Deterministic, explicitly fictional CUDA roadmap and satire generators."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Feature:
    name: str
    pitch: str
    why_it_matters: str


SCENARIOS: dict[str, dict[str, object]] = {
    "operations_first": {
        "label": "Interim caretaker (operations-first)",
        "assumption": "A hypothetical interim leader prioritizes predictable releases, compatibility, and execution discipline.",
        "features": [
            Feature("CUDA Compatibility Ledger", "A public matrix mapping toolkit, driver, compiler, and architecture compatibility.", "Reduces upgrade guesswork across long-lived production fleets."),
            Feature("Reproducible Kernel Builds", "Hermetic build manifests with compiler, flags, target, and dependency fingerprints.", "Makes performance regressions easier to reproduce and audit."),
            Feature("Fleet Health API", "A unified interface for driver health, ECC events, thermal state, and workload readiness.", "Turns fleet operations into something teams can automate."),
            Feature("Long-Term Support Toolkit", "Clearly versioned maintenance windows and migration checks for supported CUDA branches.", "Helps enterprises plan upgrades without surprise deadlines."),
            Feature("Performance Change Reports", "Release-to-release benchmark diffs with hardware, workload, and variance metadata.", "Separates a real speedup from benchmark noise."),
        ],
    },
    "engineering_led": {
        "label": "Engineering-led continuity",
        "assumption": "A hypothetical engineering-led transition protects the core programming model while investing in developer productivity.",
        "features": [
            Feature("Kernel Observatory", "A profiler view connecting source lines, launch geometry, occupancy, and hardware counters.", "Shortens the path from slow kernel to actionable diagnosis."),
            Feature("Portable CUDA Graphs", "Better graph capture diagnostics and portability checks across supported GPU generations.", "Makes complex multi-stage workloads easier to deploy."),
            Feature("Async Memory Contracts", "Static and runtime checks for asynchronous copies, barriers, and buffer lifetimes.", "Catches subtle synchronization bugs before production."),
            Feature("Compiler Feedback API", "Structured optimization remarks that IDEs and CI systems can consume.", "Moves compiler guidance into the developer workflow."),
            Feature("Open Kernel Test Corpus", "A versioned suite of representative kernels with correctness and performance baselines.", "Gives the ecosystem a shared way to validate changes."),
        ],
    },
    "ecosystem_first": {
        "label": "Ecosystem-first reset",
        "assumption": "A hypothetical ecosystem-first leader emphasizes interoperability, education, and transparent developer interfaces.",
        "features": [
            Feature("CUDA Interop Matrix", "Executable examples for interoperating with major frameworks, runtimes, and communication libraries.", "Makes integration costs visible before teams commit."),
            Feature("Stable Extension Interfaces", "Documented extension points with compatibility guarantees and deprecation windows.", "Reduces dependence on undocumented behavior."),
            Feature("Community Kernel Registry", "A curated, signed catalogue of reusable kernels with tests and provenance.", "Makes high-quality building blocks easier to discover."),
            Feature("Migration Assistant", "A static analyzer that flags deprecated APIs and suggests documented alternatives.", "Turns migration into an incremental engineering task."),
            Feature("Teaching Compute Sandbox", "Small, reproducible labs that run on local GPUs, hosted notebooks, or CPU emulation.", "Lowers the barrier to learning parallel programming."),
        ],
    },
}

FOCUS_MODIFIERS: dict[str, str] = {
    "Performance": "Prioritize measurable throughput and latency improvements, with reproducible benchmarks.",
    "Reliability": "Prioritize correctness, debuggability, and predictable behavior under production load.",
    "Developer experience": "Prioritize clear APIs, actionable diagnostics, and shorter feedback loops.",
    "Interoperability": "Prioritize documented boundaries and practical integration across the software stack.",
}

SATIRE: dict[str, list[str]] = {
    "Open-to-work card": [
        "OPEN TO WORK (FICTIONAL THOUGHT EXPERIMENT)\nRole sought: Chief Kernel Whisperer.\nStrengths: parallel thinking, launch configuration, and making a leather jacket look like formal wear.\nAvailability: hypothetical. CUDA skills: very real. Please do not contact anyone on my behalf.",
        "PROFILE UPDATE\nHeadline: Formerly the face on every GPU keynote slide; currently available for fictional consulting on kernels, compilers, and jacket ergonomics.\nReferences: one billion GPU threads, give or take.\nThis is a joke, not an employment announcement.",
    ],
    "Press release parody": [
        "FOR IMMEDIATE RELEASE — FROM THE COMPLETELY FICTIONAL JACKET OFFICE\nThe jacket has announced a strategic pivot into open-source wardrobe acceleration. Roadmap items include lower-latency zippers, deterministic pockets, and CUDA-aware dry cleaning. No actual product or personnel change is implied.",
        "BREAKING (IN A COMPLETELY MADE-UP UNIVERSE)\nThe leather jacket is exploring an open governance model. Initial RFC: should pockets be lock-free? Community feedback welcome; actual executives should be left in peace.",
    ],
    "Developer note": [
        "Dear developers: the next release will contain fewer keynote adjectives, more reproducible benchmarks, and a compiler warning when your kernel is running on vibes. This roadmap is fictional. The bugs, unfortunately, are not.",
        "CUDA FUTURE NOTE\nFeature request accepted: `nvidia-smi --tell-me-why`. Status: emotionally approved, technically imaginary. Please file real bugs through official channels, not through anyone's DMs.",
    ],
}


def build_cuda_roadmap(scenario: str, focus: str = "Performance") -> dict[str, object]:
    """Return a hypothetical roadmap. It is a scenario exercise, not a forecast."""
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    if focus not in FOCUS_MODIFIERS:
        raise ValueError(f"Unknown focus: {focus}")

    spec = SCENARIOS[scenario]
    features = [
        {
            "name": feature.name,
            "pitch": feature.pitch,
            "why_it_matters": feature.why_it_matters,
        }
        for feature in spec["features"]  # type: ignore[index]
    ]
    return {
        "scenario": str(spec["label"]),
        "assumption": str(spec["assumption"]),
        "focus": focus,
        "focus_modifier": FOCUS_MODIFIERS[focus],
        "features": features,
        "disclaimer": "Fictional product ideation. Not an NVIDIA roadmap, prediction, insider claim, or statement about any executive's plans.",
    }


def generate_satire(format_name: str = "Open-to-work card", variation: int = 0) -> str:
    """Return a light, non-targeted satire snippet without making factual claims."""
    if format_name not in SATIRE:
        raise ValueError(f"Unknown satire format: {format_name}")
    options = SATIRE[format_name]
    return options[variation % len(options)]
