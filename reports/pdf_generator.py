import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, PageBreak
)
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from database.db import get_patient
from config.institution import INSTITUTION


def generate_patient_report(patient_id: int, output_path: str):
    patient = get_patient(patient_id)
    if patient is None:
        raise ValueError(f"Paciente ID {patient_id} no encontrado")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        "InstitutionName", parent=styles["Heading1"],
        fontSize=18, textColor=HexColor("#2C3E50"), spaceAfter=4 * mm,
        alignment=TA_CENTER
    ))
    styles.add(ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=9, textColor=HexColor("#7F8C8D"),
        alignment=TA_CENTER, spaceAfter=2 * mm
    ))
    styles.add(ParagraphStyle(
        "SectionTitle", parent=styles["Heading2"],
        fontSize=13, textColor=HexColor("#2C3E50"),
        spaceBefore=6 * mm, spaceAfter=3 * mm,
        borderPadding=(0, 0, 2, 0),
    ))
    styles.add(ParagraphStyle(
        "FieldLabel", parent=styles["Normal"],
        fontSize=10, textColor=HexColor("#34495E"),
        spaceBefore=2 * mm
    ))
    styles.add(ParagraphStyle(
        "FieldValue", parent=styles["Normal"],
        fontSize=10, spaceBefore=1 * mm, spaceAfter=3 * mm,
        leftIndent=4 * mm
    ))
    styles.add(ParagraphStyle(
        "DescriptionText", parent=styles["Normal"],
        fontSize=10, leading=15,
        spaceBefore=2 * mm, spaceAfter=4 * mm,
        alignment=TA_LEFT
    ))

    elements = []

    # --- HEADER ---
    logo_path = INSTITUTION.get("logo_path", "")
    if not os.path.isfile(logo_path):
        logo_path = INSTITUTION.get("default_logo", "")

    if os.path.isfile(logo_path):
        try:
            img = RLImage(logo_path, width=4 * cm, height=2 * cm)
            elements.append(img)
        except Exception:
            pass

    elements.append(Paragraph(INSTITUTION["name"], styles["InstitutionName"]))
    elements.append(Paragraph(
        f"{INSTITUTION['address']} | Tel: {INSTITUTION['phone']} | {INSTITUTION['email']}",
        styles["Subtitle"]
    ))
    elements.append(Spacer(1, 3 * mm))

    # Separator line
    elements.append(Table([[""]], colWidths=[16 * cm],
                          style=[("LINEBELOW", (0, 0), (-1, -1), 1, HexColor("#2C3E50"))]))
    elements.append(Spacer(1, 4 * mm))

    # --- PATIENT DATA ---
    elements.append(Paragraph("Datos del Paciente", styles["SectionTitle"]))

    data = [
        ["Apellido y Nombre", patient.full_name],
        ["DNI", patient.dni or "—"],
        ["Fecha de nacimiento", patient.birth_date or "—"],
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
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, HexColor("#ECF0F1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 5 * mm))

    # --- DESCRIPTION ---
    if patient.description:
        elements.append(Paragraph("Informe Médico", styles["SectionTitle"]))
        elements.append(Paragraph(patient.description.replace("\n", "<br/>"), styles["DescriptionText"]))

    # --- IMAGES ---
    if patient.image_paths:
        elements.append(Spacer(1, 3 * mm))
        elements.append(Paragraph("Imágenes Adjuntas", styles["SectionTitle"]))
        for img_path in patient.image_paths:
            if os.path.isfile(img_path):
                try:
                    img = RLImage(img_path, width=14 * cm, height=10 * cm, kind="proportional")
                    elements.append(img)
                    elements.append(Spacer(1, 3 * mm))
                except Exception:
                    elements.append(Paragraph(
                        f"(no se pudo incluir: {os.path.basename(img_path)})",
                        styles["Subtitle"]
                    ))

    # --- FOOTER ---
    elements.append(Spacer(1, 1 * cm))
    elements.append(Table([[""]], colWidths=[16 * cm],
                          style=[("LINEABOVE", (0, 0), (-1, -1), 0.5, HexColor("#BDC3C7"))]))
    elements.append(Spacer(1, 2 * mm))
    footer_text = INSTITUTION.get("footer_text", "")
    if footer_text:
        elements.append(Paragraph(footer_text, ParagraphStyle(
            "Footer", parent=styles["Normal"],
            fontSize=8, textColor=HexColor("#95A5A6"),
            alignment=TA_CENTER
        )))

    doc.build(elements)
