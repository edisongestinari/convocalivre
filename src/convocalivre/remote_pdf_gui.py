"""Tkinter view for a single public PDF URL (no Querido Diario API)."""

from __future__ import annotations

from pathlib import Path
from queue import Empty, Queue
from threading import Thread
import webbrowser

from .remote_pdf import (
    RemotePDFError, download_and_analyze_public_pdf, validate_public_pdf_url,
)

LABELS = {
    "convocacao": "Possivel convocacao",
    "nomeacao": "Possivel nomeacao",
    "desistencia_exclusao": "Possivel exclusao/desistencia",
    "resultado_homologacao": "Possivel resultado/homologacao",
    "indeterminado": "Ato indeterminado",
}


def open_remote_pdf_dialog(parent, name: str) -> None:
    import tkinter as tk
    from tkinter import messagebox, ttk

    dialog = tk.Toplevel(parent)
    dialog.title("ConvocaLivre — Consultar PDF público por link")
    dialog.geometry("910x590")
    dialog.minsize(740, 460)
    dialog.transient(parent)

    url = tk.StringVar()
    status = tk.StringVar(
        value="Cole um link HTTPS direto para um PDF público. Nenhum download iniciado."
    )
    state: dict = {"running": False, "url": "", "matches": []}
    events: Queue = Queue()

    outer = ttk.Frame(dialog, padding=16)
    outer.pack(fill="both", expand=True)
    ttk.Label(
        outer, text="Analisar PDF público por link",
        font=("Segoe UI", 16, "bold"),
    ).pack(anchor="w")
    ttk.Label(
        outer, text=(
            "Alternativa independente da API do Querido Diário. "
            "O ConvocaLivre baixa um único PDF temporariamente e procura "
            "o nome no seu computador. Não monitora sites automaticamente."
        ), wraplength=840,
    ).pack(anchor="w", pady=(5, 10))
    ttk.Label(
        outer, text=f"Nome pesquisado: {name[:120]}",
        font=("Segoe UI", 10, "bold"),
    ).pack(anchor="w", pady=(0, 7))
    ttk.Label(
        outer, text="Endereço HTTPS do PDF oficial ou de publicação pública:"
    ).pack(anchor="w")
    url_entry = ttk.Entry(outer, textvariable=url)
    url_entry.pack(fill="x", pady=(4, 8))
    ttk.Label(
        outer, text=(
            "Privacidade: somente o endereço do PDF será solicitado ao site. "
            "O nome não será enviado como parâmetro. "
            "O site poderá registrar sua conexão e o download."
        ), wraplength=840, foreground="#805000",
    ).pack(anchor="w", pady=(0, 8))

    button = ttk.Button(outer, text="Baixar e analisar PDF")
    button.pack(anchor="w")
    ttk.Label(outer, textvariable=status, wraplength=840).pack(
        anchor="w", pady=(8, 5)
    )
    spinner = ttk.Progressbar(outer, mode="indeterminate")

    ttk.Label(
        outer, text=(
            "Ocorrências neste documento (classificações indicativas):"
        ),
    ).pack(anchor="w", pady=(9, 5))
    frame = ttk.Frame(outer)
    frame.pack(fill="both", expand=True)
    cols = ("page", "kind", "indicator")
    tree = ttk.Treeview(frame, columns=cols, show="headings")
    for key, title, width in (
        ("page", "Página física", 95),
        ("kind", "Tipo de ocorrência", 370),
        ("indicator", "Indicador", 180),
    ):
        tree.heading(key, text=title)
        tree.column(key, width=width, stretch=True)
    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    detail = tk.Text(outer, height=4, wrap="word")
    detail.pack(fill="x", pady=(8, 6))
    detail.configure(state="disabled")
    open_button = ttk.Button(outer, text="Abrir PDF original na página selecionada")
    open_button.pack(anchor="w")

    def show_detail(_event=None):
        selected = tree.selection()
        text = ""
        if selected:
            index = int(selected[0])
            if index < len(state["matches"]):
                match = state["matches"][index]
                text = str(match.get("act_context_excerpt") or match.get("excerpt") or "")
        detail.configure(state="normal")
        detail.delete("1.0", "end")
        detail.insert(
            "1.0", text or "Nenhum trecho adicional. Confira a publicação original."
        )
        detail.configure(state="disabled")

    def open_pdf(_event=None):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo(
                "Publicação", "Selecione uma ocorrência.", parent=dialog
            )
            return
        index = int(selected[0])
        if index >= len(state["matches"]):
            return
        page = state["matches"][index].get("page_number")
        source = state["url"]
        if not source:
            return
        uri = source + (f"#page={page}" if page else "")
        webbrowser.open(uri)

    def poll():
        if not dialog.winfo_exists():
            return
        try:
            kind, payload = events.get_nowait()
        except Empty:
            dialog.after(100, poll)
            return
        state["running"] = False
        spinner.stop()
        spinner.pack_forget()
        button.state(["!disabled"])
        url_entry.state(["!disabled"])
        if kind == "error":
            status.set(payload + " A falha nao significa que o nome esteja ausente.")
            return
        matches = payload["report"]["matches"]
        state["url"] = payload["source_url"]
        state["matches"] = matches[:200]
        for row in tree.get_children():
            tree.delete(row)
        for index, match in enumerate(state["matches"]):
            tree.insert(
                "", "end", iid=str(index),
                values=(
                    match.get("page_number", "—"),
                    LABELS.get(match.get("act_type"), "Ato indeterminado"),
                    match.get("act_indicator") or "—",
                ),
            )
        pages_without = payload["report"]["pages_without_text"]
        if matches:
            info = f"{len(matches)} ocorrência(s) nesta publicação."
        else:
            info = "Nome não localizado no texto extraível deste PDF."
        status.set(
            f"Análise concluída: {info} "
            f"Páginas sem texto extraível: {len(pages_without)}. "
            "Sempre confira o documento original."
        )
        show_detail()

    def start():
        if state["running"]:
            return
        try:
            chosen = validate_public_pdf_url(url.get())
        except RemotePDFError as exc:
            messagebox.showwarning("Link do PDF", str(exc), parent=dialog)
            return
        confirmed = messagebox.askyesno(
            "Autorizar download público?",
            "O ConvocaLivre acessará o endereço HTTPS informado para "
            "baixar temporariamente o PDF.\n\n"
            "O nome pesquisado NÃO será enviado como parâmetro; "
            "o site poderá registrar seu endereço de rede.\n\n"
            "Deseja continuar?",
            parent=dialog,
        )
        if not confirmed:
            status.set("Download cancelado. Nenhuma solicitação foi iniciada.")
            return
        state["running"] = True
        state["matches"] = []
        state["url"] = ""
        for item in tree.get_children():
            tree.delete(item)
        button.state(["disabled"])
        url_entry.state(["disabled"])
        status.set("Baixando PDF público e procurando o nome. Aguarde a conclusão...")
        spinner.pack(fill="x", pady=(0, 7), before=frame)
        spinner.start(15)

        def worker():
            try:
                result = download_and_analyze_public_pdf(chosen, name)
                events.put(("ok", result))
            except RemotePDFError as exc:
                events.put(("error", str(exc)))
            except Exception:
                events.put(("error", "Falha inesperada ao processar o PDF."))

        Thread(target=worker, daemon=True).start()
        dialog.after(100, poll)

    button.configure(command=start)
    open_button.configure(command=open_pdf)
    tree.bind("<<TreeviewSelect>>", show_detail)
    tree.bind("<Double-1>", open_pdf)
    url_entry.focus_set()
