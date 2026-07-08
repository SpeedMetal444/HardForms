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


# Grayscale palette
_GRAY_900 = HexColor("#1F2937")
_GRAY_800 = HexColor("#374151")
_GRAY_700 = HexColor("#4B5563")
_GRAY_600 = HexColor("#6B7280")
_GRAY_500 = HexColor("#9CA3AF")
_GRAY_400 = HexColor("#D1D5DB")
_GRAY_300 = HexColor("#DEE2E6")
_GRAY_200 = HexColor("#E5E7EB")
_GRAY_100 = HexColor("#F3F4F6")
_GRAY_50  = HexColor("#F9FAFB")
_WHITE    = colors.white
_BLACK    = HexColor("#111827")


def _header_footer(canvas, doc):
    inst = get_institution()
    canvas.saveState()

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
            a = a.point(lambda x: int(x * 0.12))
            img = PILImage.merge("RGBA", (r, g, b, a))
            buf = BytesIO()
            img.save(buf, format="PNG")
            buf.seek(0)
            reader = ImageReader(buf)
            canvas.drawImage(reader, x=10.5*cm, y=18*cm, width=8*cm, height=10*cm,
                             preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    canvas.setStrokeColor(_GRAY_400)
    canvas.setLineWidth(0.5)
    canvas.line(2.5 * cm, A4[1] - 1.5 * cm, A4[0] - 2.5 * cm, A4[1] - 1.5 * cm)

    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(_GRAY_500)
    canvas.drawCentredString(A4[0] / 2, 1.2 * cm, inst["name"])
    canvas.drawRightString(A4[0] - 2.5 * cm, 1.2 * cm, f"Pág. {canvas.getPageNumber()}")
    canvas.restoreState()


def _section(text, body, styles, col_width=16 * cm):
    header = Table(
        [[Paragraph(text, styles["SectionTitle"])]],
        colWidths=[col_width],
        style=[
            ("BACKGROUND", (0, 0), (-1, -1), _GRAY_700),
            ("TEXTCOLOR", (0, 0), (-1, -1), _WHITE),
            ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
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
        ("LINEBELOW", (0, -1), (-1, -1), 0.5, _GRAY_300),
        ("BACKGROUND", (0, 1), (-1, -1), _GRAY_50),
    ]))
    return t


def _kv_table(data, styles, col_widths=None, label_width=4.5 * cm):
    if col_widths is None:
        col_widths = [label_width, 16 * cm - label_width]
    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), _GRAY_800),
        ("TEXTCOLOR", (1, 0), (1, -1), _GRAY_900),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, _GRAY_200),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
    ]))
    return t


def _build_header(styles, col_width=16 * cm):
    INSTITUTION = get_institution()
    elements = []

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
    elements.append(Table([[""]], colWidths=[col_width],
        style=[("LINEBELOW", (0, 0), (-1, -1), 2, _GRAY_500)]))
    elements.append(Spacer(1, 3 * mm))
    return elements


def _build_footer(styles):
    INSTITUTION = get_institution()
    elements = []
    elements.append(Spacer(1, 1.5 * cm))
    elements.append(Table([[""]], colWidths=[16 * cm],
        style=[("LINEABOVE", (0, 0), (-1, -1), 0.5, _GRAY_400)]))
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
                           fontSize=7, textColor=_GRAY_500, alignment=TA_CENTER)))
    return elements


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


def _compact_table(pairs, styles, col_widths=None, font_size=9):
    if col_widths is None:
        col_widths = [3.2 * cm, 4.8 * cm, 3.2 * cm, 4.8 * cm]
    kv_rows = []
    for l1, v1, l2, v2 in pairs:
        kv_rows.append([
            Paragraph(f"<b>{l1}:</b>", styles["CellLabel"]),
            Paragraph(v1, styles["CellValue"]),
            Paragraph(f"<b>{l2}:</b>" if l2 else "", styles["CellLabel"]),
            Paragraph(v2 if l2 else "", styles["CellValue"]),
        ])
    t = Table(kv_rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, _GRAY_200),
        ("LEFTPADDING", (0, 0), (-1, -1), 2 * mm),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
    ]))
    return t


def _img_header(text, styles, col_width=16 * cm):
    return Table(
        [[Paragraph(text, styles["SectionTitle"])]],
        colWidths=[col_width],
        style=[
            ("BACKGROUND", (0, 0), (-1, -1), _GRAY_700),
            ("TEXTCOLOR", (0, 0), (-1, -1), _WHITE),
            ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
        ]
    )


def _diagnosis_table(diagnoses, col_width=16 * cm):
    diag_data = [["Diagnóstico", "Fecha"]]
    for d in diagnoses:
        diag_data.append([d.description, d.date or "—"])
    diag_table = Table(diag_data, colWidths=[12 * cm, 4 * cm])
    diag_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BACKGROUND", (0, 0), (-1, 0), _GRAY_700),
        ("TEXTCOLOR", (0, 0), (-1, 0), _WHITE),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [_GRAY_50, _WHITE]),
        ("GRID", (0, 0), (-1, -1), 0.5, _GRAY_300),
        ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
    ]))
    return diag_table


def generate_full_report(patient_id: int, output_path: str):
    patient = get_patient(patient_id)
    if patient is None:
        raise ValueError(f"Paciente ID {patient_id} no encontrado")

    diagnoses = get_diagnoses_for_patient(patient_id)

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
        fontSize=20, textColor=_GRAY_900, spaceAfter=2 * mm,
        alignment=TA_CENTER, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("InstInfo", parent=styles["Normal"],
        fontSize=10, textColor=_GRAY_600,
        alignment=TA_CENTER, spaceAfter=1 * mm, leading=13))
    styles.add(ParagraphStyle("ReportTitle", parent=styles["Heading2"],
        fontSize=16, textColor=_GRAY_800,
        spaceBefore=6 * mm, spaceAfter=5 * mm, alignment=TA_CENTER,
        fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("SectionTitle", parent=styles["Normal"],
        fontSize=10, textColor=_WHITE,
        alignment=TA_LEFT, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("CellLabel", parent=styles["Normal"],
        fontSize=9, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("CellValue", parent=styles["Normal"],
        fontSize=9))
    styles.add(ParagraphStyle("DescText", parent=styles["Normal"],
        fontSize=10, leading=16,
        spaceBefore=3 * mm, spaceAfter=5 * mm, alignment=TA_JUSTIFY))
    styles.add(ParagraphStyle("ImgDesc", parent=styles["Normal"],
        fontSize=8, leading=11, textColor=_GRAY_700,
        alignment=TA_CENTER, spaceBefore=1 * mm, spaceAfter=1 * mm,
        fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("ImgErr", parent=styles["Normal"],
        fontSize=8, textColor=_GRAY_500))

    elements = []
    elements.extend(_build_header(styles))
    elements.append(Paragraph("INFORME MÉDICO COMPLETO", styles["ReportTitle"]))

    edad = _calcular_edad(patient.birth_date) if patient.birth_date else "—"

    paciente_pairs = [
        ("Apellido y Nombre", patient.full_name, "DNI", patient.dni or "—"),
        ("HC", patient.medical_record_number or "—", "Afiliado", patient.insurance or "—"),
        ("Afiliado Nº", patient.insurance_number or "—", "Nacimiento", patient.birth_date or "—"),
        ("Edad", edad, "Teléfono", patient.phone or "—"),
        ("Médico", patient.doctor or "—", "Médico derivante", patient.referring_doctor or "—"),
        ("Estudio", patient.study_type or "—", "Centro", patient.center or "—"),
        ("Email", patient.email or "—", "Domicilio", patient.address or "—"),
    ]
    elements.append(_section("Datos del Paciente", _compact_table(paciente_pairs, styles), styles))
    elements.append(Spacer(1, 4 * mm))

    anestesia_pairs = [
        ("Anestesia", patient.anesthesia_type or "—", "Droga", patient.drug or "—"),
        ("Postoperatorio", patient.postop or "—", "Anestesiólogo", patient.anesthesiologist or "—"),
        ("Escala Boston", patient.boston_scale or "—", "", ""),
    ]
    elements.append(_section("Anestesia / Preparación", _compact_table(anestesia_pairs, styles), styles))
    elements.append(Spacer(1, 4 * mm))

    if diagnoses:
        elements.append(Spacer(1, 2 * mm))
        elements.append(_diagnosis_table(diagnoses))
        elements.append(Spacer(1, 4 * mm))

    if patient.description:
        elements.append(PageBreak())
        elements.append(_section("Informe Médico",
            Paragraph(patient.description.replace("\n", "<br/>"), styles["DescText"]), styles))
        elements.append(Spacer(1, 4 * mm))

    if patient.attachments:
        elements.append(_img_header("Imágenes Adjuntas", styles))
        rows = []
        for i in range(0, len(patient.attachments), 3):
            cells = []
            for j in range(3):
                idx = i + j
                if idx >= len(patient.attachments):
                    cells.append(Paragraph(""))
                    continue
                att = patient.attachments[idx]
                if not os.path.isfile(att.path):
                    cells.append(Paragraph(f"(no encontrada)", styles["ImgErr"]))
                    continue
                try:
                    inner = [RLImage(att.path, width=5.3 * cm, height=12 * cm, kind="proportional")]
                    if att.description:
                        inner.append(Spacer(1, 1 * mm))
                        inner.append(Paragraph(att.description, styles["ImgDesc"]))
                    cells.append(inner)
                except Exception:
                    cells.append(Paragraph(f"(error)", styles["ImgErr"]))
            rows.append(cells)
        if rows:
            img_table = Table(rows, colWidths=[5.33 * cm, 5.33 * cm, 5.33 * cm])
            img_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 1 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            elements.append(img_table)

    elements.extend(_build_footer(styles))
    doc.build(elements, onFirstPage=_header_footer, onLaterPages=_header_footer)


def generate_summary_report(patient_id: int, output_path: str):
    patient = get_patient(patient_id)
    if patient is None:
        raise ValueError(f"Paciente ID {patient_id} no encontrado")

    diagnoses = get_diagnoses_for_patient(patient_id)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("InstName", parent=styles["Heading1"],
        fontSize=14, textColor=_GRAY_900, spaceAfter=1 * mm,
        alignment=TA_CENTER, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("InstInfo", parent=styles["Normal"],
        fontSize=7, textColor=_GRAY_600,
        alignment=TA_CENTER, spaceAfter=1 * mm, leading=9))
    styles.add(ParagraphStyle("SectionTitle", parent=styles["Normal"],
        fontSize=8, textColor=_WHITE,
        alignment=TA_LEFT, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("CellLabel", parent=styles["Normal"],
        fontSize=7.5, fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("CellValue", parent=styles["Normal"],
        fontSize=7.5))
    styles.add(ParagraphStyle("ImgDesc", parent=styles["Normal"],
        fontSize=7, leading=9, textColor=_GRAY_700,
        alignment=TA_CENTER, spaceBefore=0.5 * mm, spaceAfter=0.5 * mm,
        fontName="Helvetica-Bold"))
    styles.add(ParagraphStyle("ImgErr", parent=styles["Normal"],
        fontSize=6, textColor=_GRAY_500))
    styles.add(ParagraphStyle("DiagText", parent=styles["Normal"],
        fontSize=7.5, leading=10))
    styles.add(ParagraphStyle("DescText", parent=styles["Normal"],
        fontSize=7.5, leading=11,
        spaceBefore=1 * mm, spaceAfter=2 * mm, alignment=TA_JUSTIFY))

    elements = []
    elements.extend(_build_header(styles))

    pairs = [
        ("Paciente", patient.full_name, "DNI", patient.dni or "—"),
        ("HC", patient.medical_record_number or "—", "Afiliado", patient.insurance or "—"),
        ("Nacimiento", f"{patient.birth_date or '—'} ({_calcular_edad(patient.birth_date) if patient.birth_date else '—'})",
         "Médico", patient.doctor or "—"),
        ("Estudio", patient.study_type or "—", "Centro", patient.center or "—"),
    ]
    compact_table = _compact_table(pairs, styles,
                                   col_widths=[2.2 * cm, 5.8 * cm, 2.2 * cm, 5.8 * cm],
                                   font_size=7.5)
    elements.append(_section("Datos del Paciente", compact_table, styles))
    elements.append(Spacer(1, 2 * mm))

    if diagnoses:
        diag_text = "<br/>".join(
            f"<b>{d.description}</b>  ({d.date or '—'})" for d in diagnoses
        )
        elements.append(_section("Diagnósticos",
            Paragraph(diag_text, styles["DiagText"]), styles))
        elements.append(Spacer(1, 2 * mm))

    if patient.description:
        elements.append(_section("Informe Médico",
            Paragraph(patient.description.replace("\n", "<br/>"), styles["DescText"]), styles))
        elements.append(Spacer(1, 2 * mm))

    if patient.attachments:
        imgs = patient.attachments[:3]
        elements.append(_img_header("Imágenes", styles))
        cells = []
        for att in imgs:
            if not os.path.isfile(att.path):
                cells.append(Paragraph("", styles["ImgErr"]))
                continue
            try:
                inner = [RLImage(att.path, width=5.3 * cm, height=12 * cm, kind="proportional")]
                if att.description:
                    inner.append(Spacer(1, 1 * mm))
                    inner.append(Paragraph(att.description, styles["ImgDesc"]))
                cells.append(inner)
            except Exception:
                cells.append(Paragraph(f"(error)", styles["ImgErr"]))
        while len(cells) < 3:
            cells.append(Paragraph(""))
        img_table = Table([cells], colWidths=[5.33 * cm, 5.33 * cm, 5.33 * cm])
        img_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 1 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        elements.append(img_table)

    elements.extend(_build_footer(styles))
    doc.build(elements, onFirstPage=_header_footer, onLaterPages=_header_footer)
