"""Render the reviewed Markdown thesis report to a shareable PDF."""
from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import BaseDocTemplate, Frame, Image, KeepTogether, PageTemplate, Paragraph, Spacer

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'BTP_FINAL_EXPERIMENTAL_REPORT.md'
OUTPUT=ROOT/'BTP_FINAL_EXPERIMENTAL_REPORT.pdf'
FONT=Path('C:/Windows/Fonts/arial.ttf')
BOLD=Path('C:/Windows/Fonts/arialbd.ttf')
pdfmetrics.registerFont(TTFont('ReportArial',str(FONT)))
pdfmetrics.registerFont(TTFont('ReportArialBold',str(BOLD)))
pdfmetrics.registerFontFamily('ReportArial',normal='ReportArial',bold='ReportArialBold')

styles={
 'title':ParagraphStyle('title',fontName='ReportArialBold',fontSize=18,leading=23,textColor=colors.HexColor('#17324d'),spaceAfter=14),
 'h2':ParagraphStyle('h2',fontName='ReportArialBold',fontSize=12.5,leading=16,textColor=colors.HexColor('#17324d'),spaceBefore=13,spaceAfter=6,keepWithNext=True),
 'p':ParagraphStyle('p',fontName='ReportArial',fontSize=9.3,leading=14,spaceAfter=8),
 'bullet':ParagraphStyle('bullet',fontName='ReportArial',fontSize=9.1,leading=13,leftIndent=16,firstLineIndent=-10,spaceAfter=5),
}

def format_inline(value:str)->str:
    value=html.escape(value)
    value=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',value)
    value=re.sub(r'`([^`]+)`',r'<font color="#195b80">\1</font>',value)
    return value.replace('  ',' ')

def page_canvas(canvas,doc):
    canvas.saveState()
    w,h=A4
    canvas.setStrokeColor(colors.HexColor('#cad5dd'))
    canvas.line(44,h-49,w-44,h-49)
    canvas.setFont('ReportArial',7.5)
    canvas.setFillColor(colors.HexColor('#5b6670'))
    canvas.drawString(44,h-39,'IIT Guwahati BTP | Bounded experimental report | 25 Oct 2026')
    canvas.drawRightString(w-44,29,f'{doc.page}')
    canvas.restoreState()

def build():
    doc=BaseDocTemplate(str(OUTPUT),pagesize=A4,leftMargin=48,rightMargin=48,topMargin=63,bottomMargin=51,title='BTP Final Experimental Report',author='Shivansh Gupta')
    frame=Frame(doc.leftMargin,doc.bottomMargin,doc.width,doc.height,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)
    doc.addPageTemplates(PageTemplate(id='main',frames=[frame],onPage=page_canvas))
    story=[]
    lines=SOURCE.read_text(encoding='utf-8').splitlines()
    paragraphs=[]
    def flush():
        if paragraphs:
            story.append(Paragraph(format_inline(' '.join(paragraphs)),styles['p']))
            paragraphs.clear()
    for line in lines:
        t=line.strip()
        if not t:
            flush();continue
        if t.startswith('# '):
            flush();story.append(Paragraph(format_inline(t[2:]),styles['title']))
        elif t.startswith('## '):
            flush();story.append(Paragraph(format_inline(t[3:]),styles['h2']))
        elif t.startswith('- '):
            flush();story.append(Paragraph('• '+format_inline(t[2:]),styles['bullet']))
        else:
            paragraphs.append(t)
    flush()
    figroot=ROOT/'reports/final_build'
    figures=[('Adult corrected development slices','adult_18_slice_differences.png'),('Frozen official Adult confirmation','adult_frozen_confirmation.png'),('External Bank replication','bank_external_slice_differences.png')]
    for label,name in figures:
        p=figroot/name
        if p.exists():
            im=Image(str(p)); ratio=min(doc.width/im.imageWidth,250/im.imageHeight)
            im.drawWidth=im.imageWidth*ratio;im.drawHeight=im.imageHeight*ratio
            story.append(Spacer(1,10));story.append(Paragraph(format_inline(label),styles['h2']));story.append(im)
    doc.build(story)
    print(OUTPUT)

if __name__=='__main__':build()
