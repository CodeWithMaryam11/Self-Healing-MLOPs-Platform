#!/usr/bin/env python3
"""
PipelineIQ - User Manual & Technical Specification PDF Generator
Uses ReportLab to compile a styled PDF document.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

# Colors
PRIMARY = colors.HexColor("#0F172A")    # Slate 900
SECONDARY = colors.HexColor("#0284C7")  # Sky 600
ACCENT = colors.HexColor("#0D9488")     # Teal 600
DARK_TEXT = colors.HexColor("#1E293B")  # Slate 800
LIGHT_BG = colors.HexColor("#F8FAFC")   # Slate 50
BORDER_COLOR = colors.HexColor("#E2E8F0") # Slate 200
ALERT_BG = colors.HexColor("#FEF2F2")   # Red 50
ALERT_BORDER = colors.HexColor("#FCA5A5") # Red 300
SUCCESS_BG = colors.HexColor("#F0FDF4") # Green 50
SUCCESS_BORDER = colors.HexColor("#86EFAC") # Green 300
CODE_BG = colors.HexColor("#1E293B")    # Slate 800 dark code container
CODE_TEXT = colors.HexColor("#38BDF8")  # Sky 400

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute total page count and add running headers/footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        if self._pageNumber == 1:
            # Suppress header and footer on cover page
            return

        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(SECONDARY)
        
        # Running Header
        self.drawString(54, 750, "PIPELINEIQ // SELF-HEALING MLOPS PLATFORM")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawRightString(612 - 54, 750, "USER MANUAL & SYSTEM SPECIFICATION")
        
        # Header rule line
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(54, 742, 612 - 54, 742)

        # Running Footer
        self.line(54, 45, 612 - 54, 45)
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(54, 32, "Department of CSE — Islamic University of Science and Technology (IUST)")
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 32, page_str)
        self.restoreState()

def build_pdf(filename="PipelineIQ_User_Manual.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        name="CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=28,
        leading=34,
        textColor=PRIMARY,
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name="CoverSubtitle",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=SECONDARY,
        spaceAfter=24
    ))
    styles.add(ParagraphStyle(
        name="CoverMeta",
        fontName="Helvetica",
        fontSize=10,
        leading=16,
        textColor=DARK_TEXT,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name="ChapterHeader",
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=PRIMARY,
        spaceBefore=18,
        spaceAfter=10,
        keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=SECONDARY,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        name="SubSectionHeader",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=DARK_TEXT,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    ))
    styles.add(ParagraphStyle(
        name="Body",
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=DARK_TEXT,
        spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name="BulletText",
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=DARK_TEXT,
        leftIndent=15,
        spaceAfter=4
    ))
    styles.add(ParagraphStyle(
        name="CodeBlock",
        fontName="Courier",
        fontSize=8.5,
        leading=11,
        textColor=CODE_TEXT,
        spaceAfter=8
    ))
    styles.add(ParagraphStyle(
        name="CalloutText",
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=DARK_TEXT
    ))

    story = []

    # =========================================================================
    # COVER PAGE
    # =========================================================================
    story.append(Spacer(1, 40))
    story.append(Paragraph("PIPELINEIQ // SELF-HEALING MLOPS PLATFORM", styles["CoverTitle"]))
    story.append(Paragraph("Comprehensive User Manual & System Architecture Guide", styles["CoverSubtitle"]))
    
    story.append(HRFlowable(width="100%", thickness=3, color=SECONDARY, spaceBefore=10, spaceAfter=20))

    story.append(Spacer(1, 20))
    story.append(Paragraph("<b>B.Tech Thesis Project Codebase & Operational Manual</b>", styles["CoverMeta"]))
    story.append(Spacer(1, 10))

    meta_table_data = [
        [Paragraph("<b>Submitted by:</b>", styles["CoverMeta"]), Paragraph("Group No. 10", styles["CoverMeta"])],
        [Paragraph("", styles["CoverMeta"]), Paragraph("• Maimoona Manzoor (CSE-22-LE-70)<br/>• Syed Maryam Andrabi (CSE-22-LE-74)<br/>• Momin Zahoor (CSE-22-LE-71)", styles["CoverMeta"])],
        [Paragraph("<b>Supervised by:</b>", styles["CoverMeta"]), Paragraph("<b>Dr. Sahil Sholla</b> (Assistant Professor, Dept. of CSE)", styles["CoverMeta"])],
        [Paragraph("<b>Institution:</b>", styles["CoverMeta"]), Paragraph("Islamic University of Science and Technology (IUST), Awantipora", styles["CoverMeta"])],
        [Paragraph("<b>Academic Session:</b>", styles["CoverMeta"]), Paragraph("Spring 2026", styles["CoverMeta"])],
    ]
    t_meta = Table(meta_table_data, colWidths=[110, 394])
    t_meta.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_meta)

    story.append(Spacer(1, 60))

    # Executive Box
    exec_summary_text = (
        "<b>Executive Abstract:</b> PipelineIQ is an enterprise-grade cloud-native MLOps platform engineered to "
        "fully automate data ingestion, minority balancing via SMOTE, multi-model concurrent execution (Random Forest, "
        "XGBoost, LightGBM), MLflow experiment tracking, statistical covariate drift detection (Evidently AI, KS-Test, PSI), "
        "and zero-downtime self-healing model retraining."
    )
    exec_table = Table([[Paragraph(exec_summary_text, styles["CalloutText"])]], colWidths=[504])
    exec_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 1, SECONDARY),
        ('PADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(exec_table)

    story.append(PageBreak())

    # =========================================================================
    # TABLE OF CONTENTS / CHAPTER 1: INTRODUCTION
    # =========================================================================
    story.append(Paragraph("1. Executive Summary & Rationale", styles["ChapterHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph(
        "According to empirical findings by Sculley et al. (<i>NeurIPS 2015</i>), up to 90% of technical debt in deployed "
        "machine learning systems stems from operational infrastructure—data validation, feature scaling, model drift monitoring, "
        "and manual retraining workflows—rather than the underlying model mathematics. PipelineIQ directly addresses this challenge "
        "by automating the 70% manual engineering overhead required to maintain production machine learning models.",
        styles["Body"]
    ))

    story.append(Paragraph("Key Objectives Fulfilled:", styles["SectionHeader"]))
    story.append(Paragraph("• <b>Automated Preprocessing & SMOTE Balancing:</b> Implements missing value median/mode imputation, quantile normalization, and Synthetic Minority Over-sampling Technique (SMOTE).", styles["BulletText"]))
    story.append(Paragraph("• <b>Concurrent Multi-Model Execution:</b> Simultaneously trains Random Forest, XGBoost, and LightGBM models with hyperparameter depth tuning.", styles["BulletText"]))
    story.append(Paragraph("• <b>Statistical Drift Telemetry:</b> Continuously evaluates Population Stability Index (PSI) and 2-sample Kolmogorov-Smirnov statistics.", styles["BulletText"]))
    story.append(Paragraph("• <b>Autonomous Self-Healing:</b> Dynamically dispatches background retraining threads upon drift threshold breach (PSI > 0.25) to hot-swap active champion models.", styles["BulletText"]))

    story.append(Spacer(1, 10))

    # =========================================================================
    # CHAPTER 2: FOUR-LAYER ARCHITECTURE
    # =========================================================================
    story.append(Paragraph("2. Four-Layer System Methodology", styles["ChapterHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=12))

    arch_data = [
        [Paragraph("<b>Layer</b>", styles["SubSectionHeader"]), Paragraph("<b>Core Components</b>", styles["SubSectionHeader"]), Paragraph("<b>Key Responsibilities</b>", styles["SubSectionHeader"])],
        [
            Paragraph("<b>Layer 1: Ingestion & SMOTE</b>", styles["Body"]),
            Paragraph("FastAPI, Pandas, Imbalanced-Learn", styles["Body"]),
            Paragraph("Multipart CSV ingestion, target detection, missing value median imputation, SMOTE balancing.", styles["Body"])
        ],
        [
            Paragraph("<b>Layer 2: AutoML Execution</b>", styles["Body"]),
            Paragraph("Scikit-Learn, XGBoost, LightGBM, MLflow", styles["Body"]),
            Paragraph("Concurrent multi-model training, decision threshold calibration, MLflow experiment tracking.", styles["Body"])
        ],
        [
            Paragraph("<b>Layer 3: Serving & Drift</b>", styles["Body"]),
            Paragraph("FastAPI, JWT, SciPy, Evidently AI", styles["Body"]),
            Paragraph("JWT Bearer security, 24h tokens, 2-sample KS-Test & PSI drift calculations, self-healing trigger.", styles["Body"])
        ],
        [
            Paragraph("<b>Layer 4: Orchestration</b>", styles["Body"]),
            Paragraph("Docker, Docker Compose, React Vite", styles["Body"]),
            Paragraph("Containerized multi-service deployment (React UI port 3000, FastAPI port 8000, MLflow port 5001).", styles["Body"])
        ]
    ]
    t_arch = Table(arch_data, colWidths=[130, 130, 244])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t_arch)

    story.append(Spacer(1, 14))

    # =========================================================================
    # CHAPTER 3: INSTALLATION & QUICK START
    # =========================================================================
    story.append(Paragraph("3. Installation & Quick-Start Execution Guide", styles["ChapterHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph("Option A: Instant Demo Simulation Mode (Zero Backend Setup Needed)", styles["SectionHeader"]))
    story.append(Paragraph("Ideal for quick evaluation or committee presentation on laptops without Python/MongoDB setup:", styles["Body"]))
    
    code_demo = (
        "# 1. Install Node modules\n"
        "cd June/June\n"
        "npm install\n\n"
        "# 2. Launch Vite development server\n"
        "npm run dev\n\n"
        "# 3. Open browser at http://localhost:3000"
    )
    t_demo = Table([[Paragraph(code_demo.replace("\n", "<br/>").replace(" ", "&nbsp;"), styles["CodeBlock"])]], colWidths=[504])
    t_demo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
        ('BOX', (0, 0), (-1, -1), 1, PRIMARY),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_demo)

    story.append(Paragraph("Option B: Production Docker Compose Execution", styles["SectionHeader"]))
    story.append(Paragraph("Launches full stack (FastAPI Backend, React Web UI, MongoDB, MLflow Registry):", styles["Body"]))
    
    code_docker = (
        "cd June/June\n"
        "docker-compose up --build -d\n\n"
        "# Access points:\n"
        "# React UI: http://localhost:3000 | FastAPI Docs: http://localhost:8000/docs | MLflow: http://localhost:5001"
    )
    t_docker = Table([[Paragraph(code_docker.replace("\n", "<br/>").replace(" ", "&nbsp;"), styles["CodeBlock"])]], colWidths=[504])
    t_docker.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), CODE_BG),
        ('BOX', (0, 0), (-1, -1), 1, PRIMARY),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_docker)

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 4: STEP-BY-STEP OPERATOR MANUAL
    # =========================================================================
    story.append(Paragraph("4. Step-by-Step Operator User Manual", styles["ChapterHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=12))

    steps = [
        ("Step 1: User Authentication & JWT Handshake", [
            "Navigate to http://localhost:3000.",
            "Enter pre-filled operator credentials (admin@pipelineiq.io / admin123) or click Register.",
            "Upon submission, FastAPI validates password hash via bcrypt and returns an encrypted JWT Bearer access token stored in Zustand client memory."
        ]),
        ("Step 2: Tabular Dataset Upload & Pipeline Dispatch", [
            "On the Dashboard Overview, click '+ New Pipeline Setup'.",
            "Drag and drop any tabular dataset CSV (e.g., ibm_hr_attrition.csv) into the dropzone container.",
            "Select custom models to execute concurrently: [x] Random Forest Engine, [x] XGBoost Engine, [x] LightGBM Engine.",
            "Choose target evaluation metric (F1-Score, Accuracy, or ROC-AUC).",
            "Click 'Launch Training Pipeline' to trigger SMOTE preprocessing and background worker execution."
        ]),
        ("Step 3: Real-Time Telemetry & Champion Model Promotion", [
            "The dashboard updates live every 5000ms using TanStack Query polling.",
            "A temporary yellow 'Training...' placeholder badge provides immediate zero-latency feedback.",
            "Upon completion, metrics are evaluated, and the top-performing algorithm is automatically awarded a green 'CHAMPION MODEL' badge."
        ]),
        ("Step 4: Statistical Data Drift Monitoring", [
            "Inspect the Evidently AI Drift Monitor panel at the bottom of the dashboard.",
            "Under baseline operation, the telemetry monitor displays a green STABLE status with PSI < 0.10 and KS-Test p-value > 0.05."
        ]),
        ("Step 5: Injecting Synthetic Covariate Shift & Alert State", [
            "Click 'Inject Covariate Shift' to simulate real-world data corruption/behavioral shift.",
            "The statistical engine calculates PSI > 0.25 (e.g. PSI = 0.38), triggering a high-visibility yellow alert border.",
            "The banner turns blue/yellow: 'CRITICAL DATA DRIFT DETECTED — AUTONOMOUS RETRAINING IN PROGRESS'."
        ]),
        ("Step 6: Autonomous Self-Healing Recovery", [
            "Algorithm 4 dispatches background worker thread to tune hyperparameter depth and retrain candidate models on shifted data.",
            "Once retrained, the system hot-swaps the champion model registry.",
            "Click 'Reset Drift Baseline' to return system telemetry to STABLE HEALTHY status."
        ])
    ]

    for title, substeps in steps:
        story.append(Paragraph(title, styles["SectionHeader"]))
        for s in substeps:
            story.append(Paragraph(f"• {s}", styles["BulletText"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 10))

    # Callout Box
    alert_box_text = (
        "<b>Operational Note:</b> The 5-second deterministic polling strategy uses refetchIntervalInBackground: true "
        "to ensure telemetry updates continue seamlessly even while an operator switches tabs during model training."
    )
    t_alert = Table([[Paragraph(alert_box_text, styles["CalloutText"])]], colWidths=[504])
    t_alert.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), SUCCESS_BG),
        ('BOX', (0, 0), (-1, -1), 1, SUCCESS_BORDER),
        ('PADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t_alert)

    story.append(PageBreak())

    # =========================================================================
    # CHAPTER 5: MATHEMATICAL FOUNDATIONS & ALGORITHMS
    # =========================================================================
    story.append(Paragraph("5. Mathematical Foundations & System Algorithms", styles["ChapterHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph("5.1 Synthetic Minority Over-sampling Technique (SMOTE)", styles["SectionHeader"]))
    story.append(Paragraph(
        "To eliminate class imbalance in datasets like employee attrition (84% Stayed vs 16% Left), SMOTE synthesizes minority class "
        "samples along feature-space line segments connecting k-nearest neighbors:",
        styles["Body"]
    ))
    story.append(Paragraph("<i>x_new = x_i + λ (x_zi - x_i),  where λ ~ Uniform(0, 1)</i>", styles["SubSectionHeader"]))

    story.append(Paragraph("5.2 Population Stability Index (PSI)", styles["SectionHeader"]))
    story.append(Paragraph(
        "Population Stability Index quantifies shift between baseline reference data and live production distributions across 10 quantile bins:",
        styles["Body"]
    ))
    story.append(Paragraph("<i>PSI = Σ [ (P_current,b - P_baseline,b) * ln(P_current,b / P_baseline,b) ]</i>", styles["SubSectionHeader"]))
    
    psi_table_data = [
        [Paragraph("<b>PSI Range</b>", styles["SubSectionHeader"]), Paragraph("<b>Statistical Classification</b>", styles["SubSectionHeader"]), Paragraph("<b>System Action</b>", styles["SubSectionHeader"])],
        [Paragraph("PSI < 0.10", styles["Body"]), Paragraph("No Significant Drift", styles["Body"]), Paragraph("Maintain standard model serving state.", styles["Body"])],
        [Paragraph("0.10 <= PSI <= 0.25", styles["Body"]), Paragraph("Moderate Covariate Shift", styles["Body"]), Paragraph("Flag telemetry warning in audit log.", styles["Body"])],
        [Paragraph("PSI > 0.25", styles["Body"]), Paragraph("Critical Covariate Shift", styles["Body"]), Paragraph("Trigger Algorithm 4 Autonomous Retraining.", styles["Body"])],
    ]
    t_psi = Table(psi_table_data, colWidths=[110, 160, 234])
    t_psi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_psi)

    story.append(Paragraph("5.3 2-Sample Kolmogorov-Smirnov Test", styles["SectionHeader"]))
    story.append(Paragraph(
        "Compares empirical cumulative distribution functions (eCDF) F_1(x) and F_2(x). Drift is signaled when p-value < 0.05:",
        styles["Body"]
    ))
    story.append(Paragraph("<i>D = sup_x | F_reference(x) - F_current(x) |</i>", styles["SubSectionHeader"]))

    story.append(Spacer(1, 10))

    # =========================================================================
    # CHAPTER 6: REST API SPECIFICATION
    # =========================================================================
    story.append(Paragraph("6. REST API Endpoint Reference", styles["ChapterHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=12))

    api_data = [
        [Paragraph("<b>Method</b>", styles["SubSectionHeader"]), Paragraph("<b>Endpoint Path</b>", styles["SubSectionHeader"]), Paragraph("<b>Auth</b>", styles["SubSectionHeader"]), Paragraph("<b>Description</b>", styles["SubSectionHeader"])],
        [Paragraph("POST", styles["Body"]), Paragraph("/api/v1/auth/register", styles["Body"]), Paragraph("None", styles["Body"]), Paragraph("Register new user & MLflow profile.", styles["Body"])],
        [Paragraph("POST", styles["Body"]), Paragraph("/api/v1/auth/login", styles["Body"]), Paragraph("None", styles["Body"]), Paragraph("Authenticate & issue JWT Bearer token.", styles["Body"])],
        [Paragraph("GET", styles["Body"]), Paragraph("/api/v1/health", styles["Body"]), Paragraph("None", styles["Body"]), Paragraph("Check FastAPI, MongoDB, MLflow status.", styles["Body"])],
        [Paragraph("POST", styles["Body"]), Paragraph("/api/v1/models/train", styles["Body"]), Paragraph("Bearer", styles["Body"]), Paragraph("Dispatch multi-model AutoML pipeline.", styles["Body"])],
        [Paragraph("GET", styles["Body"]), Paragraph("/api/v1/runs", styles["Body"]), Paragraph("Bearer", styles["Body"]), Paragraph("Fetch live MLflow run telemetry history.", styles["Body"])],
        [Paragraph("GET", styles["Body"]), Paragraph("/api/v1/drift", styles["Body"]), Paragraph("Bearer", styles["Body"]), Paragraph("Get Evidently AI KS & PSI drift telemetry.", styles["Body"])],
        [Paragraph("POST", styles["Body"]), Paragraph("/api/v1/drift/inject", styles["Body"]), Paragraph("Bearer", styles["Body"]), Paragraph("Inject artificial covariate shift.", styles["Body"])],
        [Paragraph("POST", styles["Body"]), Paragraph("/api/v1/drift/reset", styles["Body"]), Paragraph("Bearer", styles["Body"]), Paragraph("Reset drift baseline metrics to stable.", styles["Body"])],
    ]
    t_api = Table(api_data, colWidths=[55, 145, 50, 254])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT_BG),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_api)

    story.append(Spacer(1, 14))

    # =========================================================================
    # CHAPTER 7: TROUBLESHOOTING & ACKNOWLEDGEMENTS
    # =========================================================================
    story.append(Paragraph("7. Troubleshooting & Thesis Acknowledgements", styles["ChapterHeader"]))
    story.append(HRFlowable(width="100%", thickness=1, color=SECONDARY, spaceBefore=2, spaceAfter=12))

    story.append(Paragraph("Common Issues & Solutions:", styles["SectionHeader"]))
    story.append(Paragraph("• <b>Passlib / Bcrypt Module Error:</b> Run <code>pip install passlib bcrypt==4.0.1</code> in virtual environment.", styles["BulletText"]))
    story.append(Paragraph("• <b>MongoDB Connection Timeout:</b> Ensure <code>mongod</code> is running locally on port 27017 or set <code>MONGO_URL</code> environment variable.", styles["BulletText"]))
    story.append(Paragraph("• <b>XGBoost OpenMP Error on macOS:</b> Install OpenMP library via Homebrew: <code>brew install libomp</code>.", styles["BulletText"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph("Academic Thesis Acknowledgements:", styles["SectionHeader"]))
    story.append(Paragraph(
        "We express our sincere gratitude to our supervisor, <b>Dr. Sahil Sholla</b>, Assistant Professor in the Department "
        "of Computer Science and Engineering at the Islamic University of Science and Technology (IUST), Awantipora, Kashmir, "
        "for his invaluable guidance, technical insight, and steadfast support throughout the design and execution of this thesis project.",
        styles["Body"]
    ))

    # Build PDF
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {filename}")

if __name__ == "__main__":
    output_path = "PipelineIQ_User_Manual.pdf"
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    build_pdf(output_path)
