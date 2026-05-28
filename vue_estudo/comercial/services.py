import re
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.utils import timezone


PLACEHOLDER_RE = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


def extract_placeholders(file_path):
    path = Path(file_path)
    suffix = path.suffix.lower()
    text = ""

    if suffix == ".docx":
        try:
            from docx import Document
        except ImportError:
            return []
        document = Document(str(path))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        for table in document.tables:
            for row in table.rows:
                text += "\n" + " ".join(cell.text for cell in row.cells)
    elif suffix == ".pdf":
        try:
            import fitz
        except ImportError:
            return []
        with fitz.open(str(path)) as doc:
            text = "\n".join(page.get_text() for page in doc)
    else:
        text = path.read_text(encoding="utf-8", errors="ignore")

    return sorted(set(PLACEHOLDER_RE.findall(text)))


def render_document_with_values(contrato):
    original = Path(contrato.documento_modelo.path)
    output_dir = Path(settings.MEDIA_ROOT) / "documentos" / "finais"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_name = f"contrato_{contrato.pk}_{timezone.now().strftime('%Y%m%d%H%M%S')}{original.suffix}"
    output_path = output_dir / output_name

    suffix = original.suffix.lower()
    values = contrato.valores_preenchidos or {}

    if suffix == ".docx":
        _render_docx(original, output_path, values)
    elif suffix == ".pdf":
        _render_pdf(original, output_path, values)
    else:
        text = original.read_text(encoding="utf-8", errors="ignore")
        output_path.write_text(_replace_text(text, values), encoding="utf-8")

    with output_path.open("rb") as final_file:
        contrato.documento_final.save(output_name, File(final_file), save=True)

    return contrato.documento_final


def _replace_text(text, values):
    for key, value in values.items():
        text = re.sub(r"{{\s*" + re.escape(key) + r"\s*}}", str(value), text)
    return text


def _render_docx(original, output_path, values):
    from docx import Document

    document = Document(str(original))

    for paragraph in document.paragraphs:
        _replace_in_runs(paragraph.runs, values)

    for table in document.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    _replace_in_runs(paragraph.runs, values)

    document.save(str(output_path))


def _replace_in_runs(runs, values):
    for run in runs:
        run.text = _replace_text(run.text, values)


def _render_pdf(original, output_path, values):
    import fitz

    with fitz.open(str(original)) as doc:
        for page in doc:
            for key, value in values.items():
                token = "{{" + key + "}}"
                areas = page.search_for(token)
                for rect in areas:
                    page.add_redact_annot(rect, fill=(1, 1, 1))
                    page.apply_redactions()
                    page.insert_text(
                        rect.bottom_left,
                        str(value),
                        fontsize=max(rect.height * 0.8, 8),
                        color=(0, 0, 0),
                    )
        doc.save(str(output_path))


def gerar_pdf_orcamento(orcamento):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Frame, Paragraph

    output_dir = Path(settings.MEDIA_ROOT) / "orcamentos"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"orcamento_{orcamento.pk}.pdf"

    c = canvas.Canvas(str(output_path), pagesize=A4)
    width, height = A4
    amarelo = colors.HexColor("#FFC52F")
    vermelho = colors.HexColor("#D8332F")
    preto = colors.HexColor("#191919")

    logo = orcamento.logo.path if orcamento.logo else None
    if not logo:
        from .models import ConfiguracaoEmpresa

        configuracao = ConfiguracaoEmpresa.objects.first()
        if configuracao and configuracao.logo:
            logo = configuracao.logo.path
    fallback_logo = Path(settings.BASE_DIR) / "logo2.png"
    logo = logo or (str(fallback_logo) if fallback_logo.exists() else None)

    if logo:
        c.drawImage(logo, 2 * cm, height - 4 * cm, width=4.5 * cm, height=2 * cm, preserveAspectRatio=True, mask="auto")

    c.setFillColor(preto)
    c.setFont("Helvetica-Bold", 26)
    c.drawString(2 * cm, height - 5.2 * cm, f"Orçamento #{orcamento.pk}")
    c.setFont("Helvetica", 11)
    c.drawString(2 * cm, height - 6 * cm, f"Cliente: {orcamento.cliente.nome_completo}")
    c.drawString(2 * cm, height - 6.6 * cm, f"CPF: {orcamento.cliente.cpf} | Email: {orcamento.cliente.email}")
    c.drawString(2 * cm, height - 7.2 * cm, f"Pagamento: {orcamento.get_forma_pagamento_display()}")

    y = height - 8.5 * cm
    c.setFillColor(vermelho)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, y, "Produtos")
    y -= 0.7 * cm
    y = _draw_items(c, y, orcamento.itens_produto.all(), lambda item: item.produto.nome)

    y -= 0.4 * cm
    c.setFillColor(vermelho)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2 * cm, y, "Serviços")
    y -= 0.7 * cm
    y = _draw_items(c, y, orcamento.itens_servico.all(), lambda item: item.servico.nome)

    c.setFillColor(amarelo)
    c.roundRect(2 * cm, 3.1 * cm, width - 4 * cm, 1.3 * cm, 0.2 * cm, fill=1, stroke=0)
    c.setFillColor(preto)
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(width - 2.2 * cm, 3.55 * cm, f"Total: R$ {orcamento.valor_total:.2f}")

    if orcamento.observacoes:
        style = ParagraphStyle("obs", fontName="Helvetica", fontSize=10, leading=13, textColor=preto)
        frame = Frame(2 * cm, 1.5 * cm, width - 4 * cm, 1.2 * cm, showBoundary=0)
        frame.addFromList([Paragraph(orcamento.observacoes, style)], c)

    c.save()
    with output_path.open("rb") as pdf_file:
        orcamento.arquivo_pdf.save(output_path.name, File(pdf_file), save=True)

    return orcamento.arquivo_pdf


def _draw_items(c, y, items, label_getter):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm

    c.setFillColor(colors.HexColor("#191919"))
    c.setFont("Helvetica", 10)
    if not items:
        c.drawString(2 * cm, y, "Nenhum item informado.")
        return y - 0.5 * cm

    for item in items:
        if y < 5 * cm:
            c.showPage()
            y = A4[1] - 2 * cm
            c.setFont("Helvetica", 10)
        c.drawString(2 * cm, y, label_getter(item))
        c.drawRightString(15 * cm, y, f"{item.quantidade} x R$ {item.valor_unitario:.2f}")
        c.drawRightString(19 * cm, y, f"R$ {item.total:.2f}")
        y -= 0.55 * cm
    return y
