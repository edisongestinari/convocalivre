"""Local command line interface for TXT and searchable PDF files."""
import argparse
import json
from pathlib import Path
import sys

from . import __version__
from .core import analyze
from .pdf import analyze_pdf
from .diagnostics import diagnose_pdf
from .local_batch import collect_files, analyze_local_files


def _write_json(report: dict, output: str | None) -> None:
    encoded = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if output:
        Path(output).write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


def _local_tools(argv: list[str]) -> int:
    command = argv[0]
    if command == "gui":
        if len(argv) > 1:
            print("Uso: python -m convocalivre gui", file=sys.stderr)
            return 2
        from .gui import main as gui_main
        return gui_main()
    parser = argparse.ArgumentParser(
        prog=f"convocalivre {command}",
        description="Consulta local. Nenhum dado e enviado pela ferramenta.",
    )
    if command == "diagnose":
        parser.add_argument("file", help="Arquivo PDF local")
        parser.add_argument("--output", help="Salvar JSON sem trechos pessoais")
    elif command == "batch":
        parser.add_argument("paths", nargs="+", help="PDFs, TXT ou pastas locais")
        parser.add_argument("--name", required=True, help="Nome completo")
        parser.add_argument("--recursive", action="store_true",
                            help="Incluir subpastas")
        parser.add_argument("--output", help="Relatorio JSON local (contem nomes)")
    else:
        return 2
    args = parser.parse_args(argv[1:])
    try:
        if command == "diagnose":
            report = diagnose_pdf(args.file)
        else:
            files = collect_files(args.paths, recursive=args.recursive)
            report = analyze_local_files(files, args.name)
        _write_json(report, args.output)
        return 0
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2


def main(argv: list[str] | None = None) -> int:
    args_in = list(sys.argv[1:] if argv is None else argv)
    if args_in and args_in[0] in {"gui", "diagnose", "batch"}:
        return _local_tools(args_in)
    parser = argparse.ArgumentParser(
        prog="convocalivre",
        description="Busca local de nomes em TXT e PDF com evidencias.",
        epilog="Tambem disponivel: convocalivre gui | diagnose ARQUIVO.pdf | batch PASTA --name NOME",

    )
    parser.add_argument("--version", action="version", version=f"ConvocaLivre {__version__}")
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
        _write_json(report, args.output)
        return 0
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
