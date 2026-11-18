"""Entry point for a Windows frozen executable.

This launcher deliberately does not create a Tk window during --smoke-test,
so the GitHub Windows runner can validate a produced executable headlessly.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--smoke-test"]:
        from convocalivre import __version__
        from convocalivre import pdf, gui, diagnostics, remote_pdf
        assert callable(pdf.analyze_pdf)
        assert callable(gui.launch)
        assert callable(diagnostics.diagnose_pdf)
        assert callable(remote_pdf.download_and_analyze_public_pdf)
        print("ConvocaLivre " + __version__ + ": packaging smoke test OK")
        return 0
    if argv:
        print("Argumento desconhecido. Execute o aplicativo sem argumentos.")
        return 2
    from convocalivre.gui import main as launch_gui
    return launch_gui()


if __name__ == "__main__":
    raise SystemExit(main())
