"""
pdf_gen.py  —  Générateur PDF Devis BTP - Logo net et bien dimensionné
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, KeepTogether)
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
import os
from pathlib import Path
from datetime import datetime
from PIL import Image as PILImage
from io import BytesIO

def _fmt(v, dec=0):
    try:
        n = float(v or 0)
        if dec == 0:
            return f"{int(round(n)):,}".replace(",", " ")
        return f"{n:,.{dec}f}".replace(",", " ")
    except:
        return "0"

def _fmt_fcfa(v):
    return _fmt(v) + " FCFA"

def _fdate(s):
    try:
        return datetime.strptime(str(s), "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return str(s) if s else "—"

NOIR     = colors.HexColor("#000000")
BLEU     = colors.HexColor("#1565C0")
GRIS_HDR = colors.HexColor("#D9D9D9")
BLANC    = colors.white
GRIS_L   = colors.HexColor("#F5F5F5")
BORD     = colors.HexColor("#AAAAAA")
BORD_E   = colors.HexColor("#333333")

class NumCanvas(canvas.Canvas):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._pages = []
    def showPage(self):
        self._pages.append(dict(self.__dict__))
        self._startPage()
    def save(self):
        n = len(self._pages)
        for state in self._pages:
            self.__dict__.update(state)
            self._footer(self._pageNumber, n)
            super().showPage()
        super().save()
    def _footer(self, page, total):
        self.saveState()
        W, H = A4
        self.setStrokeColor(BORD)
        self.setLineWidth(0.5)
        self.line(1.5*cm, 1.8*cm, W-1.5*cm, 1.8*cm)
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#666666"))
        self.drawString(1.5*cm, 1.2*cm, "Document généré par DevisBTP · Togo")
        self.drawRightString(W-1.5*cm, 1.2*cm, f"Page {page} / {total}")
        self.restoreState()

def _S(name, **kw):
    return ParagraphStyle(name, **kw)

def generate_devis_pdf(devis, lignes, entreprise, output_path):
    W_PAGE, H_PAGE = A4
    MARGIN = 1.5*cm
    W = W_PAGE - 2*MARGIN

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=1.5*cm, bottomMargin=2.5*cm,
        title=f"Devis {devis.get('numero','')}"
    )
    ent = entreprise
    story = []

    # ---------- EN-TÊTE ----------
    sigle = (ent.get("sigle", "") or "").strip()
    nom = (ent.get("nom", "") or "").strip()
    slogan = (ent.get("slogan", "") or "").strip()
    adresse = " · ".join(filter(None, [
        ent.get("adresse", ""), ent.get("quartier", ""),
        ent.get("ville", ""), ent.get("pays", "")
    ])).strip()
    tel1 = ent.get("telephone1", "").strip()
    tel2 = ent.get("telephone2", "").strip()
    email = ent.get("email", "").strip()
    site = ent.get("site_web", "").strip()

    titre_principal = (sigle.upper() if sigle else nom.upper())
    sous_titre = nom.upper() if sigle else ""

    ent_block = []
    ent_block.append(Paragraph(titre_principal, _S("tp",
        fontName="Helvetica-Bold", fontSize=16, textColor=NOIR,
        alignment=TA_CENTER, leading=20)))
    if sous_titre:
        ent_block.append(Paragraph(sous_titre, _S("st",
            fontName="Helvetica-Bold", fontSize=10, textColor=BLEU,
            alignment=TA_CENTER, leading=13)))
    if slogan:
        ent_block.append(Paragraph(f"<i>{slogan}</i>", _S("sl",
            fontName="Helvetica-Oblique", fontSize=7.5, textColor=BLEU,
            alignment=TA_CENTER, leading=11)))
    if adresse:
        ent_block.append(Paragraph(adresse, _S("ad",
            fontName="Helvetica", fontSize=7.5, textColor=NOIR,
            alignment=TA_CENTER, leading=10)))
    contacts = []
    if tel1 or tel2:
        contacts.append(f"Tél : {' / '.join(filter(None, [tel1, tel2]))}")
    if email:
        contacts.append(f'<a href="mailto:{email}">Email : {email}</a>')
    if site:
        if not site.startswith("http"):
            site = "http://" + site
        contacts.append(f'<a href="{site}">Web : {site}</a>')
    if contacts:
        ent_block.append(Paragraph("  ".join(contacts), _S("ct",
            fontName="Helvetica", fontSize=7.5, textColor=NOIR,
            alignment=TA_CENTER, leading=10)))

    # ---------- LOGO : redimensionnement PIL de haute qualité ----------
    logo_rl = None
    logo_path = ent.get("logo_path", "")
    if logo_path and os.path.exists(logo_path):
        try:
            pil_img = PILImage.open(logo_path)
            # Hauteur cible : 2.5 cm (convertie en points)
            target_h = 2.5 * 28.346
            ratio = target_h / pil_img.height
            target_w = pil_img.width * ratio
            # Redimension avec LANCZOS (qualité maximale)
            pil_img = pil_img.resize((int(target_w), int(target_h)), PILImage.LANCZOS)
            # Convertir en bytes pour ReportLab
            buf = BytesIO()
            pil_img.save(buf, format='PNG')
            buf.seek(0)
            logo_rl = RLImage(buf)
            logo_rl.drawWidth = target_w
            logo_rl.drawHeight = target_h
        except Exception as e:
            print(f"[ERREUR Logo] {e}")
            logo_rl = None

    if logo_rl:
        logo_width = logo_rl.drawWidth
        logo_col = logo_width + 0.2*cm
        text_col = W - logo_col
        hdr_table = Table([[logo_rl, ent_block]], colWidths=[logo_col, text_col])
    else:
        hdr_table = Table([[ent_block]], colWidths=[W])

    hdr_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(hdr_table)
    story.append(Spacer(1, 3*mm))
    story.append(HRFlowable(width="100%", thickness=1.5, color=NOIR, spaceAfter=1*mm))
    story.append(HRFlowable(width="100%", thickness=0.4, color=NOIR, spaceAfter=4*mm))
    story.append(Paragraph(
        "<u><b>DEVIS QUANTITATIF ET ESTIMATIF</b></u>",
        _S("titre", fontName="Helvetica-Bold", fontSize=12,
           textColor=NOIR, alignment=TA_CENTER, leading=16, spaceAfter=6)
    ))

    # ---------- TABLEAU ----------
    CW = [W*0.52, W*0.07, W*0.09, W*0.16, W*0.16]

    def _th(txt, align=TA_CENTER):
        return Paragraph(f"<b>{txt}</b>", _S("th",
            fontName="Helvetica-Bold", fontSize=8, textColor=NOIR,
            alignment=align, leading=11))

    def _tc(txt, align=TA_LEFT, bold=False):
        fn = "Helvetica-Bold" if bold else "Helvetica"
        return Paragraph(str(txt), _S("tc", fontName=fn, fontSize=8,
            textColor=NOIR, alignment=align, leading=11))

    def _tc_num(txt):
        return Paragraph(str(txt), _S("tn", fontName="Helvetica", fontSize=8,
            textColor=NOIR, alignment=TA_RIGHT, leading=11))

    header = [
        _th("Désignation", TA_LEFT),
        _th("U"),
        _th("Qté"),
        _th("Prix Unitaire"),
        _th("Montant"),
    ]
    tdata = [header]
    tstyle = [
        ('BACKGROUND', (0,0), (-1,0), GRIS_HDR),
        ('ALIGN', (0,0), (0,0), 'LEFT'),
        ('ALIGN', (1,0), (-1,0), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, BORD),
        ('BOX', (0,0), (-1,-1), 1.0, BORD_E),
        ('ALIGN', (1,1), (-1,-1), 'CENTER'),
        ('ALIGN', (3,1), (4,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]

    sec_num = 0
    item_num = 0
    for l in lignes:
        tl = l.get("type_ligne", "item")
        ri = len(tdata)
        mont = float(l.get("montant", 0) or 0)

        if tl == "section":
            sec_num += 1
            item_num = 0
            tdata.append([
                Paragraph(f"<b>{l.get('designation','')}</b>", _S("sec",
                    fontName="Helvetica-Bold", fontSize=8.5, textColor=NOIR,
                    alignment=TA_CENTER, leading=12)),
                "", "", "", ""
            ])
            tstyle += [
                ('SPAN', (0,ri), (-1,ri)),
                ('BACKGROUND', (0,ri), (-1,ri), GRIS_HDR),
                ('ALIGN', (0,ri), (-1,ri), 'CENTER'),
            ]
        elif tl == "subtotal":
            tdata.append([
                Paragraph(f"<b>{l.get('designation','Sous-total')}</b>", _S("st",
                    fontName="Helvetica-Bold", fontSize=8, textColor=NOIR,
                    alignment=TA_RIGHT, leading=11)),
                "", "", "",
                _tc_num(_fmt(mont))
            ])
            tstyle += [
                ('SPAN', (0,ri), (3,ri)),
                ('BACKGROUND', (0,ri), (-1,ri), colors.HexColor("#E8EAF6")),
                ('LINEABOVE', (0,ri), (-1,ri), 0.8, NOIR),
            ]
        elif tl == "comment":
            tdata.append([
                Paragraph(f"<i>{l.get('designation','')}</i>", _S("cm",
                    fontName="Helvetica-Oblique", fontSize=8, textColor=NOIR,
                    alignment=TA_CENTER, leading=11)),
                "", "", "", ""
            ])
            tstyle += [
                ('SPAN', (0,ri), (-1,ri)),
                ('ALIGN', (0,ri), (-1,ri), 'CENTER'),
                ('BACKGROUND', (0,ri), (-1,ri), colors.HexColor("#F9F9F9")),
            ]
        else:
            item_num += 1
            num = f"{sec_num}.{item_num}" if sec_num else str(item_num)
            qte = float(l.get("quantite", 0) or 0)
            pu = float(l.get("prix_unitaire", 0) or 0)
            qs = str(int(qte)) if qte == int(qte) else f"{qte:.2f}"
            bg = GRIS_L if item_num % 2 == 0 else BLANC
            tdata.append([
                _tc(f"{num}  {l.get('designation','')}"),
                _tc(l.get("unite", ""), TA_CENTER),
                _tc(qs, TA_CENTER),
                _tc_num(_fmt(pu)),
                _tc_num(_fmt(mont)),
            ])
            tstyle.append(('BACKGROUND', (0,ri), (-1,ri), bg))

    tbl = Table(tdata, colWidths=CW, repeatRows=1)
    tbl.setStyle(TableStyle(tstyle))
    story.append(tbl)
    story.append(Spacer(1, 5*mm))

    # ---------- TOTAUX ----------
    ht = float(devis.get("montant_ht", 0) or 0)
    tva_t = float(devis.get("tva_taux", 0) or 0)
    tva = float(devis.get("montant_tva", 0) or 0)
    ttc = float(devis.get("montant_ttc", 0) or 0)

    def _recap_row(label, valeur, bold=False):
        fn = "Helvetica-Bold" if bold else "Helvetica"
        sz = 9 if bold else 8
        return [
            Paragraph(f"<b>{label}</b>" if bold else label,
                      _S("rl", fontName=fn, fontSize=sz, textColor=NOIR,
                         alignment=TA_RIGHT, leading=12)),
            Paragraph(f"<b>{valeur} FCFA</b>" if bold else f"{valeur} FCFA",
                      _S("rv", fontName=fn, fontSize=sz, textColor=NOIR,
                         alignment=TA_RIGHT, leading=12)),
        ]

    recap_data = [
        _recap_row("Total Hors Taxes (HT) :", _fmt(ht)),
        _recap_row(f"TVA ({tva_t:.0f} %) :", _fmt(tva)),
        _recap_row("MONTANT TOTAL TTC :", _fmt(ttc), bold=True),
    ]
    recap_w = [5.5*cm, 4.5*cm]
    recap_t = Table(recap_data, colWidths=recap_w)
    recap_t.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, BORD),
        ('BOX', (0,0), (-1,-1), 1, BORD_E),
        ('BACKGROUND', (0,0), (1,1), colors.HexColor("#F9F9F9")),
        ('BACKGROUND', (0,2), (1,2), GRIS_HDR),
        ('LINEABOVE', (0,2), (1,2), 1.2, NOIR),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
    ]))
    align_row = Table([[Spacer(W - 10.3*cm, 1), recap_t]],
                      colWidths=[W - 10.3*cm, 10.3*cm])
    align_row.setStyle(TableStyle([('LEFTPADDING', (0,0), (-1,-1), 0),
                                   ('RIGHTPADDING', (0,0), (-1,-1), 0)]))
    story.append(align_row)
    story.append(Spacer(1, 6*mm))

    # ---------- CONDITIONS ET SIGNATURES ----------
    cond = (devis.get("conditions_reglement", "") or ent.get("conditions_def", "") or "").strip()
    notes = (devis.get("notes", "") or "").strip()
    delai = (devis.get("delai_execution", "") or "").strip()
    banque = (ent.get("banque", "") or "").strip()
    rib = (ent.get("rib", "") or "").strip()

    left_items = []
    if cond: left_items.append(("CONDITIONS DE RÈGLEMENT", cond))
    if delai: left_items.append(("DÉLAI D'EXÉCUTION", delai))
    if banque or rib:
        bc = " | ".join(filter(None, [f"Banque : {banque}" if banque else "", f"RIB : {rib}" if rib else ""]))
        left_items.append(("COORDONNÉES BANCAIRES", bc))
    if notes: left_items.append(("NOTES", notes))

    left_flow = []
    for title, txt in left_items:
        left_flow.append(Paragraph(f"<b><u>{title}</u></b>", _S("lt",
            fontName="Helvetica-Bold", fontSize=7, textColor=NOIR, leading=9)))
        left_flow.append(Paragraph(txt, _S("lb",
            fontName="Helvetica", fontSize=6.5, textColor=NOIR, leading=8, spaceAfter=2)))

    ville_ent = ent.get("ville", "Lomé")
    date_str = _fdate(devis.get("date_creation", ""))
    sig_lieu = f"Fait à {ville_ent}, le {date_str}"

    sig_data = [
        [Paragraph("<b>Pour l'Entreprise</b>", _S("sh", fontName="Helvetica-Bold", fontSize=6.5, textColor=NOIR, alignment=TA_CENTER)),
         Paragraph("<b>Bon pour Accord – Client</b>", _S("sh2", fontName="Helvetica-Bold", fontSize=6.5, textColor=NOIR, alignment=TA_CENTER))],
        [Paragraph(sig_lieu, _S("sl", fontName="Helvetica-Oblique", fontSize=6, textColor=NOIR, alignment=TA_CENTER)),
         Paragraph(sig_lieu, _S("sl2", fontName="Helvetica-Oblique", fontSize=6, textColor=NOIR, alignment=TA_CENTER))],
        [Spacer(1, 1.2*cm), Spacer(1, 1.2*cm)],
        [Paragraph("Signature & Cachet", _S("ss", fontName="Helvetica", fontSize=6, textColor=NOIR, alignment=TA_CENTER)),
         Paragraph("Date & Signature", _S("ss2", fontName="Helvetica", fontSize=6, textColor=NOIR, alignment=TA_CENTER))],
        [Paragraph("_ _ _ _ _ _ _ _ _ _", _S("sl3", fontName="Helvetica", fontSize=6, textColor=colors.HexColor("#BBBBBB"), alignment=TA_CENTER)),
         Paragraph("_ _ _ _ _ _ _ _ _ _", _S("sl4", fontName="Helvetica", fontSize=6, textColor=colors.HexColor("#BBBBBB"), alignment=TA_CENTER))],
    ]

    left_width = 4.5*cm
    space = 0.4*cm
    sig_width = W - left_width - space
    sig_half = sig_width / 2
    sig_tbl = Table(sig_data, colWidths=[sig_half, sig_half])
    sig_tbl.setStyle(TableStyle([
        ('BOX', (0,0), (0,-1), 0.5, BORD_E),
        ('BOX', (1,0), (1,-1), 0.5, BORD_E),
        ('LINEBETWEEN', (0,0), (1,-1), 3, BLANC),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor("#F0F0F0")),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor("#EEF4FF")),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))

    if not left_flow:
        left_flow = [Spacer(1, 1)]

    bottom_table = Table(
        [[left_flow, Spacer(space, 1), sig_tbl]],
        colWidths=[left_width, space, sig_width]
    )
    bottom_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(KeepTogether(bottom_table))

    doc.build(story, canvasmaker=NumCanvas)
    return output_path
