"""Offline, recorded-data-only PDF rendering. No network or database writes."""
from pathlib import Path

from fpdf import FPDF

FONT = Path(__file__).resolve().parent / "pdf_fonts" / "DejaVuSans.ttf"
NOTICE = (
    "Confidential patient information. User-entered data; not independently "
    "verified laboratory results. No diagnosis, interpretation, recommendation, "
    "unit conversion or inferred reference range is provided."
)


class UnsupportedPDFText(ValueError):
    pass


class ReportPDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Recorded", size=8)
            self.cell(0, 5, self.record_identifiers, new_x="LMARGIN", new_y="NEXT")
            self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Recorded", size=8)
        self.cell(0, 5, f"Confidential | Recorded data only | Page {self.page_no()}", align="C")


def render_report_pdf(report, results, history, history_total, generated_at):
    """Render a materialized snapshot; unsupported glyphs fail, never disappear."""
    pdf = ReportPDF()
    pdf.add_font("Recorded", fname=str(FONT))
    pdf.set_font("Recorded", size=10)
    pdf.set_text_shaping(True)
    pdf.set_auto_page_break(True, margin=22)
    pdf.set_margins(16, 16, 16)
    pdf.set_title("LabAssist recorded-data report")
    pdf.set_creator("LabAssist")
    pdf.record_identifiers = f"LabAssist | Patient ID {report.patient_id} | Report ID {report.pk}"
    pdf.add_page()

    def text(value, size=10):
        value = str(value)
        # Preserve line breaks; tabs are visual spacing only.
        value = value.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "    ")
        cmap = pdf.fonts["recorded"].cmap
        if any(ord(char) not in cmap for char in value if char != "\n"):
            raise UnsupportedPDFText("Recorded text contains an unsupported character.")
        pdf.set_font("Recorded", size=size)
        pdf.multi_cell(0, 6, value, new_x="LMARGIN", new_y="NEXT", wrapmode="WORD")

    def field(label, value):
        text(f"{label}: {value if value is not None and value != '' else 'Not recorded'}")

    def result_block(result):
        pdf.ln(3)
        text(f"{result.lab_test.name} ({result.lab_test.code})", 12)
        field("Result ID / revision", f"{result.pk} / {result.revision}")
        field("Source report ID", result.report_id)
        field("Test date", result.test_date.isoformat())
        field("Recorded value", result.value)
        field("Recorded unit", result.unit)
        field("Recorded reference range", result.reference_range)
        field("Recorded notes", result.notes)

    text("LabAssist — Recorded data report", 16)
    text(NOTICE)
    field("Export generated at (UTC)", generated_at.isoformat())
    text("This export reflects current stored revisions, not a signed original laboratory report.")
    pdf.ln(4)
    patient = report.patient
    text("Patient", 13)
    field("Patient ID / revision", f"{patient.pk} / {patient.revision}")
    field("Name", patient.full_name)
    field("Date of birth", patient.date_of_birth.isoformat() if patient.date_of_birth else None)
    field("Sex assigned at birth", patient.get_sex_assigned_at_birth_display())
    pdf.ln(4)
    text("Report", 13)
    field("Report ID / revision", f"{report.pk} / {report.revision}")
    field("Laboratory", report.laboratory_name)
    field("Report number", report.report_number)
    field("Report issue date", report.report_date.isoformat() if report.report_date else None)
    field("Recorded at (UTC)", report.created_at.isoformat())
    field("Last updated at (UTC)", report.updated_at.isoformat())
    field("Recorded report notes", report.notes)
    pdf.ln(4)
    text(f"Recorded results ({len(results)})", 13)
    if not results:
        text("No linked results.")
    for result in results:
        result_block(result)
    pdf.ln(4)
    text("Related earlier recorded results", 13)
    text(
        "Same patient and exact catalog test ID only, with a test date strictly "
        "before the earliest date of that test in this report. Current report "
        "excluded. Same-day results excluded. No unit equivalence or trend is inferred."
    )
    text(f"Showing {len(history)} of {history_total} matching results, newest first (maximum 100).")
    if not history:
        text("No matching earlier results.")
    for result in history:
        result_block(result)
    return bytes(pdf.output())
