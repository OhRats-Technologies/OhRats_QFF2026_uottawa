"""Typeset the audited Markdown report; optional reportlab dependency only.

Run with: uv run --with reportlab==4.4.9 python -m scripts.quantum_world_pdf
"""
import html,re,argparse
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle,getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.utils import ImageReader
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,KeepTogether


def inline(text):
    text=text.translate(str.maketrans({'₂':'2','₄':'4','†':'^dagger','–':'-','—':'-','−':'-','→':'->','×':'x','²':'^2','π':'pi','γ':'gamma','ρ':'rho','Δ':'Delta'}))
    text=html.escape(text)
    text=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',r'<link href="\2" color="#176f68">\1</link>',text)
    text=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',text)
    text=re.sub(r'`([^`]+)`',r'<font name="Courier" size="8">\1</font>',text)
    return text


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',default='quantum_world/REPORT.md')
    parser.add_argument('--output',default='output/pdf/quantum-worlds-report.pdf')
    parser.add_argument('--title',default='Quantum Worlds: coupling, physicality and learned representations')
    parser.add_argument('--footer',default='Quantum Worlds | Local simulation | 3 October 2026')
    parser.add_argument('--compact',action='store_true',help='Compact four-page style for short technical reports')
    args=parser.parse_args()
    source=Path(args.source);output=Path(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    width=475;styles=getSampleStyleSheet()
    styles.add(ParagraphStyle('BodyQ',fontName='Helvetica',fontSize=10,leading=14.5,spaceAfter=9,textColor=colors.HexColor('#252a2e')))
    styles.add(ParagraphStyle('TitleQ',fontName='Helvetica-Bold',fontSize=23,leading=27,spaceAfter=15,textColor=colors.HexColor('#163b38'),keepWithNext=True))
    styles.add(ParagraphStyle('SectionQ',fontName='Helvetica-Bold',fontSize=15,leading=19,spaceBefore=17,spaceAfter=9,keepWithNext=True))
    styles.add(ParagraphStyle('SubQ',fontName='Helvetica-Bold',fontSize=11.5,leading=15,spaceBefore=12,spaceAfter=8,keepWithNext=True))
    styles.add(ParagraphStyle('CaptionQ',fontSize=8.5,leading=11,textColor=colors.HexColor('#626b70'),spaceAfter=10))
    styles.add(ParagraphStyle('CellQ',fontName='Helvetica',fontSize=8,leading=11,alignment=TA_LEFT))
    if args.compact:
        styles['BodyQ'].fontSize=9.5;styles['BodyQ'].leading=13;styles['BodyQ'].spaceAfter=7
        styles['SectionQ'].fontSize=14;styles['SectionQ'].leading=18;styles['SectionQ'].spaceBefore=14;styles['SectionQ'].spaceAfter=8
        styles['CaptionQ'].fontSize=8;styles['CaptionQ'].leading=10
    lines=source.read_text().splitlines();story=[];i=0
    while i<len(lines):
        line=lines[i].strip();i+=1
        if not line:continue
        if line.startswith('#'):
            level=len(line)-len(line.lstrip('#'));name={1:'TitleQ',2:'SectionQ'}.get(level,'SubQ')
            story.append(Paragraph(inline(line.lstrip('#').strip()),styles[name]));continue
        if line.startswith('!['):
            match=re.fullmatch(r'!\[([^]]*)\]\(([^)]+)\)',line)
            path=(source.parent/match[2]).resolve();w,h=ImageReader(str(path)).getSize()
            scale=min(width/w,275/h);image=Image(str(path),width=w*scale,height=h*scale)
            story.append(KeepTogether([Spacer(1,5),image,Spacer(1,4),Paragraph(inline(match[1]),styles['CaptionQ'])]));continue
        if line.startswith('|'):
            rows=[line]
            while i<len(lines) and lines[i].strip().startswith('|'):rows.append(lines[i].strip());i+=1
            data=[]
            for row in rows:
                cells=[x.strip() for x in row.strip('|').split('|')]
                if all(re.fullmatch(r':?-+:?',x) for x in cells):continue
                data.append([Paragraph(inline(x),styles['CellQ']) for x in cells])
            count=len(data[0]);col=[width*.33]+[width*.67/(count-1)]*(count-1)
            table=Table(data,colWidths=col,repeatRows=1,hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e7eeec')),('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#7b9891')),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#dce3e0')),
                ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),6)]))
            story.append(KeepTogether([table,Spacer(1,11)]));continue
        bullet=line.startswith('- ')
        text=line[2:] if bullet else line
        while i<len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(('#','![','|','- ')):
            text+=' '+lines[i].strip();i+=1
        story.append(Paragraph(inline(text),styles['BodyQ'],bulletText='-' if bullet else None))
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#dce3e0'));canvas.line(60,43,535,43)
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#626b70'))
        canvas.drawString(60,29,args.footer);canvas.drawRightString(535,29,str(doc.page));canvas.restoreState()
    doc=SimpleDocTemplate(str(output),pagesize=(595,842),leftMargin=60,rightMargin=60,topMargin=49,bottomMargin=58,
        title=args.title,author='OhRats Technologies')
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(output)


if __name__=='__main__':main()
