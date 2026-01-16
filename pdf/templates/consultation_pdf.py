"""
PDF generation module for consultation notes.
Deterministic template-based generation - NO AI calls.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import datetime
from typing import Dict, Any, List


def create_custom_styles():
    """Create custom paragraph styles for medical notes"""
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=12,
        alignment=TA_CENTER
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c5aa0'),
        spaceBefore=12,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='SubSection',
        parent=styles['Heading3'],
        fontSize=11,
        textColor=colors.HexColor('#4a4a4a'),
        spaceBefore=8,
        spaceAfter=4,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='Body',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=6
    ))
    
    styles.add(ParagraphStyle(
        name='Bullet',
        parent=styles['Normal'],
        fontSize=10,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=4
    ))
    
    styles.add(ParagraphStyle(
        name='Alert',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.red,
        fontName='Helvetica-Bold',
        spaceAfter=6
    ))
    
    return styles


def generate_consultation_pdf(
    consultation_artifact: Dict[str, Any],
    output_path: str,
    facility_info: Dict[str, str] = None
) -> str:
    """
    Generate PDF consultation notes from artifact.
    
    Args:
        consultation_artifact: Complete consultation artifact from Bedrock
        output_path: Path to save PDF
        facility_info: Optional facility details (name, address, phone, logo_path)
        
    Returns:
        Path to generated PDF
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=2*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )
    
    styles = create_custom_styles()
    story = []
    
    # Extract sections
    metadata = consultation_artifact.get('metadata', {})
    patient = consultation_artifact.get('patient_context', {})
    soap = consultation_artifact.get('soap_notes', {})
    safety = consultation_artifact.get('clinical_safety', {})
    tasks = consultation_artifact.get('follow_up_tasks', [])
    handover = consultation_artifact.get('handover', {})
    
    # === HEADER ===
    if facility_info:
        story.append(Paragraph(f"<b>{facility_info.get('name', 'Medical Facility')}</b>", styles['Normal']))
        if facility_info.get('address'):
            story.append(Paragraph(facility_info['address'], styles['Normal']))
        if facility_info.get('phone'):
            story.append(Paragraph(f"Ph: {facility_info['phone']}", styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("CONSULTATION NOTES", styles['Title']))
    story.append(Spacer(1, 0.3*cm))
    
    # === METADATA ===
    meta_data = [
        ['Date:', metadata.get('timestamp', datetime.now().isoformat())[:10]],
        ['Setting:', metadata.get('setting_type', 'N/A').replace('_', ' ').title()],
        ['Encounter:', metadata.get('encounter_type', 'N/A').replace('_', ' ').title()],
        ['Specialty:', metadata.get('specialty', 'N/A').replace('_', ' ').title()]
    ]
    
    if patient.get('age_range'):
        meta_data.append(['Patient Age:', patient['age_range']])
    if patient.get('hospital_day'):
        meta_data.append(['Hospital Day:', str(patient['hospital_day'])])
    
    meta_table = Table(meta_data, colWidths=[4*cm, 10*cm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 0.5*cm))
    
    # === RED FLAGS (if any) ===
    red_flags = safety.get('red_flags', [])
    if red_flags:
        story.append(Paragraph("⚠️ RED FLAGS / ALERTS", styles['Alert']))
        for flag in red_flags:
            story.append(Paragraph(
                f"• [{flag.get('severity', 'N/A').upper()}] {flag.get('flag')} - {flag.get('action_taken', 'No action documented')}",
                styles['Alert']
            ))
        story.append(Spacer(1, 0.3*cm))
    
    # === SOAP NOTES ===
    
    # SUBJECTIVE
    story.append(Paragraph("SUBJECTIVE", styles['SectionHeader']))
    
    subjective = soap.get('subjective', {})
    if subjective.get('chief_complaint'):
        story.append(Paragraph("<b>Chief Complaint:</b>", styles['SubSection']))
        story.append(Paragraph(subjective['chief_complaint'], styles['Body']))
    
    if subjective.get('history_of_presenting_complaint'):
        story.append(Paragraph("<b>History of Presenting Complaint:</b>", styles['SubSection']))
        story.append(Paragraph(subjective['history_of_presenting_complaint'], styles['Body']))
    
    symptoms = subjective.get('symptoms', [])
    if symptoms:
        story.append(Paragraph("<b>Symptoms:</b>", styles['SubSection']))
        for symptom in symptoms:
            symptom_text = f"• <b>{symptom.get('symptom')}</b>"
            if symptom.get('onset'):
                symptom_text += f" - Onset: {symptom['onset']}"
            if symptom.get('severity'):
                symptom_text += f", Severity: {symptom['severity']}"
            if symptom.get('characteristics'):
                symptom_text += f" - {symptom['characteristics']}"
            story.append(Paragraph(symptom_text, styles['Bullet']))
    
    current_meds = subjective.get('current_medications', [])
    if current_meds:
        story.append(Paragraph("<b>Current Medications:</b>", styles['SubSection']))
        for med in current_meds:
            story.append(Paragraph(
                f"• {med.get('medication')} {med.get('dose', '')} {med.get('frequency', '')} - {med.get('indication', '')}",
                styles['Bullet']
            ))
    
    allergies = subjective.get('allergies', [])
    if allergies:
        story.append(Paragraph("<b>Allergies:</b>", styles['SubSection']))
        for allergy in allergies:
            story.append(Paragraph(
                f"• {allergy.get('allergen')} - {allergy.get('reaction')} ({allergy.get('severity')})",
                styles['Bullet']
            ))
    
    story.append(Spacer(1, 0.3*cm))
    
    # OBJECTIVE
    story.append(Paragraph("OBJECTIVE", styles['SectionHeader']))
    
    objective = soap.get('objective', {})
    vitals = objective.get('vital_signs', {})
    if any(vitals.values()):
        story.append(Paragraph("<b>Vital Signs:</b>", styles['SubSection']))
        vital_data = []
        for key, value in vitals.items():
            if value:
                vital_data.append([key.replace('_', ' ').title(), str(value)])
        
        if vital_data:
            vital_table = Table(vital_data, colWidths=[5*cm, 9*cm])
            vital_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f8f8f8')),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            story.append(vital_table)
            story.append(Spacer(1, 0.2*cm))
    
    exam_findings = objective.get('physical_examination', [])
    if exam_findings:
        story.append(Paragraph("<b>Physical Examination:</b>", styles['SubSection']))
        for exam in exam_findings:
            story.append(Paragraph(
                f"• <b>{exam.get('system', 'General').title()}:</b> {exam.get('findings', 'No findings documented')}",
                styles['Bullet']
            ))
            abnormalities = exam.get('abnormalities', [])
            if abnormalities:
                for abn in abnormalities:
                    story.append(Paragraph(f"  - {abn}", styles['Bullet']))
    
    investigations = objective.get('investigations', [])
    if investigations:
        story.append(Paragraph("<b>Investigations:</b>", styles['SubSection']))
        for inv in investigations:
            story.append(Paragraph(
                f"• {inv.get('test_name')}: {inv.get('result')} ({inv.get('interpretation', 'N/A')})",
                styles['Bullet']
            ))
    
    story.append(Spacer(1, 0.3*cm))
    
    # ASSESSMENT
    story.append(Paragraph("ASSESSMENT", styles['SectionHeader']))
    
    assessment = soap.get('assessment', {})
    if assessment.get('primary_diagnosis'):
        story.append(Paragraph(f"<b>Primary Diagnosis:</b> {assessment['primary_diagnosis']}", styles['Body']))
    
    if assessment.get('clinical_impression'):
        story.append(Paragraph("<b>Clinical Impression:</b>", styles['SubSection']))
        story.append(Paragraph(assessment['clinical_impression'], styles['Body']))
    
    problem_list = assessment.get('problem_list', [])
    if problem_list:
        story.append(Paragraph("<b>Problem List:</b>", styles['SubSection']))
        for problem in sorted(problem_list, key=lambda x: x.get('priority', 999)):
            story.append(Paragraph(
                f"• {problem.get('problem')} - {problem.get('status', 'N/A').title()}",
                styles['Bullet']
            ))
    
    story.append(Spacer(1, 0.3*cm))
    
    # PLAN
    story.append(Paragraph("PLAN", styles['SectionHeader']))
    
    plan = soap.get('plan', {})
    if plan.get('treatment_plan'):
        story.append(Paragraph(f"<b>Treatment Strategy:</b> {plan['treatment_plan']}", styles['Body']))
    
    meds_prescribed = plan.get('medications_prescribed', [])
    if meds_prescribed:
        story.append(Paragraph("<b>Medications Prescribed:</b>", styles['SubSection']))
        for med in meds_prescribed:
            story.append(Paragraph(
                f"• {med.get('medication')} {med.get('dose')} {med.get('route')} {med.get('frequency')} for {med.get('duration')} - {med.get('indication')}",
                styles['Bullet']
            ))
    
    investigations_ordered = plan.get('investigations_ordered', [])
    if investigations_ordered:
        story.append(Paragraph("<b>Investigations Ordered:</b>", styles['SubSection']))
        for inv in investigations_ordered:
            story.append(Paragraph(
                f"• [{inv.get('urgency', 'routine').upper()}] {inv.get('test_name')} - {inv.get('indication')}",
                styles['Bullet']
            ))
    
    referrals = plan.get('referrals', [])
    if referrals:
        story.append(Paragraph("<b>Referrals:</b>", styles['SubSection']))
        for ref in referrals:
            story.append(Paragraph(
                f"• {ref.get('specialty')} ({ref.get('urgency')}) - {ref.get('reason')}",
                styles['Bullet']
            ))
    
    follow_up = plan.get('follow_up', {})
    if follow_up.get('required'):
        story.append(Paragraph("<b>Follow-up:</b>", styles['SubSection']))
        story.append(Paragraph(
            f"• {follow_up.get('timeframe')} with {follow_up.get('with_whom', 'clinician')} - {follow_up.get('reason')}",
            styles['Bullet']
        ))
    
    safety_netting = plan.get('safety_netting', [])
    if safety_netting:
        story.append(Paragraph("<b>Safety Netting:</b>", styles['SubSection']))
        for item in safety_netting:
            story.append(Paragraph(f"• {item}", styles['Bullet']))
    
    # === FOLLOW-UP TASKS ===
    if tasks:
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("FOLLOW-UP TASKS", styles['SectionHeader']))
        
        # Group by urgency
        stat_tasks = [t for t in tasks if t.get('urgency') == 'stat']
        urgent_tasks = [t for t in tasks if t.get('urgency') == 'urgent']
        routine_tasks = [t for t in tasks if t.get('urgency') in ['routine', 'low']]
        
        if stat_tasks:
            story.append(Paragraph("<b>STAT (Immediate):</b>", styles['SubSection']))
            for task in stat_tasks:
                story.append(Paragraph(
                    f"• [{task.get('task_type').replace('_', ' ').upper()}] {task.get('description')} - Assigned to: {task.get('owner_role')}",
                    styles['Bullet']
                ))
        
        if urgent_tasks:
            story.append(Paragraph("<b>Urgent:</b>", styles['SubSection']))
            for task in urgent_tasks:
                story.append(Paragraph(
                    f"• [{task.get('task_type').replace('_', ' ').upper()}] {task.get('description')} - Assigned to: {task.get('owner_role')}",
                    styles['Bullet']
                ))
        
        if routine_tasks:
            story.append(Paragraph("<b>Routine:</b>", styles['SubSection']))
            for task in routine_tasks:
                story.append(Paragraph(
                    f"• [{task.get('task_type').replace('_', ' ').upper()}] {task.get('description')} - Assigned to: {task.get('owner_role')}",
                    styles['Bullet']
                ))
    
    # === HANDOVER (New Page) ===
    if handover and any(handover.values()):
        story.append(PageBreak())
        story.append(Paragraph("CLINICAL HANDOVER", styles['Title']))
        story.append(Spacer(1, 0.3*cm))
        
        if handover.get('situation'):
            story.append(Paragraph("<b>Situation:</b>", styles['SubSection']))
            story.append(Paragraph(handover['situation'], styles['Body']))
        
        if handover.get('background'):
            story.append(Paragraph("<b>Background:</b>", styles['SubSection']))
            story.append(Paragraph(handover['background'], styles['Body']))
        
        if handover.get('assessment'):
            story.append(Paragraph("<b>Assessment:</b>", styles['SubSection']))
            story.append(Paragraph(handover['assessment'], styles['Body']))
        
        if handover.get('recommendation'):
            story.append(Paragraph("<b>Recommendation:</b>", styles['SubSection']))
            story.append(Paragraph(handover['recommendation'], styles['Body']))
        
        if handover.get('active_issues'):
            story.append(Paragraph("<b>Active Issues:</b>", styles['SubSection']))
            for issue in handover['active_issues']:
                story.append(Paragraph(f"• {issue}", styles['Bullet']))
        
        if handover.get('escalation_criteria'):
            story.append(Paragraph("<b>Escalation Criteria:</b>", styles['SubSection']))
            for criteria in handover['escalation_criteria']:
                story.append(Paragraph(f"• {criteria}", styles['Bullet']))
        
        if handover.get('next_review_time'):
            story.append(Paragraph(f"<b>Next Review:</b> {handover['next_review_time']}", styles['Body']))
    
    # === FOOTER ===
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        f"<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
        styles['Normal']
    ))
    story.append(Paragraph(
        "<i>This document was automatically generated from consultation transcript. Please review for accuracy.</i>",
        styles['Normal']
    ))
    
    # Build PDF
    doc.build(story)
    
    return output_path
