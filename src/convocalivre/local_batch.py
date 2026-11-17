"""Local multi-document scanning; no web access and no background monitoring."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .core import analyze
from .pdf import analyze_pdf

ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_BATCH_FILES = 100
MAX_TXT_BYTES = 25 * 1024 * 1024


def collect_files(inputs: list[str | Path], *, recursive: bool = False) -> list[Path]:
    """Expand paths and folders without following symlinks or duplicating files."""
    found: dict[str, Path] = {}
    for supplied in inputs:
        path = Path(supplied).expanduser()
        if path.is_symlink():
            continue
        if path.is_dir():
            candidates = path.rglob("*") if recursive else path.iterdir()
        elif path.is_file():
            candidates = (path,)
        else:
            raise ValueError(f"Arquivo ou pasta nao encontrado: {path}")
        for candidate in candidates:
            if candidate.is_symlink() or not candidate.is_file():
                continue
            if candidate.suffix.lower() not in ALLOWED_EXTENSIONS:
                continue
            key = str(candidate.resolve())
            found.setdefault(key, candidate)
            if len(found) > MAX_BATCH_FILES:
                raise ValueError(
                    f"Limite de {MAX_BATCH_FILES} arquivos por lote excedido."
                )
    return sorted(found.values(), key=lambda item: str(item).casefold())


def analyze_local_files(files: list[str | Path], name: str) -> dict:
    """Process an explicit local file set and isolate per-file failures."""
    if not isinstance(name, str) or len(name.split()) < 2:
        raise ValueError("Informe um nome completo com ao menos duas partes.")
    if not files or len(files) > MAX_BATCH_FILES:
        raise ValueError("Informe de 1 a 100 documentos.")
    outputs = []
    mentions = 0
    files_with_names = 0
    failures = 0
    for supplied in files:
        path = Path(supplied)
        item = {"file": str(path), "status": "error", "report": None}
        try:
            if path.is_symlink() or path.suffix.lower() not in ALLOWED_EXTENSIONS:
                raise ValueError("Arquivo nao suportado ou link simbolico.")
            if path.suffix.lower() == ".pdf":
                report = analyze_pdf(path, name)
            else:
                if path.stat().st_size > MAX_TXT_BYTES:
                    raise ValueError("TXT excede o limite seguro de tamanho.")
                content = path.read_text(encoding="utf-8")
                if "\x00" in content:
                    raise ValueError("TXT contem bytes nulos e nao e texto simples.")
                report = analyze(content, name)
            item.update(status="analyzed", report=report)
            mentions += report["match_count"]
            files_with_names += int(report["match_count"] > 0)
        except (OSError, UnicodeError, ValueError) as exc:
            # Avoid echoing parser exception contents, which might contain PDF text.
            item["error_type"] = type(exc).__name__
            item["message"] = "Nao foi possivel analisar este documento."
            failures += 1
        outputs.append(item)
    return {
        "tool": "ConvocaLivre",
        "batch_version": "1",
        "analyzed_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_name": name.strip(),
        "files_total": len(files),
        "files_analyzed": len(files) - failures,
        "files_failed": failures,
        "files_with_name": files_with_names,
        "mention_count": mentions,
        "documents": outputs,
        "privacy_notice": (
            "O relatorio fica no dispositivo do usuario e inclui nome, "
            "trechos e caminhos locais. Nao publique sem revisar."
        ),
        "important_notice": (
            "Uma mencao ou classificacao e apenas indiciaria, "
            "nunca confirmacao juridica de nomeacao ou convocacao."
        ),
    }
