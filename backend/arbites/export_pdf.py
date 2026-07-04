"""Export da matriz de rastreabilidade em PDF (fpdf2 — puro Python)."""

from __future__ import annotations

from fpdf import FPDF

# fonte core (Helvetica) é latin-1; troca o que não codifica
def _latin1(text: str) -> str:
    return text.encode("latin-1", "replace").decode("latin-1")


COLUMNS = [
    ("Epic / Story", 70),
    ("CTs", 12),
    ("Ultimo resultado", 30),
    ("Execution", 25),
    ("Evid.", 12),
    ("Defeitos", 30),
]


def matrix_pdf(matrix: dict) -> bytes:
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, "Matriz de rastreabilidade", new_x="LMARGIN", new_y="NEXT")
    if matrix.get("sprint_filter"):
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, _latin1(f"Sprint: {matrix['sprint_filter']}"),
                 new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 8)
    for title, width in COLUMNS:
        pdf.cell(width * 1.5, 6, _latin1(title), border=1)
    pdf.ln()

    for epic in matrix["epics"]:
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(sum(w for _, w in COLUMNS) * 1.5, 6,
                 _latin1(f"{epic['id']} {epic['title']}"), border=1,
                 new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 8)
        for story in epic["stories"]:
            status = story["last_status"] or (
                "sem execucao" if story["covered"] else "sem cobertura"
            )
            defects = ", ".join(d["id"] for d in story["defects"]) or "-"
            cells = [
                f"  {story['id']} {story['title']}",
                str(story["ct_count"]),
                status,
                story["last_execution"] or "-",
                str(story["evidence_count"]),
                defects,
            ]
            for (title, width), value in zip(COLUMNS, cells):
                pdf.cell(width * 1.5, 6, _latin1(value), border=1)
            pdf.ln()

    return bytes(pdf.output())
