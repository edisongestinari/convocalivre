"""Explicitly user-triggered online search dialog for the local GUI.

No calls are made on opening the dialog; the user must first consent to
sending their full name to Querido Diario's third-party search endpoint.
"""

from __future__ import annotations

from queue import Empty, Queue
from threading import Thread
import webbrowser

from .online_search import OnlineSearchError, search_gazettes, validate_search

IBGE_INFO_URL = "https://www.ibge.gov.br/explica/codigos-dos-municipios.php"


def open_online_dialog(parent, person_name: str) -> None:
    import tkinter as tk
    from tkinter import messagebox, ttk

    dialog = tk.Toplevel(parent)
    dialog.title("ConvocaLivre — Consultar diários oficiais online")
    dialog.geometry("950x610")
    dialog.minsize(720, 460)
    dialog.transient(parent)
    dialog.grab_set()

    status = tk.StringVar(
        value="Consulta sob demanda: nenhuma informacao foi enviada."
    )
    city = tk.StringVar()
    events: Queue = Queue()
    state = {"running": False, "results": []}

    outer = ttk.Frame(dialog, padding=16)
    outer.pack(fill="both", expand=True)
    ttk.Label(
        outer, text="Consultar publicações online",
        font=("Segoe UI", 16, "bold"),
    ).pack(anchor="w")
    ttk.Label(
        outer,
        text=(
            "Fonte: API publica Querido Diario (Open Knowledge Brasil). "
            "Esta pesquisa exige conexao com a internet e nao cobre "
            "necessariamente todos os municipios ou diarios."
        ),
        wraplength=875,
    ).pack(anchor="w", pady=(4, 12))
    ttk.Label(
        outer,
        text=(
            "Privacidade: ao iniciar esta consulta, o NOME COMPLETO "
            "sera transmitido a um servico externo. A busca local de "
            "PDFs continua offline."
        ),
        wraplength=875,
        foreground="#805000",
    ).pack(anchor="w", pady=(0, 10))

    name_label = ttk.Label(
        outer, text=f"Nome a pesquisar: {person_name[:120]}",
        font=("Segoe UI", 10, "bold"),
    )
    name_label.pack(anchor="w", pady=(0, 6))
    controls = ttk.Frame(outer)
    controls.pack(fill="x")
    ttk.Label(controls, text="Código IBGE do município (7 dígitos):").pack(
        side="left", padx=(0, 7)
    )
    city_entry = ttk.Entry(controls, textvariable=city, width=14)
    city_entry.pack(side="left")
    ttk.Button(
        controls, text="Encontrar código IBGE",
        command=lambda: webbrowser.open(IBGE_INFO_URL),
    ).pack(side="left", padx=10)
    ttk.Label(
        outer, text="Exemplo: Cruzeiro do Oeste (PR) = 4106605."
    ).pack(anchor="w", pady=(3, 10))

    search_button = ttk.Button(outer, text="Consultar agora")
    search_button.pack(anchor="w", pady=(0, 8))
    ttk.Label(
        outer, textvariable=status, wraplength=850
    ).pack(anchor="w", pady=(0, 8))
    activity = ttk.Progressbar(outer, mode="indeterminate")
    # Only pack while request is in progress.

    ttk.Label(
        outer,
        text="Possíveis menções encontradas — nunca confirmação de nomeação:",
    ).pack(anchor="w", pady=(7, 5))
    frame = ttk.Frame(outer)
    frame.pack(fill="both", expand=True)
    cols = ("data", "municipio", "edicao", "trecho")
    tree = ttk.Treeview(
        frame, columns=cols, show="headings", selectmode="browse"
    )
    for key, title, width in (
        ("data", "Data", 110),
        ("municipio", "Município", 160),
        ("edicao", "Edição", 80),
        ("trecho", "Trecho da API (não verificado)", 570),
    ):
        tree.heading(key, text=title)
        tree.column(key, width=width, stretch=True)
    scroll = ttk.Scrollbar(frame, command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    detail = tk.Text(outer, height=4, wrap="word")
    detail.pack(fill="x", pady=(8, 7))
    detail.configure(state="disabled")
    actions = ttk.Frame(outer)
    actions.pack(fill="x")
    open_button = ttk.Button(actions, text="Abrir publicação original")
    open_button.pack(side="left")
    ttk.Button(
        actions, text="Abrir site Querido Diário",
        command=lambda: webbrowser.open("https://queridodiario.org.br/"),
    ).pack(side="left", padx=(12, 0))
    ttk.Label(
        outer, text=(
            "Se a API não responder, use o site do Querido Diário ou "
            "consulte diretamente o órgão responsável pela publicação. "
            "Falha de conexão não significa ausência do nome."
        ), wraplength=870,
    ).pack(anchor="w", pady=(5, 0))

    def select_result(_event=None):
        selection = tree.selection()
        text = ""
        if selection:
            index = int(selection[0])
            if index < len(state["results"]):
                text = state["results"][index]["excerpt"]
        detail.configure(state="normal")
        detail.delete("1.0", "end")
        detail.insert("1.0", text or "Sem trecho disponível. Consulte a publicação.")
        detail.configure(state="disabled")

    def open_original(_event=None):
        selection = tree.selection()
        if not selection:
            messagebox.showinfo(
                "Publicação", "Selecione uma ocorrência.", parent=dialog
            )
            return
        index = int(selection[0])
        if index >= len(state["results"]):
            return
        url = state["results"][index]["pdf_url"]
        if not url:
            messagebox.showinfo(
                "Publicação", "A API não forneceu um link HTTPS para esta edição.",
                parent=dialog,
            )
            return
        webbrowser.open(url)

    def poll():
        if not dialog.winfo_exists():
            return
        try:
            kind, payload = events.get_nowait()
        except Empty:
            dialog.after(100, poll)
            return
        state["running"] = False
        activity.stop()
        activity.pack_forget()
        search_button.state(["!disabled"])
        city_entry.state(["!disabled"])
        if kind == "error":
            status.set(
                payload + " Nenhuma conclusão pode ser tirada desta falha. "
                "Use o botão para abrir o site como alternativa."
            )
            return
        state["results"] = payload["results"]
        for item in tree.get_children():
            tree.delete(item)
        for i, result in enumerate(state["results"]):
            tree.insert(
                "", "end", iid=str(i),
                values=(
                    result["date"] or "—",
                    result["municipality"] or "—",
                    result["edition"] or "—",
                    result["excerpt"][:180],
                ),
            )
        n = len(state["results"])
        status.set(
            f"Consulta concluída: {n} edição(ões) recebida(s) da API. "
            "A ausência de resultados NÃO prova ausência de publicação."
        )
        detail.configure(state="normal")
        detail.delete("1.0", "end")
        detail.configure(state="disabled")

    def run_query():
        if state["running"]:
            return
        try:
            name, territory_id = validate_search(person_name, city.get())
        except ValueError as exc:
            messagebox.showwarning("Dados da consulta", str(exc), parent=dialog)
            return
        approved = messagebox.askyesno(
            "Autorizar consulta externa?",
            "O seu nome completo será enviado à API pública do Querido Diário "
            "para pesquisar possíveis menções no município escolhido.\n\n"
            "Esta consulta não cria monitoramento, cadastro ou alertas.\n\n"
            "Deseja continuar?",
            parent=dialog,
        )
        if not approved:
            status.set("Consulta cancelada. Nenhum nome foi transmitido.")
            return

        state["running"] = True
        search_button.state(["disabled"])
        city_entry.state(["disabled"])
        status.set("Consultando o Querido Diário... procurando menções.")
        activity.pack(fill="x", pady=(0, 8), before=frame)
        activity.start(15)

        def worker():
            try:
                result = search_gazettes(name, territory_id)
                events.put(("ok", result))
            except (OnlineSearchError, ValueError) as exc:
                events.put(("error", str(exc)))
            except Exception:
                events.put(("error", "Ocorreu uma falha inesperada na consulta."))

        Thread(target=worker, daemon=True).start()
        dialog.after(100, poll)

    search_button.configure(command=run_query)
    open_button.configure(command=open_original)
    tree.bind("<<TreeviewSelect>>", select_result)
    tree.bind("<Double-1>", open_original)
    city_entry.focus_set()
