from pathlib import Path
from datetime import datetime
import json
import pandas as pd
import streamlit as st

# Alternativa ao WeasyPrint para Streamlit Cloud
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    USE_REPORTLAB = True
except:
    USE_REPORTLAB = False

TEMPLATE_HTML = """
<!doctype html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            color: #111; 
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 { color: #0a6; border-bottom: 3px solid #0a6; padding-bottom: 10px; }
        h2 { color: #048; margin-top: 30px; }
        h3 { color: #666; }
        table { 
            border-collapse: collapse; 
            width: 100%;
            margin: 20px 0;
        }
        td, th { 
            border: 1px solid #ddd; 
            padding: 8px;
            text-align: left;
        }
        th { 
            background-color: #f0f0f0;
            font-weight: bold;
        }
        .metric {
            display: inline-block;
            padding: 10px;
            margin: 10px;
            background: #f9f9f9;
            border-left: 4px solid #0a6;
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #0a6;
        }
        .metric-label {
            font-size: 12px;
            color: #666;
        }
        .section {
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-radius: 5px;
        }
        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <h1>{{ title }}</h1>
    
    <div class="section">
        <p><b>Projeto:</b> {{ project }}</p>
        <p><b>Data:</b> {{ date }}</p>
        <p><b>Autor:</b> {{ author }}</p>
    </div>
    
    <div class="section">
        <h2>Resumo Executivo</h2>
        <p>{{ summary }}</p>
    </div>
    
    {% if metrics %}
    <div class="section">
        <h2>Métricas Principais</h2>
        {% for m in metrics %}
        <div class="metric">
            <div class="metric-value">{{ m.value }}</div>
            <div class="metric-label">{{ m.label }}</div>
        </div>
        {% endfor %}
    </div>
    {% endif %}
    
    {% if tables %}
    <div class="section">
        <h2>Análises Detalhadas</h2>
        {% for t in tables %}
        <h3>{{ t.title }}</h3>
        {{ t.html | safe }}
        {% if t.interpretation %}
        <p><i>{{ t.interpretation }}</i></p>
        {% endif %}
        {% endfor %}
    </div>
    {% endif %}
    
    {% if conclusions %}
    <div class="section">
        <h2>Conclusões</h2>
        {{ conclusions | safe }}
    </div>
    {% endif %}
    
    {% if recommendations %}
    <div class="section">
        <h2>Recomendações</h2>
        <ul>
        {% for r in recommendations %}
        <li>{{ r }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}
    
    <div class="footer">
        <p>Relatório gerado automaticamente pelo Sistema DMAIC - {{ org }}</p>
        <p>{{ timestamp }}</p>
    </div>
</body>
</html>
"""

def render_html_report(
    title,
    project,
    summary,
    author="Equipe DMAIC",
    org="Greenpeace",
    metrics=None,
    tables=None,
    conclusions=None,
    recommendations=None,
    out_html: Path = None,
    out_pdf: Path = None
):
    """Gera relatório HTML e opcionalmente PDF"""
    from jinja2 import Template
    
    # Prepara dados
    tmpl = Template(TEMPLATE_HTML)
    
    # Converte DataFrames para HTML
    if tables:
        for t in tables:
            if 'df' in t:
                t['html'] = t['df'].to_html(index=False, classes='table')
    
    # Renderiza
    html = tmpl.render(
        title=title,
        project=project,
        summary=summary,
        author=author,
        org=org,
        date=datetime.now().strftime("%Y-%m-%d"),
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        metrics=metrics,
        tables=tables,
        conclusions=conclusions,
        recommendations=recommendations
    )
    
    # Salva HTML
    if out_html:
        out_html.write_text(html, encoding="utf-8")
        st.success(f"Relatório HTML salvo: {out_html.name}")
    
    # Gera PDF se possível
    if out_pdf and USE_REPORTLAB:
        generate_pdf_report(
            title=title,
            project=project,
            summary=summary,
            author=author,
            metrics=metrics,
            tables=tables,
            conclusions=conclusions,
            recommendations=recommendations,
            out_pdf=out_pdf
        )
    
    return html

def generate_pdf_report(
    title,
    project,
    summary,
    author,
    metrics=None,
    tables=None,
    conclusions=None,
    recommendations=None,
    out_pdf: Path = None
):
    """Gera PDF usando ReportLab (alternativa ao WeasyPrint)"""
    if not USE_REPORTLAB:
        st.warning("ReportLab não disponível. PDF não será gerado.")
        return
    
    try:
        doc = SimpleDocTemplate(
            str(out_pdf),
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Container para elementos
        story = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#0a6600'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph(title, title_style))
        story.append(Spacer(1, 12))
        
        # Info do projeto
        story.append(Paragraph(f"<b>Projeto:</b> {project}", styles['Normal']))
        story.append(Paragraph(f"<b>Autor:</b> {author}", styles['Normal']))
        story.append(Paragraph(f"<b>Data:</b> {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Resumo
        story.append(Paragraph("<b>Resumo Executivo</b>", styles['Heading2']))
        story.append(Paragraph(summary, styles['Normal']))
        story.append(Spacer(1, 20))
        
        # Métricas
        if metrics:
            story.append(Paragraph("<b>Métricas Principais</b>", styles['Heading2']))
            for m in metrics:
                story.append(Paragraph(f"• {m['label']}: <b>{m['value']}</b>", styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Tabelas
        if tables:
            story.append(Paragraph("<b>Análises</b>", styles['Heading2']))
            for t in tables:
                if 'title' in t:
                    story.append(Paragraph(t['title'], styles['Heading3']))
                if 'df' in t and isinstance(t['df'], pd.DataFrame):
                    # Converte DataFrame para tabela ReportLab
                    data = [t['df'].columns.tolist()] + t['df'].values.tolist()
                    table = Table(data)
                    table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    story.append(table)
                story.append(Spacer(1, 12))
        
        # Conclusões
        if conclusions:
            story.append(PageBreak())
            story.append(Paragraph("<b>Conclusões</b>", styles['Heading2']))
            story.append(Paragraph(conclusions, styles['Normal']))
            story.append(Spacer(1, 20))
        
        # Recomendações
        if recommendations:
            story.append(Paragraph("<b>Recomendações</b>", styles['Heading2']))
            for r in recommendations:
                story.append(Paragraph(f"• {r}", styles['Normal']))
        
        # Gera PDF
        doc.build(story)
        st.success(f"Relatório PDF salvo: {out_pdf.name}")
        
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")

def save_analysis_manifest(phase, dataset_id, parameters, results, run_id=None):
    """Salva manifesto de análise para rastreabilidade"""
    from app.components.upload_and_store import RESULTS
    
    if not run_id:
        run_id = f"{phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    manifest = {
        "run_id": run_id,
        "phase": phase,
        "dataset_id": dataset_id,
        "timestamp": datetime.now().isoformat(),
        "parameters": parameters,
        "results": results
    }
    
    manifest_path = RESULTS / f"manifest_{run_id}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    
    return run_id, manifest_path
