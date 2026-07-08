import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from PIL import Image as PILImage

from database.db import get_patient, get_diagnoses_for_patient
from config.institution import get_institution


def _header_footer(canvas, doc):
    inst = get_institution()
    canvas.saveState()

    # Watermark: logo transparente al fondo
    wm_path = inst.get("watermark_path", "")
    if not os.path.isfile(wm_path):
        logo_path = inst.get("logo_path", "")
        if not os.path.isfile(logo_path):
            logo_path = inst.get("default_logo", "")
        wm_path = logo_path
    if os.path.isfile(wm_path):
        try:
            img = PILImage.open(wm_path).convert("RGBA")
            r, g, b, a = img.split()
            a = a.point(lambda x: int(x * 0.08))
            img = PILImage.merge("RGBA", (r, g, b, a))
            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            reader = ImageReader(buf)
            w, h = A4
            canvas.drawImage(reader, x=2*cm, y=3*cm, width=w-4*cm, height=h-6*cm,
                             preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    # Header line
    canvas.setStrokeColor(HexColor("#2980B9"))
    canvas.setLineWidth(0.5)
    canvas.line(2.5 * cm, A4[1] - 1.5 * cm, A4[0] - 2.5 * cm, A4[1] - 1.5 * cm)

    # Footer
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(HexColor("#95A5A6"))
    canvas.drawCentredString(A4[0] / 2, 1.2 * cm, inst["name"])
    canvas.drawRightString(A4[0] - 2.5 * cm, 1.2 * cm, f"Pág. {canvas.getPageNumber()}")
    canvas.restoreState()


def _section(text, body, styles, col_width=16 * cm):
    header = Table(
        [[Paragraph(text, styles["SectionTitle"])]],
        colWidths=[col_width],
        style=[
            ("BACKGROUND", (0, 0), (-1, -1), HexColor("#2980B9")),
            ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
            ("TOPPADDING", (0, 0), (-1, -1), 4 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
        ]
    )
    rows = [[header]]
    if body:
        rows.append([body])
    t = Table(rows, colWidths=[col_width])
    t.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, HexColor("#D5D8DC")),
    ]))
    return t


def _kv_table(data, styles, col_widths=None, label_width=4.5 * cm):
    if col_widths is None:
        col_widths = [label_width, 16 * cm - label_width]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), HexColor("#2C3E50")),
        ("TEXTCOLOR", (1, 0), (1, -1), HexColor("#34495E")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, HexColor("#E8E8E8")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
    ]))
    return t


def generate_patient_report(patient_id: int, output_path: str):
    patient = get_patient(patient_id)
    if patient is None:
        raise ValueError(f"Paciente ID {patient_id} no encontrado")

    diagnoses = get_diagnoses_for_patient(patient_id)
    INSTITUTION = get_institution()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=2.2 * cm,
        bottomMargin=2.2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("InstName", parent=styles["Heading1"],
        fontSize=20, textColor=HexColor("#2980B9"), spaceAfter=2 * mm,
        alignment=TA_CENTER, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("InstInfo", parent=styles["Normal"],
        fontSize=10, textColor=HexColor("#34495E"),
        alignment=TA_CENTER, spaceAfter=1 * mm, leading=13))
    styles.add(ParagraphStyle("ReportTitle", parent=styles["Heading2"],
        fontSize=16, textColor=HexColor("#2980B9"),
        spaceBefore=6 * mm, spaceAfter=5 * mm, alignment=TA_CENTER,
        fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("SectionTitle", parent=styles["Normal"],
        fontSize=10, textColor=colors.white,
        alignment=TA_LEFT, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("DescText", parent=styles["Normal"],
        fontSize=10, leading=16,
        spaceBefore=3 * mm, spaceAfter=5 * mm, alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle("ImgDesc", parent=styles["Normal"],
        fontSize=9, leading=12, textColor=HexColor("#2C3E50"),
        alignment=TA_CENTER, spaceBefore=2 * mm, spaceAfter=3 * mm,
        fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("ImgErr", parent=styles["Normal"],
        fontSize=8, textColor=HexColor("#E74C3C")))

    elements = []

    # ===== HEADER =====
    logo_path = INSTITUTION.get("logo_path", "")
    if not os.path.isfile(logo_path):
        logo_path = INSTITUTION.get("default_logo", "")
    header_img = None
    if os.path.isfile(logo_path):
        try:
            header_img = RLImage(logo_path, width=3.5 * cm, height=1.8 * cm, kind="proportional")
        except Exception:
            pass

    details = " | ".join(filter(None, [
        INSTITUTION.get("address"),
        f"Tel: {INSTITUTION['phone']}" if INSTITUTION.get("phone") else None,
        f"MP: {INSTITUTION['mp_number']}" if INSTITUTION.get("mp_number") else None,
        INSTITUTION.get("email"),
        INSTITUTION.get("web"),
        f"Dr. {INSTITUTION['doctor_name']}" if INSTITUTION.get("doctor_name") else None,
    ]))

    if header_img:
        right = Table(
            [[Paragraph(INSTITUTION["name"], styles["InstName"])],
             [Paragraph(details, styles["InstInfo"])]],
            colWidths=[11.5 * cm],
            style=[("ALIGN", (0, 0), (-1, -1), "LEFT"),
                   ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                   ("TOPPADDING", (0, 0), (-1, -1), 0),
                   ("BOTTOMPADDING", (0, 0), (-1, -1), 0)])
        elements.append(Table([[header_img, right]],
            colWidths=[4.5 * cm, 11.5 * cm],
            style=[("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                   ("LEFTPADDING", (0, 0), (0, 0), 0),
                   ("RIGHTPADDING", (1, 0), (1, 0), 0)]))
    else:
        elements.append(Paragraph(INSTITUTION["name"], styles["InstName"]))
        if details:
            elements.append(Paragraph(details, styles["InstInfo"]))

    elements.append(Spacer(1, 3 * mm))
    elements.append(Table([[""]], colWidths=[16 * cm],
        style=[("LINEBELOW", (0, 0), (-1, -1), 2, HexColor("#2980B9"))]))
    elements.append(Spacer(1, 3 * mm))
    elements.append(Paragraph("INFORME MÉDICO", styles["ReportTitle"]))

    # ===== DATOS DEL PACIENTE (con Médico Operador incluido) =====
    data = [
        ["Apellido y Nombre", patient.full_name],
        ["DNI", patient.dni or "—"],
        ["Nro. Historia Clínica", patient.medical_record_number or "—"],
        ["Afiliado", patient.insurance or "—"],
        ["Afiliado Nº", patient.insurance_number or "—"],
        ["Fecha de nacimiento", patient.birth_date or "—"],
        ["Edad", _calcular_edad(patient.birth_date) if patient.birth_date else "—"],
        ["Teléfono", patient.phone or "—"],
        ["Médico derivante", patient.referring_doctor or "—"],
        ["Tipo de estudio", patient.study_type or "—"],
        ["Centro", patient.center or "—"],
        ["Médico Operador", patient.doctor or "—"],
        ["Email", patient.email or "—"],
        ["Domicilio", patient.address or "—"],
    ]
    elements.append(_section("Datos del Paciente", _kv_table(data, styles), styles))
    elements.append(Spacer(1, 4 * mm))

    # ===== DIAGNÓSTICOS =====
    if diagnoses:
        diag_data = [["Diagnóstico", "Fecha"]]
        for d in diagnoses:
            diag_data.append([d.description, d.date or "—"])
        diag_table = Table(diag_data, colWidths=[12 * cm, 4 * cm])
        diag_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2980B9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#F8F9FA"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#D5D8DC")),
            ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ]))
        elements.append(Spacer(1, 2 * mm))
        elements.append(diag_table)
        elements.append(Spacer(1, 4 * mm))

    # ===== INFORME MÉDICO =====
    if patient.description:
        elements.append(PageBreak())
        elements.append(_section("Informe Médico",
            Paragraph(patient.description.replace("\n", "<br/>"), styles["DescText"]), styles))
        elements.append(Spacer(1, 4 * mm))

    # ===== IMÁGENES =====
    if patient.attachments:
        rows = []
        for i in range(0, len(patient.attachments), 2):
            cells = []
            for j in range(2):
                idx = i + j
                if idx >= len(patient.attachments):
                    cells.append(Paragraph(""))
                    continue
                att = patient.attachments[idx]
                if not os.path.isfile(att.path):
                    cells.append(Paragraph(f"(no encontrada: {os.path.basename(att.path)})",
                                           styles["ImgErr"]))
                    continue
                try:
                    inner = [RLImage(att.path, width=7 * cm, height=5 * cm, kind="proportional")]
                    if att.description:
                        inner.append(Spacer(1, 1 * mm))
                        inner.append(Paragraph(att.description, styles["ImgDesc"]))
                    cells.append(inner)
                except Exception:
                    cells.append(Paragraph(f"(error: {os.path.basename(att.path)})",
                                           styles["ImgErr"]))
            rows.append(cells)
        if rows:
            img_table = Table(rows, colWidths=[7.5 * cm, 7.5 * cm])
            img_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
                ("BOX", (0, 0), (-1, -1), 0.75, HexColor("#BDC3C7")),
                ("BACKGROUND", (0, 0), (-1, -1), HexColor("#FFFFFF")),
            ]))
            elements.append(_section("Imágenes Adjuntas", img_table, styles))

    # ===== FOOTER =====
    elements.append(Spacer(1, 1.5 * cm))
    elements.append(Table([[""]], colWidths=[16 * cm],
        style=[("LINEABOVE", (0, 0), (-1, -1), 0.5, HexColor("#BDC3C7"))]))
    elements.append(Spacer(1, 2 * mm))
    footer_parts = []
    if INSTITUTION.get("footer_text"):
        footer_parts.append(INSTITUTION["footer_text"])
    doc_parts = []
    if INSTITUTION.get("doctor_name"):
        doc_parts.append(f"Dr. {INSTITUTION['doctor_name']}")
    if INSTITUTION.get("mp_number"):
        doc_parts.append(f"MP: {INSTITUTION['mp_number']}")
    if doc_parts:
        footer_parts.append(" | ".join(doc_parts))
    if footer_parts:
        elements.append(Paragraph(
            "<br/>".join(footer_parts),
            ParagraphStyle("Footer", parent=styles["Normal"],
                           fontSize=7, textColor=HexColor("#95A5A6"), alignment=TA_CENTER)))

    doc.build(elements, onFirstPage=_header_footer, onLaterPages=_header_footer)


def _calcular_edad(birth_date: str) -> str:
    import datetime
    try:
        day, month, year = birth_date.split("/")
        nac = datetime.date(int(year), int(month), int(day))
        hoy = datetime.date.today()
        edad = hoy.year - nac.year - ((hoy.month, hoy.day) < (nac.month, nac.day))
        return f"{edad} años"
    except Exception:
        return "—"
