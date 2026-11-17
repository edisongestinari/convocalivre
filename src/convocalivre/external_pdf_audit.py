"""Privacy-conscious audit of public municipal PDFs.

The manifest stores SHA-256 digests of names, not candidate names.
Full names are reconstructed transiently from the PDF text layer and are
never printed, persisted, or included in the JSON output.

This is an exploratory, hand-annotated sample, not a population estimate.
Remote sources may change or become unavailable. No OCR or web scraping.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import tempfile
from urllib.request import Request, urlopen
from urllib.parse import urlparse

from pypdf import PdfReader

from .acts import EVENT_TYPES
from .core import normalize_with_mapping
from .pdf import analyze_pdf, MAX_PDF_BYTES, MAX_PAGES

LABELS = (*EVENT_TYPES, "no_name_match")
EVENTS = set(EVENT_TYPES) - {"indeterminado"}
WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
MAX_WORDS = 8


def normalize_name(value: str) -> str:
    normalized = normalize_with_mapping(value)[0]
    return " ".join(normalized.split())


def name_digest(value: str) -> str:
    return sha256(normalize_name(value).encode("utf-8")).hexdigest()


def recover_name_from_page(page, digest: str) -> tuple[str | None, str | None]:
    """Reconstruct a name without keeping target plaintext in the manifest.

    This locator is itself an additional source of *selection bias*:
    unresolved names are reported separately and NEVER counted as true
    negatives. A matching digest never proves an act's legal meaning.
    """
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Invalid name digest")
    for mode in ("plain", "layout"):
        raw = (
            page.extract_text() if mode == "plain"
            else page.extract_text(extraction_mode="layout")
        ) or ""
        words = [m.group() for m in WORD.finditer(raw)]
        folded = [normalize_name(word) for word in words]
        for index in range(len(words)):
            for count in range(2, min(MAX_WORDS, len(words) - index) + 1):
                possible = " ".join(folded[index:index + count])
                if sha256(possible.encode("utf-8")).hexdigest() == digest:
                    return " ".join(words[index:index + count]), mode
    return None, None


def fetch_public_pdf(url: str, *, max_bytes: int = MAX_PDF_BYTES) -> bytes:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("Only fixed HTTPS public PDF URLs are permitted")
    request = Request(
        url,
        headers={
            "User-Agent": "ConvocaLivre-Public-Document-Audit/0.1 (research; one-off)",
            "Accept": "application/pdf,*/*",
        },
    )
    with urlopen(request, timeout=25) as response:
        final_url = response.geturl()
        # Reject protocol downgrade and do not follow redirection to HTTP.
        if urlparse(final_url).scheme != "https":
            raise ValueError("Insecure redirect")
        data = response.read(max_bytes + 1)
    if not data.startswith(b"%PDF-") or len(data) > max_bytes:
        raise ValueError("Invalid or oversized PDF")
    return data


def _prediction(report: dict, expected_page: int) -> tuple[str, int]:
    matches = [
        item for item in report["matches"]
        if item["page_number"] == expected_page
    ]
    if not matches:
        return "no_name_match", 0
    types = {match["act_type"] for match in matches}
    return (next(iter(types)) if len(types) == 1 else "indeterminado",
            len(matches))


def _matrix_metrics(pairs: list[tuple[str, str]]) -> dict:
    matrix = {label: {other: 0 for other in LABELS} for label in LABELS}
    for actual, predicted in pairs:
        matrix[actual][predicted] += 1
    classes = {}
    for label in LABELS:
        tp = matrix[label][label]
        fp = sum(matrix[actual][label] for actual in LABELS if actual != label)
        fn = sum(matrix[label][other] for other in LABELS if other != label)
        classes[label] = {
            "tp": tp, "fp": fp, "fn": fn,
            "precision": round(tp / (tp + fp), 4) if tp + fp else None,
            "recall": round(tp / (tp + fn), 4) if tp + fn else None,
        }
    return {
        "n": len(pairs),
        "exact_matches": sum(matrix[label][label] for label in LABELS),
        "exact_accuracy": (
            round(sum(matrix[label][label] for label in LABELS) / len(pairs), 4)
            if pairs else None
        ),
        "per_class": classes,
        "confusion_matrix": matrix,
    }


def evaluate_public_pdfs(manifest: dict, fetcher=fetch_public_pdf) -> dict:
    if manifest.get("dataset_kind") != "human_annotated_public_pdfs":
        raise ValueError("Unrecognized audit manifest")
    sources = manifest["sources"]
    if len({source["id"] for source in sources}) != len(sources):
        raise ValueError("Duplicated source id")
    all_case_ids = [
        case["id"] for source in sources for case in source["cases"]
    ]
    if len(set(all_case_ids)) != len(all_case_ids):
        raise ValueError("Duplicated case id")

    source_statuses = []
    case_results = []
    recovered = {}
    saved = {}
    label_pairs = []
    name_tp = name_fp = name_fn = name_tn = 0

    with tempfile.TemporaryDirectory() as tmp:
        for source in sources:
            source_id = source["id"]
            status = {
                "source_id": source_id, "url": source["url"],
                "status": "source_unavailable", "page_count": None,
                "pdf_sha256": None,
            }
            source_statuses.append(status)
            try:
                blob = fetcher(source["url"])
                reader = PdfReader(BytesIO(blob), strict=False)
                if reader.is_encrypted or not 1 <= len(reader.pages) <= MAX_PAGES:
                    raise ValueError("Encrypted or oversized page count")
                path = Path(tmp) / (source_id + ".pdf")
                path.write_bytes(blob)
                saved[source_id] = path
                status.update({
                    "status": "available",
                    "page_count": len(reader.pages),
                    "pdf_sha256": sha256(blob).hexdigest(),
                })
            except Exception as exc:
                status["reason"] = type(exc).__name__
                for case in source["cases"]:
                    case_results.append({
                        "id": case["id"], "source_id": source_id,
                        "status": "source_unavailable", "expected": case["expected"],
                    })
                continue

            for case in source["cases"]:
                result = {
                    "id": case["id"], "source_id": source_id,
                    "expected": case["expected"],
                }
                case_results.append(result)
                target_page = case["page_number"]
                if not 1 <= target_page <= len(reader.pages):
                    result["status"] = "invalid_reference_page"
                    continue
                try:
                    name, locator = recover_name_from_page(
                        reader.pages[target_page - 1], case["name_sha256"]
                    )
                except Exception as exc:
                    result.update({
                        "status": "locator_error", "reason": type(exc).__name__,
                    })
                    continue
                if name is None:
                    result["status"] = "target_unresolved"
                    continue
                result["locator_mode"] = locator
                recovered[case["id"]] = name
                try:
                    report = analyze_pdf(path, name)
                    predicted, matches_here = _prediction(report, target_page)
                except Exception as exc:
                    result.update({
                        "status": "analysis_error", "reason": type(exc).__name__,
                    })
                    continue
                result.update({
                    "status": "evaluated",
                    "predicted": predicted,
                    "matched_name_on_reference_page": bool(matches_here),
                })
                if matches_here:
                    name_tp += 1
                else:
                    name_fn += 1
                label_pairs.append((case["expected"], predicted))

        for pair in manifest.get("negative_pairs", []):
            case_id, destination = pair["target_case"], pair["in_source"]
            result = {
                "id": pair["id"], "source_id": destination,
                "expected": "no_name_match",
            }
            case_results.append(result)
            if case_id not in recovered or destination not in saved:
                result["status"] = "dependent_case_unavailable"
                continue
            try:
                report = analyze_pdf(saved[destination], recovered[case_id])
            except Exception as exc:
                result.update({
                    "status": "analysis_error", "reason": type(exc).__name__,
                })
                continue
            scoped_page = pair.get("page_number")
            if scoped_page is not None:
                if not isinstance(scoped_page, int) or not (
                    1 <= scoped_page <= report["page_count"]
                ):
                    result["status"] = "invalid_reference_page"
                    continue
                observed = any(
                    match["page_number"] == scoped_page
                    for match in report["matches"]
                )
            else:
                observed = bool(report["matches"])
            result.update({
                "status": "evaluated",
                "scope": "page" if scoped_page is not None else "document",
                "predicted": "name_present" if observed else "no_name_match",
            })
            if observed:
                name_fp += 1
            else:
                name_tn += 1
            # Binary name-absence probes are kept separate from act labels.
            # Never count their predicted 'name_present' as an act category.

    return {
        "audit_kind": "exploratory_real_public_pdf_end_to_end",
        "privacy": "No candidate names or extracted personal fields in output",
        "source_statuses": source_statuses,
        "case_results": case_results,
        "available_sources": sum(
            item["status"] == "available" for item in source_statuses
        ),
        "positive_reference_cases": len(all_case_ids),
        "positive_cases_evaluated": len(label_pairs),
        "unresolved_positive_cases": sum(
            item["status"] == "target_unresolved" for item in case_results
        ),
        "name_presence": {
            "tp": name_tp, "fp": name_fp, "fn": name_fn, "tn": name_tn,
            "note": (
                "Cases with unresolved hashed targets are not counted. "
                "Cross-document negatives are opportunistic, not a random sample."
            ),
        },
        "act_classification": _matrix_metrics(label_pairs),
        "caution": (
            "Small, non-random, hand-labeled convenience sample. Results "
            "cannot estimate production accuracy. Hashed-name locator can "
            "introduce selection bias; source unavailability is not a TN."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    result = evaluate_public_pdfs(manifest)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    # A missing third-party document is inconclusive; not a software failure.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
