"""Regenerate documented synthetic examples from the engine, without touching saved campus data."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from engine import calculate, prepare, summarize
from models import CalculationRequest, CampusResponse
from sample_data import create_sample_campus


if __name__ == "__main__":
    campus = create_sample_campus()
    packages, audit = prepare(campus)
    response = CampusResponse(campus=campus, baseline=summarize(campus.buildings, [p[0] for p in packages], campus.scenario),
                              profile_audit=audit)
    (ROOT / "docs/sample-campus.json").write_text(response.model_dump_json(indent=2), encoding="utf-8")
    result = calculate(campus, CalculationRequest(revision=campus.revision, mode="A"))
    (ROOT / "docs/sample-calculation.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
    print(f"Generated synthetic examples: {audit.hour_count} hours; status={result.status}")
