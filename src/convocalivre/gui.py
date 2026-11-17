"""Optional offline desktop interface for the ConvocaLivre local MVP.

Run: python -m convocalivre.gui
Requires tkinter (shipped with most Windows Python installations).
No external servers, telemetry, or automatic publication monitoring.
"""

from __future__ import annotations

import json
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
import webbrowser

from .local_batch import analyze_local_files, collect_files


LABELS = {
    "convocacao": "Possivel convocacao",
    "nomeacao": "Possivel nomeacao",
    "desistencia_exclusao": "Possivel exclusao/desistencia",
    "resultado_homologacao": "Possivel resultado/homologacao",
    "indeterminado": "Ato indeterminado",
}


def launch() -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    class Window:
        def __init__(self, root):
            self.root = root
            self.root.title("ConvocaLivre — Consulta local de publicacoes")
            self.root.geometry("1050x670")
            self.root.minsize(820, 530)
            self.name = tk.StringVar()
            self.status = tk.StringVar(value="Selecione um ou mais arquivos PDF ou TXT.")
            self.paths: list[Path] = []
            self.scan_result: dict | None = None
            self.row_paths: dict[str, tuple[Path, int | None]] = {}
            self.messages: Queue = Queue()
            self.running = False

            outer = ttk.Frame(root, padding=16)
            outer.pack(fill="both", expand=True)
            ttk.Label(
                outer,
                text="ConvocaLivre",
                font=("Segoe UI", 19, "bold"),
            ).pack(anchor="w")
            ttk.Label(
                outer,
                text="Consulta offline de nomes em publicacoes. "
                     "O resultado nao confirma nomeacao nem convocacao.",
                wraplength=990,
            ).pack(anchor="w", pady=(1, 12))

            name_row = ttk.Frame(outer)
            name_row.pack(fill="x", pady=(0, 8))
            ttk.Label(name_row, text="Nome completo:").pack(side="left")
            self.name_entry = ttk.Entry(name_row, textvariable=self.name, width=66)
            self.name_entry.pack(side="left", padx=(8, 0), fill="x", expand=True)

            controls = ttk.Frame(outer)
            controls.pack(fill="x", pady=(0, 10))
            ttk.Button(controls, text="Adicionar PDFs/TXT",
                       command=self.add_files).pack(side="left", padx=(0, 6))
            ttk.Button(controls, text="Adicionar pasta",
                       command=self.add_folder).pack(side="left", padx=(0, 6))
            ttk.Button(controls, text="Limpar lista",
                       command=self.clear_files).pack(side="left", padx=(0, 6))
            self.run_button = ttk.Button(
                controls, text="Buscar nome", command=self.run
            )
            self.run_button.pack(side="left", padx=(12, 6))
            self.export_button = ttk.Button(
                controls, text="Salvar relatorio JSON", command=self.export
            )
            self.export_button.pack(side="right")
            self.export_button.state(["disabled"])

            ttk.Label(outer, textvariable=self.status, wraplength=990).pack(
                anchor="w", pady=(0, 9)
            )
            ttk.Label(outer, text="Resultados (todos exigem revisao humana):").pack(
                anchor="w", pady=(0, 5)
            )
            content = ttk.Frame(outer)
            content.pack(fill="both", expand=True)
            columns = ("arquivo", "pagina", "resultado", "indicador")
            self.tree = ttk.Treeview(
                content, columns=columns, show="headings", selectmode="browse"
            )
            for key, caption, width in (
                ("arquivo", "Arquivo", 310),
                ("pagina", "Pagina PDF", 105),
                ("resultado", "Tipo de ocorrencia", 300),
                ("indicador", "Indicador", 155),
            ):
                self.tree.heading(key, text=caption)
                self.tree.column(key, width=width, anchor="w", stretch=True)
            yscroll = ttk.Scrollbar(content, orient="vertical", command=self.tree.yview)
            self.tree.configure(yscrollcommand=yscroll.set)
            self.tree.pack(side="left", fill="both", expand=True)
            yscroll.pack(side="right", fill="y")
            self.tree.bind("<Double-1>", lambda _event: self.open_selected())

            actions = ttk.Frame(outer)
            actions.pack(fill="x", pady=(9, 2))
            ttk.Button(actions, text="Abrir PDF selecionado",
                       command=self.open_selected).pack(side="left")
            ttk.Label(
                actions,
                text="A pagina informada e a posicao fisica no PDF.",
            ).pack(side="left", padx=(15, 0))
            ttk.Label(
                outer,
                text="Privacidade: consulta e processada no seu computador. "
                     "Um JSON exportado contem nomes e trechos do documento. "
                     "PDFs digitalizados sem texto podem nao ser pesquisaveis.",
                wraplength=990,
            ).pack(anchor="w", pady=(9, 0))
            self.name_entry.focus_set()

        def _add(self, candidates):
            if self.running:
                return
            try:
                selected = collect_files([*self.paths, *candidates])
            except ValueError as exc:
                messagebox.showerror("Arquivos", str(exc))
                return
            self.paths = selected
            self.status.set(
                f"{len(self.paths)} documento(s) selecionado(s). "
                "Limite de 100 por consulta."
            )
            self.scan_result = None
            self.export_button.state(["disabled"])

        def add_files(self):
            names = filedialog.askopenfilenames(
                title="Selecione PDFs e TXT",
                filetypes=[("PDF e TXT", "*.pdf *.txt"),
                           ("PDF", "*.pdf"), ("Texto", "*.txt")],
            )
            if names:
                self._add(list(names))

        def add_folder(self):
            folder = filedialog.askdirectory(title="Selecione pasta local")
            if folder:
                self._add([folder])

        def clear_files(self):
            if self.running:
                return
            self.paths = []
            self.scan_result = None
            self.row_paths = {}
            self.export_button.state(["disabled"])
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.status.set("Lista limpa. Selecione novos documentos.")

        def run(self):
            if self.running:
                return
            name = self.name.get().strip()
            if len(name.split()) < 2:
                messagebox.showwarning(
                    "Nome", "Informe nome completo com pelo menos duas partes."
                )
                return
            if not self.paths:
                messagebox.showwarning(
                    "Arquivos", "Selecione pelo menos um PDF ou TXT."
                )
                return
            self.running = True
            self.run_button.state(["disabled"])
            self.export_button.state(["disabled"])
            self.status.set(f"Analisando {len(self.paths)} documento(s) localmente...")
            self.scan_result = None
            selected_files = self.paths[:]
            for item in self.tree.get_children():
                self.tree.delete(item)
            self.row_paths = {}

            def worker():
                try:
                    report = analyze_local_files(selected_files, name)
                    self.messages.put(("ok", report))
                except Exception:
                    # Do not display sensitive parser exception content.
                    self.messages.put(("error", None))

            Thread(target=worker, daemon=True).start()
            self.root.after(100, self.poll)

        def poll(self):
            try:
                outcome, report = self.messages.get_nowait()
            except Empty:
                self.root.after(100, self.poll)
                return
            self.running = False
            self.run_button.state(["!disabled"])
            if outcome != "ok":
                self.status.set("A consulta falhou. Verifique os arquivos.")
                return
            self.scan_result = report
            self.export_button.state(["!disabled"])
            self.status.set(
                f"{report['files_analyzed']}/{report['files_total']} arquivo(s) "
                f"analisado(s) | {report['files_with_name']} arquivo(s) "
                f"com mencao | {report['mention_count']} ocorrencia(s). "
                "Confira as paginas originais."
            )
            for document in report["documents"]:
                file = Path(document["file"])
                if document["status"] != "analyzed":
                    self.append(file, None, "Falha na analise", "")
                    continue
                matches = document["report"]["matches"]
                if not matches:
                    self.append(file, None, "Nome nao encontrado", "")
                    continue
                for match in matches:
                    self.append(
                        file,
                        match.get("page_number"),
                        LABELS.get(match["act_type"], "Indeterminado"),
                        match.get("act_indicator") or "",
                    )

        def append(self, file, page, category, indicator):
            identity = self.tree.insert(
                "", "end",
                values=(file.name, page if page is not None else "—",
                        category, indicator),
            )
            self.row_paths[identity] = (file, page)

        def open_selected(self):
            selection = self.tree.selection()
            if not selection:
                messagebox.showinfo("Abrir", "Selecione uma linha do resultado.")
                return
            file, page = self.row_paths[selection[0]]
            if not file.is_file():
                messagebox.showerror("Abrir", "Arquivo nao encontrado.")
                return
            uri = file.resolve().as_uri()
            if file.suffix.lower() == ".pdf" and page:
                uri += f"#page={page}"
            if not webbrowser.open(uri):
                messagebox.showinfo(
                    "Abrir", "O navegador nao abriu o arquivo. "
                    f"Localize-o manualmente em: {file}"
                )

        def export(self):
            if not self.scan_result:
                return
            dest = filedialog.asksaveasfilename(
                title="Salvar relatorio no seu computador",
                defaultextension=".json",
                filetypes=[("Relatorio JSON", "*.json")],
            )
            if not dest:
                return
            try:
                Path(dest).write_text(
                    json.dumps(self.scan_result, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
            except OSError:
                messagebox.showerror("Salvar", "Nao foi possivel salvar o relatorio.")
                return
            messagebox.showinfo(
                "Salvo", "Relatorio salvo localmente. "
                "Nao compartilhe sem revisar os dados pessoais."
            )

    root = tk.Tk()
    Window(root)
    root.mainloop()


def main() -> int:
    try:
        launch()
    except ImportError:
        print("Erro: tkinter nao instalado. Use Python com suporte a Tk.", flush=True)
        return 2
    except Exception as exc:
        # TclError for headless machines; otherwise bubble in development.
        if type(exc).__name__ == "TclError":
            print("Erro: interface grafica indisponivel nesta sessao.", flush=True)
            return 2
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
