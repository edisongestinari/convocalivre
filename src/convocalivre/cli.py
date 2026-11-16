"""Local command line interface for TXT and searchable PDF files."""
import argparse
import json
from pathlib import Path
import sys

from .core import analyze
from .pdf import analyze_pdf


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="convocalivre", description="Busca local de nomes em TXT e PDF com evidencias."
    )
    parser.add_argument("file", help="Arquivo .txt UTF-8 ou PDF com texto pesquisavel")
    parser.add_argument("--name", required=True, help="Nome completo (nao transmitido)")
    parser.add_argument("--source-url", default="", help="Link fornecido pelo usuario, NAO verificado")
    parser.add_argument("--date", default="", help="Data informada pelo usuario, NAO verificada")
    parser.add_argument("--output", help="Caminho para salvar relatorio JSON; padrao: stdout")
    args = parser.parse_args(argv)
    try:
        path = Path(args.file)
        if path.suffix.lower() == ".pdf":
            report = analyze_pdf(
                path, args.name, source_url=args.source_url, publication_date=args.date
            )
        elif path.suffix.lower() == ".txt":
            report = analyze(
                path.read_text(encoding="utf-8"), args.name,
                source_url=args.source_url, publication_date=args.date,
            )
        else:
            raise ValueError("Formato nao suportado: use .pdf ou .txt.")
        encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            Path(args.output).write_text(encoded, encoding="utf-8")
        else:
            print(encoded, end="")
        return 0
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
