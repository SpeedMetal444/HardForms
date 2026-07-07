import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.colors import HexColor

from database.db import get_patient, get_diagnoses_for_patient
from config.institution import INSTITUTION


def _header_footer(canvas, doc):
    canvas.saveState()
    # Header line
    canvas.setStrokeColor(HexColor("#2C3E50"))
    canvas.setLineWidth(0.5)
    canvas.line(2.5 * cm, A4[1] - 1.5 * cm, A4[0] - 2.5 * cm, A4[1] - 1.5 * cm)
    # Footer
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(HexColor("#95A5A6"))
    canvas.drawCentredString(A4[0] / 2, 1.2 * cm, INSTITUTION["name"])
    canvas.drawRightString(A4[0] - 2.5 * cm, 1.2 * cm, f"Pág. {canvas.getPageNumber()}")
    canvas.restoreState()


def generate_patient_report(patient_id: int, output_path: str):
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

    styles.add(ParagraphStyle(
        "InstitutionName", parent=styles["Heading1"],
        fontSize=20, textColor=HexColor("#2C3E50"), spaceAfter=2 * mm,
        alignment=TA_CENTER, fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        "InstitutionInfo", parent=styles["Normal"],
        fontSize=8, textColor=HexColor("#7F8C8D"),
        alignment=TA_CENTER, spaceAfter=1 * mm, leading=11
    ))
    styles.add(ParagraphStyle(
        "ReportTitle", parent=styles["Heading2"],
        fontSize=14, textColor=HexColor("#2980B9"),
        spaceBefore=6 * mm, spaceAfter=4 * mm, alignment=TA_CENTER,
        fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        "SectionTitle", parent=styles["Heading2"],
        fontSize=12, textColor=HexColor("#2C3E50"),
        spaceBefore=5 * mm, spaceAfter=3 * mm,
        fontName="Helvetica-Bold"
    ))
    styles.add(ParagraphStyle(
        "DescriptionText", parent=styles["Normal"],
        fontSize=10, leading=16,
        spaceBefore=2 * mm, spaceAfter=4 * mm,
        alignment=TA_JUSTIFY
    ))

    elements = []

    # ===== HEADER =====
    logo_path = INSTITUTION.get("logo_path", "")
    if not os.path.isfile(logo_path):
        logo_path = INSTITUTION.get("default_logo", "")

    header_parts = []
    if os.path.isfile(logo_path):
        try:
            img = RLImage(logo_path, width=3.5 * cm, height=1.8 * cm)
            header_parts.append(img)
        except Exception:
            pass

    info_lines = [
        f"<b>{INSTITUTION['name']}</b>",
        f"{INSTITUTION['address']} | Tel: {INSTITUTION['phone']}",
        f"{INSTITUTION['email']} | {INSTITUTION['web']}",
    ]
    info_text = Paragraph("<br/>".join(info_lines), styles["InstitutionInfo"])

    if header_parts:
        header_table = Table(
            [[header_parts[0], info_text]],
            colWidths=[4.5 * cm, 11.5 * cm],
            style=[
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, 0), 0),
                ("RIGHTPADDING", (1, 0), (1, 0), 0),
            ]
        )
        elements.append(header_table)
    else:
        elements.append(Paragraph(INSTITUTION["name"], styles["InstitutionName"]))
        elements.append(Paragraph(
            f"{INSTITUTION['address']} | Tel: {INSTITUTION['phone']}",
            styles["InstitutionInfo"]
        ))

    elements.append(Spacer(1, 2 * mm))

    # Separator
    elements.append(Table([[""]], colWidths=[16 * cm],
                          style=[("LINEBELOW", (0, 0), (-1, -1), 1.5, HexColor("#2980B9"))]))
    elements.append(Spacer(1, 3 * mm))

    # Report title
    elements.append(Paragraph("INFORME MÉDICO", styles["ReportTitle"]))

    # ===== PATIENT DATA =====
    elements.append(Paragraph("Datos del Paciente", styles["SectionTitle"]))

    data = [
        ["Apellido y Nombre", patient.full_name],
        ["DNI", patient.dni or "—"],
        ["Afiliado", patient.insurance or "—"],
        ["Afiliado Nº", patient.insurance_number or "—"],
        ["Fecha de nacimiento", patient.birth_date or "—"],
        ["Edad", _calcular_edad(patient.birth_date) if patient.birth_date else "—"],
        ["Teléfono", patient.phone or "—"],
        ["Email", patient.email or "—"],
        ["Domicilio", patient.address or "—"],
        ["Nro. Historia Clínica", patient.medical_record_number or "—"],
    ]

    t = Table(data, colWidths=[5 * cm, 11 * cm])
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), HexColor("#2C3E50")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, HexColor("#ECF0F1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4 * mm),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 4 * mm))

    # ===== DIAGNOSES =====
    if diagnoses:
        elements.append(Paragraph("Diagnósticos", styles["SectionTitle"]))

        diag_data = [["Diagnóstico", "Fecha"]]
        for d in diagnoses:
            diag_data.append([d.description, d.date or "—"])

        diag_table = Table(diag_data, colWidths=[12 * cm, 4 * cm])
        diag_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#2980B9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [HexColor("#F8F9FA"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#D5D8DC")),
            ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ]))
        elements.append(diag_table)
        elements.append(Spacer(1, 4 * mm))

    # ===== MEDICAL REPORT =====
    if patient.description:
        elements.append(Paragraph("Informe Médico", styles["SectionTitle"]))
        elements.append(Paragraph(
            patient.description.replace("\n", "<br/>"),
            styles["DescriptionText"]
        ))

    # ===== IMAGES =====
    if patient.attachments:
        elements.append(Spacer(1, 2 * mm))
        elements.append(Paragraph("Imágenes Adjuntas", styles["SectionTitle"]))
        for att in patient.attachments:
            if os.path.isfile(att.path):
                try:
                    img = RLImage(att.path, width=14 * cm, height=9 * cm, kind="proportional")
                    elements.append(Spacer(1, 2 * mm))
                    elements.append(img)
                    if att.description:
                        elements.append(Paragraph(
                            f"<i>{att.description}</i>",
                            ParagraphStyle("ImgDesc", parent=styles["Normal"],
                                           fontSize=9, textColor=HexColor("#7F8C8D"),
                                           alignment=TA_CENTER, spaceAfter=3 * mm)
                        ))
                except Exception:
                    elements.append(Paragraph(
                        f"(no se pudo incluir: {os.path.basename(att.path)})",
                        ParagraphStyle("ImgErr", parent=styles["Normal"],
                                       fontSize=9, textColor=HexColor("#E74C3C"))
                    ))

    # ===== FOOTER SPACE =====
    elements.append(Spacer(1, 1.5 * cm))
    elements.append(Table([[""]], colWidths=[16 * cm],
                          style=[("LINEABOVE", (0, 0), (-1, -1), 0.5, HexColor("#BDC3C7"))]))
    elements.append(Spacer(1, 2 * mm))
    footer_text = INSTITUTION.get("footer_text", "")
    if footer_text:
        elements.append(Paragraph(
            footer_text,
            ParagraphStyle("Footer", parent=styles["Normal"],
                           fontSize=7, textColor=HexColor("#95A5A6"), alignment=TA_CENTER)
        ))

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
