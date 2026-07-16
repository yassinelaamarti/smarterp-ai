import logging
import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from fpdf import FPDF
from fastapi import FastAPI
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.services.ai_agent import generate_dashboard_summary
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class StrategicReportPDF(FPDF):
    def header(self):
        # Pour les pages après la première, on peut afficher un petit en-tête simple
        if self.page_no() > 1:
            self.set_font("Helvetica", style="I", size=8)
            self.set_text_color(148, 163, 184)
            self.cell(0, 5, "SmartERP AI - Rapport Stratégique Confidentiel", align="L")
            self.ln(8)
            
    def footer(self):
        self.set_y(-15)
        self.set_line_width(0.2)
        self.set_draw_color(148, 163, 184)
        self.line(15, self.h - 18, self.w - 15, self.h - 18)
        self.set_font("Helvetica", size=8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 10, "SmartERP AI - Rapport Stratégique Confidentiel", align="L")
        # alias_nb_pages s'assure d'insérer le nombre de pages total via {nb}
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="R")



def _write_formatted_line(pdf: FPDF, text: str, indent: float = 15):
    pdf.set_x(indent)
    parts = text.split("**")
    for idx, part in enumerate(parts):
        is_bold = (idx % 2 != 0)
        if is_bold:
            pdf.set_font("Helvetica", style="B", size=10)
            pdf.set_text_color(30, 41, 59)
        else:
            pdf.set_font("Helvetica", style="", size=10)
            pdf.set_text_color(51, 65, 85)
        pdf.write(5.5, part)
    pdf.ln(5.5)


def generate_pdf_report(summary: str) -> bytes:
    pdf = StrategicReportPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # En-tête Banner (style identique à jsPDF)
    pdf.set_fill_color(37, 99, 235)  # blue-600
    pdf.rect(0, 0, 210, 35, "F")
    
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", style="B", size=20)
    pdf.text(15, 14, "SmartERP AI")
    pdf.set_font("Helvetica", style="", size=10)
    pdf.text(15, 22, "Rapport de Synthese Decisionnelle & Recommandations")
    pdf.text(15, 27, "Instance : Odoo 17 Cache | Rapport IA Confidentiel")
    
    # Métadonnées
    pdf.set_y(45)
    pdf.set_text_color(30, 41, 59)  # slate-800
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.cell(0, 10, "RAPPORT STRATEGIQUE GLOBAL", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_draw_color(226, 232, 240)
    pdf.set_line_width(0.5)
    pdf.line(15, 53, 195, 53)
    
    pdf.set_y(55)
    pdf.set_font("Helvetica", style="", size=9)
    pdf.set_text_color(100, 116, 139)
    date_str = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
    pdf.cell(0, 5, f"Genere le : {date_str}", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "Destinataire : Direction Generale / Direction Commerciale", new_x="LMARGIN", new_y="NEXT")
    
    pdf.line(15, 68, 195, 68)
    pdf.set_y(75)
    
    # Contenu du rapport
    lines = summary.split("\n")
    pdf.set_font("Helvetica", style="", size=10)
    pdf.set_text_color(51, 65, 85)  # slate-700
    
    for line in lines:
        trimmed = line.strip()
        if not trimmed:
            pdf.ln(4)
            continue
            
        if trimmed.startswith("##") or trimmed.startswith("#"):
            pdf.ln(4)
            pdf.set_font("Helvetica", style="B", size=11)
            pdf.set_text_color(37, 99, 235)  # Accent color blue-600
            pdf.cell(0, 8, trimmed.lstrip("# ").strip(), new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", style="", size=10)
            pdf.set_text_color(51, 65, 85)
        elif trimmed.startswith("- ") or trimmed.startswith("* "):
            content = trimmed[2:]
            _write_formatted_line(pdf, "- " + content, indent=20)
        elif trimmed[0].isdigit() and ". " in trimmed[:4]:
            _write_formatted_line(pdf, trimmed, indent=15)
        else:
            _write_formatted_line(pdf, trimmed, indent=15)
            
    return bytes(pdf.output())


def check_and_send_scheduled_reports(db: Session = None):
    """
    Vérifie si des rapports programmés doivent être envoyés aux utilisateurs abonnés.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True
        
    try:
        users = db.query(User).filter(User.report_schedule != "none").all()
        today = datetime.date.today()
        
        for user in users:
            is_due = False
            last_sent_str = user.last_report_sent
            
            if not last_sent_str:
                is_due = True
            else:
                try:
                    last_sent = datetime.datetime.strptime(last_sent_str, "%Y-%m-%d").date()
                    days_diff = (today - last_sent).days
                    
                    if user.report_schedule == "daily":
                        if days_diff >= 1:
                            is_due = True
                    elif user.report_schedule == "weekly":
                        if days_diff >= 6:
                            is_due = True
                    elif user.report_schedule == "monthly":
                        if days_diff >= 27:
                            is_due = True
                except ValueError:
                    is_due = True
                        
            if is_due:
                logger.info(f"Rapport programme ({user.report_schedule}) du pour l'utilisateur {user.email}")
                success = send_single_report(db, user)
                if success:
                    user.last_report_sent = today.strftime("%Y-%m-%d")
                    db.commit()
    except Exception as e:
        logger.error(f"Erreur lors de la verification/envoi des rapports programmes: {e}")
    finally:
        if close_db:
            db.close()


def send_single_report(db: Session, user: User) -> bool:
    """
    Génère un rapport de synthèse décisionnelle de tableau de bord et l'envoie à l'utilisateur.
    """
    try:
        # 1. Générer le rapport via l'IA
        summary = generate_dashboard_summary()
        
        # 2. Générer le PDF
        pdf_data = generate_pdf_report(summary)
        
        # 3. Préparer les variables d'envoi
        dest_email = user.report_email or user.email
        subject = "SmartERP AI — Votre Rapport Strategique Global"
        body = (
            f"Bonjour {user.full_name or 'l`utilisateur'},\n\n"
            f"Veuillez trouver ci-joint votre rapport de synthese strategique periodique genere automatiquement par l'IA "
            f"de SmartERP AI.\n\n"
            f"Ce rapport contient :\n"
            f"- Une synthese de performance globale de l'entreprise.\n"
            f"- L'analyse detaillee par axe commercial, financier et operationnel.\n"
            f"- Les risques et points de vigilance.\n"
            f"- Vos recommandations strategiques actionnables.\n\n"
            f"Cordialement,\n"
            f"L'equipe SmartERP AI"
        )
        
        pdf_filename = f"SmartERP_AI_Synthese_{datetime.date.today().strftime('%Y-%m-%d')}.pdf"
        
        # Envoi d'email avec simulation locale si aucun compte SMTP configuré
        if not settings.smtp_username or not settings.smtp_password:
            logger.warning(f"[SIMULATION EMAIL] Vers: {dest_email} | Sujet: {subject}")
            logger.warning(f"[SIMULATION EMAIL] Corps: {body}")
            
            # Enregistrer le PDF localement dans test_reports/
            test_reports_dir = "/app/test_reports" if os.path.exists("/app") else "test_reports"
            os.makedirs(test_reports_dir, exist_ok=True)
            filepath = os.path.join(test_reports_dir, pdf_filename)
            with open(filepath, "wb") as f:
                f.write(pdf_data)
            logger.warning(f"[SIMULATION EMAIL] PDF ecrit avec succes dans : {filepath}")
            return True
            
        # Envoi d'un email réel via SMTP
        msg = MIMEMultipart()
        msg['From'] = settings.smtp_from
        msg['To'] = dest_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_data)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename= {pdf_filename}")
        msg.attach(part)
        
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
            
        logger.info(f"Rapport strategique envoye par email a {dest_email} avec succes.")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la generation/envoi du rapport pour {user.email}: {e}")
        return False


def setup_scheduler(app: FastAPI):
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler(timezone="UTC")
    
    # Ajouter la tâche périodique (vérifier toutes les heures)
    scheduler.add_job(
        check_and_send_scheduled_reports,
        trigger="interval",
        hours=1,
        id="check_reports_job"
    )
    
    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("Planificateur de rapports demarre avec succes (verification toutes les heures).")
