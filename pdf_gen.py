"""
pdf_gen.py  —  Générateur PDF Devis BTP (thème Blanc / Bleu professionnel)
Format Togo · Devise FCFA · ReportLab
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, Image, KeepTogether)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
import os
from pathlib import Path
from datetime import datetime

# ── Palette Blanc / Bleu ─────────────────────────────────────────────────────
BLEU_FONCE  = colors.HexColor("#0D47A1")   # bleu marine foncé
BLEU_MED    = colors.HexColor("#1565C0")   # bleu principal
BLEU_CLAIR  = colors.HexColor("#1976D2")   # bleu moyen
BLEU_TBL    = colors.HexColor("#E3F2FD")   # bleu très clair (lignes paires)
BLEU_LIGNE  = colors.HexColor("#BBDEFB")   # bleu clair séparateur
ORANGE      = colors.HexColor("#E65100")   # orange accent (total TTC)
BLANC       = colors.white
NOIR        = colors.HexColor("#212121")
GRIS_TEXTE  = colors.HexColor("#546E7A")
GRIS_BORD   = colors.HexColor("#90CAF9")
GRIS_FOND   = colors.HexColor("#F8FBFF")   # fond très légèrement bleuté

def fmt(v, dec=0):
    try: return f"{int(round(float(v))):,}".replace(",", " ")
    except: return "0"

def fmt_fcfa(v):
    return fmt(v) + " FCFA"

def fdate(d):
    try: return datetime.strptime(str(d), "%Y-%m-%d").strftime("%d/%m/%Y")
    except: return str(d) if d else "—"

# ── Canvas numérotation ───────────────────────────────────────────────────────
class PageCanvas(canvas.Canvas):
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
        # Ligne bleue bas de page
        self.setStrokeColor(BLEU_MED)
        self.setLineWidth(1.5)
        self.line(1.5*cm, 2.0*cm, W-1.5*cm, 2.0*cm)
        # Texte
        self.setFont("Helvetica", 7)
        self.setFillColor(GRIS_TEXTE)
        self.drawString(1.5*cm, 1.5*cm, "Document généré par DevisBTP  •  Togo")
        self.drawCentredString(W/2, 1.5*cm, "Ce devis est valable jusqu'à la date indiquée — TVA incluse au taux légal")
        self.drawRightString(W-1.5*cm, 1.5*cm, f"Page {page} / {total}")
        self.restoreState()

# ── Styles texte ──────────────────────────────────────────────────────────────
def S(name, **kw):
    return ParagraphStyle(name, **kw)

def make_styles():
    base = dict(fontName="Helvetica", fontSize=8, textColor=NOIR, leading=11)
    return {
        'ent_nom'  : S("en", fontName="Helvetica-Bold",   fontSize=13, textColor=BLEU_FONCE, leading=16),
        'ent_sub'  : S("es", fontName="Helvetica-Oblique",fontSize=8,  textColor=BLEU_CLAIR, leading=10),
        'ent_info' : S("ei", fontName="Helvetica",        fontSize=7.5,textColor=GRIS_TEXTE, leading=10),
        'ent_id'   : S("eid",fontName="Helvetica-Bold",   fontSize=7.5,textColor=GRIS_TEXTE, leading=10),
        'devis_num': S("dn", fontName="Helvetica-Bold",   fontSize=22, textColor=BLEU_FONCE, leading=26, alignment=TA_CENTER),
        'devis_ref': S("dr", fontName="Helvetica-Bold",   fontSize=11, textColor=BLANC,      leading=14, alignment=TA_CENTER),
        'bloc_hdr' : S("bh", fontName="Helvetica-Bold",   fontSize=8,  textColor=BLANC,      leading=11),
        'bloc_lbl' : S("bl", fontName="Helvetica-Bold",   fontSize=7.5,textColor=GRIS_TEXTE, leading=10),
        'bloc_val' : S("bv", fontName="Helvetica",        fontSize=8,  textColor=NOIR,       leading=11),
        'bloc_val_b':S("bvb",fontName="Helvetica-Bold",   fontSize=8.5,textColor=BLEU_FONCE, leading=12),
        'tbl_hdr'  : S("th", fontName="Helvetica-Bold",   fontSize=7.5,textColor=BLANC,      leading=10, alignment=TA_CENTER),
        'tbl_hdr_l': S("thl",fontName="Helvetica-Bold",   fontSize=7.5,textColor=BLANC,      leading=10),
        'tbl_sec'  : S("ts", fontName="Helvetica-Bold",   fontSize=8,  textColor=BLANC,      leading=11),
        'tbl_item' : S("ti", fontName="Helvetica",        fontSize=7.5,textColor=NOIR,       leading=10),
        'tbl_item_r':S("tir",fontName="Helvetica",        fontSize=7.5,textColor=NOIR,       leading=10, alignment=TA_RIGHT),
        'tbl_item_c':S("tic",fontName="Helvetica",        fontSize=7.5,textColor=NOIR,       leading=10, alignment=TA_CENTER),
        'tbl_sub'  : S("tsb",fontName="Helvetica-Bold",   fontSize=7.5,textColor=BLEU_FONCE, leading=10),
        'tbl_sub_r': S("tsr",fontName="Helvetica-Bold",   fontSize=7.5,textColor=BLEU_FONCE, leading=10, alignment=TA_RIGHT),
        'tbl_cmt'  : S("tc", fontName="Helvetica-Oblique",fontSize=7,  textColor=GRIS_TEXTE, leading=10),
        'tot_lbl'  : S("tl", fontName="Helvetica-Bold",   fontSize=8.5,textColor=GRIS_TEXTE, leading=12, alignment=TA_RIGHT),
        'tot_val'  : S("tv", fontName="Helvetica",        fontSize=8.5,textColor=NOIR,       leading=12, alignment=TA_RIGHT),
        'ttc_lbl'  : S("ttl",fontName="Helvetica-Bold",   fontSize=11, textColor=BLANC,      leading=14, alignment=TA_RIGHT),
        'ttc_val'  : S("ttv",fontName="Helvetica-Bold",   fontSize=11, textColor=BLANC,      leading=14, alignment=TA_RIGHT),
        'note'     : S("nt", fontName="Helvetica-Oblique",fontSize=7,  textColor=GRIS_TEXTE, leading=9),
        'cond_hdr' : S("ch", fontName="Helvetica-Bold",   fontSize=8,  textColor=BLEU_MED,   leading=11),
        'cond_val' : S("cv", fontName="Helvetica",        fontSize=7.5,textColor=NOIR,       leading=10),
        'sig_hdr'  : S("sh", fontName="Helvetica-Bold",   fontSize=7.5,textColor=BLANC,      leading=10, alignment=TA_CENTER),
        'sig_txt'  : S("st", fontName="Helvetica",        fontSize=7,  textColor=GRIS_TEXTE, leading=9,  alignment=TA_CENTER),
    }

# ── Générateur principal ──────────────────────────────────────────────────────
def generate_devis_pdf(devis, lignes, entreprise, output_path):
    W_PAGE, H_PAGE = A4
    MARGIN = 1.5*cm
    W = W_PAGE - 2*MARGIN

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=1.5*cm, bottomMargin=2.8*cm,
        title=f"Devis {devis.get('numero','')}"
    )
    ST   = make_styles()
    story = []
    ent  = entreprise

    # ══════════════════════════════════════════════════════════════════════
    # EN-TÊTE : logo + infos entreprise + bandeau "DEVIS Nº"
    # ══════════════════════════════════════════════════════════════════════
    # -- Logo
    logo_img = ""
    lp = ent.get("logo_path","")
    if lp and os.path.exists(lp):
        try:
            img = Image(lp)
            img._restrictSize(4*cm, 2.2*cm)
            logo_img = img
        except: pass

    # -- Texte entreprise
    def ent_block():
        b = []
        nom = ent.get("nom","") or "Entreprise"
        sigle = ent.get("sigle","")
        forme = ent.get("forme_juridique","")
        titre = nom + (f"  ({sigle})" if sigle else "")
        b.append(Paragraph(titre, ST['ent_nom']))
        if forme or ent.get("slogan",""):
            sub = " · ".join(filter(None,[forme, ent.get("slogan","")]))
            b.append(Paragraph(sub, ST['ent_sub']))
        b.append(Spacer(1,2*mm))
        adr = " · ".join(filter(None,[
            ent.get("adresse",""), ent.get("quartier",""),
            ent.get("ville",""), ent.get("pays","")]))
        if adr: b.append(Paragraph(adr, ST['ent_info']))
        tels = " / ".join(filter(None,[ent.get("telephone1",""),ent.get("telephone2","")]))
        if tels: b.append(Paragraph(f"Tél : {tels}", ST['ent_info']))
        if ent.get("email"):    b.append(Paragraph(f"Email : {ent['email']}", ST['ent_info']))
        if ent.get("site_web"): b.append(Paragraph(f"Web : {ent['site_web']}", ST['ent_info']))
        b.append(Spacer(1,2*mm))
        ids = " | ".join(filter(None,[
            f"RCCM : {ent['rccm']}" if ent.get("rccm") else "",
            f"NIF : {ent['nif']}"   if ent.get("nif")  else ""]))
        if ids: b.append(Paragraph(ids, ST['ent_id']))
        return b

    # -- Bandeau DEVIS numéro (colonne droite)
    num_data = [
        [Paragraph("DEVIS", ST['devis_num'])],
        [Paragraph(f"N°  {devis.get('numero','')}", ST['devis_ref'])],
    ]
    num_table = Table(num_data, colWidths=[5.5*cm])
    num_table.setStyle(TableStyle([
        ('BACKGROUND',    (0,0),(0,0), GRIS_FOND),
        ('BACKGROUND',    (0,1),(0,1), BLEU_MED),
        ('BOX',           (0,0),(0,-1), 1.5, BLEU_MED),
        ('LINEBELOW',     (0,0),(0,0),  1,   BLEU_LIGNE),
        ('TOPPADDING',    (0,0),(0,-1), 8),
        ('BOTTOMPADDING', (0,0),(0,-1), 8),
        ('ROUNDEDCORNERS',[3]),
    ]))

    logo_w = 4*cm if logo_img else 0
    ent_w  = W - logo_w - 5.5*cm - 0.4*cm
    if logo_img:
        hdr_data = [[logo_img, ent_block(), num_table]]
        hdr_cols = [logo_w+0.2*cm, ent_w, 5.5*cm]
    else:
        hdr_data = [[ent_block(), num_table]]
        hdr_cols = [W - 5.5*cm - 0.2*cm, 5.5*cm]

    hdr_table = Table(hdr_data, colWidths=hdr_cols)
    hdr_table.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),
        ('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),
        ('BOTTOMPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(hdr_table)
    story.append(Spacer(1,3*mm))

    # Ligne séparatrice bleue double
    story.append(HRFlowable(width="100%", thickness=3, color=BLEU_MED, spaceAfter=1*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BLEU_LIGNE, spaceAfter=3*mm))

    # ══════════════════════════════════════════════════════════════════════
    # BLOCS : CLIENT  +  INFOS DEVIS (sans icônes)
    # ══════════════════════════════════════════════════════════════════════
    def info_card(titre, rows, accent=BLEU_MED):
        """Crée un bloc info avec en-tête bleu et contenu blanc."""
        data = [[Paragraph(titre.upper(), ST['bloc_hdr'])]]
        style = [
            ('BACKGROUND',(0,0),(0,0), accent),
            ('TOPPADDING',(0,0),(-1,-1), 4),
            ('BOTTOMPADDING',(0,0),(-1,-1), 4),
            ('LEFTPADDING',(0,0),(-1,-1), 7),
            ('RIGHTPADDING',(0,0),(-1,-1), 5),
            ('BOX',(0,0),(-1,-1), 1, BLEU_LIGNE),
        ]
        for i,(lbl,val) in enumerate(rows):
            if lbl:
                data.append([Table([[Paragraph(lbl, ST['bloc_lbl']),
                                     Paragraph(str(val), ST['bloc_val'])]],
                             colWidths=[2.4*cm, None],
                             style=[('LEFTPADDING',(0,0),(-1,-1),0),
                                    ('RIGHTPADDING',(0,0),(-1,-1),0),
                                    ('BOTTOMPADDING',(0,0),(-1,-1),1),
                                    ('TOPPADDING',(0,0),(-1,-1),1)])])
            else:
                data.append([Paragraph(str(val), ST['bloc_val_b'])])
            bg = BLANC if i%2==0 else GRIS_FOND
            style.append(('BACKGROUND',(0,i+1),(0,i+1), bg))
        t = Table(data, colWidths=[(W/2 - 4*mm)])
        t.setStyle(TableStyle(style))
        return t

    # Infos client
    cli_rows = [("", devis.get('client_nom','—'))]
    if devis.get('client_adresse'): cli_rows.append(("Adresse :", devis['client_adresse']))
    if devis.get('client_ville'):   cli_rows.append(("Ville :",   devis['client_ville']))
    if devis.get('client_tel'):     cli_rows.append(("Tél :",     devis['client_tel']))
    if devis.get('client_email'):   cli_rows.append(("Email :",   devis['client_email']))
    if devis.get('client_nif'):     cli_rows.append(("NIF :",     devis['client_nif']))

    # Infos devis
    statut = devis.get('statut','Brouillon')
    statut_colors = {'Accepté':'Accepté','Envoyé':'Envoyé',
                     'Facturé':'Facturé','Refusé':'Refusé',
                     'Brouillon':'Brouillon'}
    dev_rows = [
        ("Date :",       fdate(devis.get('date_creation',''))),
        ("Validité :",   fdate(devis.get('date_validite',''))),
        ("Statut :",     statut_colors.get(statut, statut)),
        ("Chantier :",   devis.get('chantier','') or '—'),
    ]
    if devis.get('localisation'):    dev_rows.append(("Localisation :", devis['localisation']))
    if devis.get('delai_execution'): dev_rows.append(("Délai :",        devis['delai_execution']))

    blocs = Table(
        [[info_card("Client / Maître d'ouvrage", cli_rows),
          Spacer(8*mm,1),
          info_card("Informations du devis", dev_rows, BLEU_CLAIR)]],
        colWidths=[W/2 - 4*mm, 8*mm, W/2 - 4*mm]
    )
    blocs.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),
        ('RIGHTPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(blocs)

    # Objet des travaux
    if devis.get('description'):
        story.append(Spacer(1,3*mm))
        obj_data = [
            [Paragraph("OBJET DES TRAVAUX", ST['bloc_hdr'])],
            [Paragraph(devis['description'], ST['cond_val'])],
        ]
        obj_t = Table(obj_data, colWidths=[W])
        obj_t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(0,0), BLEU_MED),
            ('BACKGROUND',(0,1),(0,1), GRIS_FOND),
            ('BOX',(0,0),(0,-1), 1, BLEU_LIGNE),
            ('LINEBELOW',(0,0),(0,0), 0.5, BLEU_LIGNE),
            ('TOPPADDING',(0,0),(-1,-1), 5),
            ('BOTTOMPADDING',(0,0),(-1,-1), 5),
            ('LEFTPADDING',(0,0),(-1,-1), 8),
        ]))
        story.append(obj_t)

    story.append(Spacer(1,5*mm))

    # ══════════════════════════════════════════════════════════════════════
    # TABLEAU DES PRESTATIONS
    # ══════════════════════════════════════════════════════════════════════
    CW = [0.9*cm, 7.5*cm, 1.3*cm, 1.4*cm, 2.3*cm, 2.3*cm]  # Total ≈ W

    hdr_row = [
        Paragraph("N°",           ST['tbl_hdr']),
        Paragraph("DÉSIGNATION DES TRAVAUX", ST['tbl_hdr_l']),
        Paragraph("UNITÉ",        ST['tbl_hdr']),
        Paragraph("QTÉ",          ST['tbl_hdr']),
        Paragraph("P.U. (FCFA)",  ST['tbl_hdr']),
        Paragraph("MONTANT (FCFA)",ST['tbl_hdr']),
    ]
    tdata  = [hdr_row]
    tstyle = [
        # En-tête
        ('BACKGROUND',    (0,0),(-1,0), BLEU_FONCE),
        ('TEXTCOLOR',     (0,0),(-1,0), BLANC),
        ('LINEBELOW',     (0,0),(-1,0), 1.5, BLEU_MED),
        # Padding global
        ('TOPPADDING',    (0,0),(-1,-1), 4),
        ('BOTTOMPADDING', (0,0),(-1,-1), 4),
        ('LEFTPADDING',   (0,0),(-1,-1), 4),
        ('RIGHTPADDING',  (0,0),(-1,-1), 4),
        # Alignements colonnes
        ('ALIGN',  (0,1), (0,-1), 'CENTER'),
        ('ALIGN',  (2,1), (3,-1), 'CENTER'),
        ('ALIGN',  (4,1), (5,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1),'MIDDLE'),
        # Grille légère
        ('LINEBELOW', (0,1),(-1,-1), 0.3, BLEU_LIGNE),
        ('LINEBEFORE',(1,0),(1,-1), 0.3, BLEU_LIGNE),
        ('LINEBEFORE',(4,0),(4,-1), 0.3, BLEU_LIGNE),
        ('LINEBEFORE',(5,0),(5,-1), 0.3, BLEU_LIGNE),
        # Bordure extérieure
        ('BOX', (0,0),(-1,-1), 1.2, BLEU_MED),
    ]

    item_n = 0; sec_n = 0
    for i, l in enumerate(lignes):
        tl   = l.get('type_ligne','item')
        ri   = len(tdata)
        mont = float(l.get('montant',0) or 0)

        if tl == 'section':
            sec_n += 1; item_n = 0
            tdata.append([
                Paragraph(str(sec_n), ST['tbl_sec']),
                Paragraph(l.get('designation','').upper(), ST['tbl_sec']),
                "","","",""
            ])
            tstyle += [
                ('BACKGROUND',(0,ri),(-1,ri), BLEU_MED),
                ('SPAN',(1,ri),(-1,ri)),
                ('LINEABOVE',(0,ri),(-1,ri), 0.8, BLEU_FONCE),
            ]
        elif tl == 'subtotal':
            tdata.append([
                "", Paragraph(l.get('designation','Sous-total'), ST['tbl_sub']),
                "","",
                Paragraph("Sous-total :", ST['tbl_sub_r']),
                Paragraph(fmt(mont), ST['tbl_sub_r']),
            ])
            tstyle += [
                ('BACKGROUND',(0,ri),(-1,ri), BLEU_TBL),
                ('LINEABOVE', (0,ri),(-1,ri), 1,   BLEU_MED),
                ('LINEBELOW', (0,ri),(-1,ri), 1,   BLEU_MED),
                ('SPAN',(4,ri),(4,ri)),
            ]
        elif tl == 'comment':
            tdata.append(["",
                Paragraph(f"↳  {l.get('designation','')}", ST['tbl_cmt']),
                "","","",""])
            tstyle += [
                ('SPAN',(1,ri),(-1,ri)),
                ('BACKGROUND',(0,ri),(-1,ri), BLANC),
            ]
        else:
            item_n += 1
            num = f"{sec_n}.{item_n}" if sec_n else str(item_n)
            qte = float(l.get('quantite',0) or 0)
            pu  = float(l.get('prix_unitaire',0) or 0)
            q_s = str(int(qte)) if qte == int(qte) else f"{qte:.2f}"
            bg  = BLANC if item_n % 2 else BLEU_TBL
            tdata.append([
                Paragraph(num, ST['tbl_item_c']),
                Paragraph(l.get('designation',''), ST['tbl_item']),
                Paragraph(l.get('unite',''), ST['tbl_item_c']),
                Paragraph(q_s, ST['tbl_item_c']),
                Paragraph(fmt(pu), ST['tbl_item_r']),
                Paragraph(fmt(mont), ST['tbl_item_r']),
            ])
            tstyle.append(('BACKGROUND',(0,ri),(-1,ri), bg))

    tbl = Table(tdata, colWidths=CW, repeatRows=1)
    tbl.setStyle(TableStyle(tstyle))
    story.append(tbl)
    story.append(Spacer(1,5*mm))

    # ══════════════════════════════════════════════════════════════════════
    # TOTAUX
    # ══════════════════════════════════════════════════════════════════════
    ht      = float(devis.get('montant_ht',0)  or 0)
    tva_t   = float(devis.get('tva_taux',18)   or 18)
    tva     = float(devis.get('montant_tva',0) or 0)
    ttc     = float(devis.get('montant_ttc',0) or 0)

    tot_data = [
        [Paragraph("Montant Hors Taxes (HT) :", ST['tot_lbl']),
         Paragraph(fmt_fcfa(ht), ST['tot_val'])],
        [Paragraph(f"TVA ({tva_t:.0f} %) :", ST['tot_lbl']),
         Paragraph(fmt_fcfa(tva), ST['tot_val'])],
        [Paragraph("MONTANT TOTAL TTC :", ST['ttc_lbl']),
         Paragraph(fmt_fcfa(ttc), ST['ttc_val'])],
    ]
    tot_t = Table(tot_data, colWidths=[5*cm, 4.2*cm])
    tot_t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,1), GRIS_FOND),
        ('BACKGROUND',(0,2),(-1,2), BLEU_MED),
        ('LINEABOVE',  (0,2),(-1,2), 2,   BLEU_FONCE),
        ('LINEBELOW',  (0,1),(-1,1), 0.5, BLEU_LIGNE),
        ('BOX',        (0,0),(-1,-1), 1.2, BLEU_MED),
        ('TOPPADDING', (0,0),(-1,-1), 6),
        ('BOTTOMPADDING',(0,0),(-1,-1), 6),
        ('LEFTPADDING', (0,0),(-1,-1), 8),
        ('RIGHTPADDING',(0,0),(-1,-1), 8),
        ('ALIGN', (1,0),(1,-1), 'RIGHT'),
        ('ROUNDEDCORNERS',[2]),
    ]))

    align_row = Table([[Spacer(W-9.5*cm,1), tot_t]],
                      colWidths=[W-9.5*cm, 9.5*cm])
    align_row.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),
                                   ('RIGHTPADDING',(0,0),(-1,-1),0)]))
    story.append(align_row)
    story.append(Spacer(1,5*mm))

    # ══════════════════════════════════════════════════════════════════════
    # CONDITIONS + SIGNATURES (corrigé : pas de débordement)
    # ══════════════════════════════════════════════════════════════════════
    cond  = devis.get('conditions_reglement','') or ent.get('conditions_def','') or ''
    notes = devis.get('notes','') or ''
    delai = devis.get('delai_execution','') or ''
    banque= ent.get('banque','') or ''
    rib   = ent.get('rib','') or ''

    left_col = []
    if cond:
        left_col.append(Paragraph("CONDITIONS DE RÈGLEMENT", ST['cond_hdr']))
        left_col.append(Paragraph(cond, ST['cond_val']))
        left_col.append(Spacer(1,2*mm))
    if delai:
        left_col.append(Paragraph("DÉLAI D'EXÉCUTION", ST['cond_hdr']))
        left_col.append(Paragraph(delai, ST['cond_val']))
        left_col.append(Spacer(1,2*mm))
    if banque or rib:
        left_col.append(Paragraph("COORDONNÉES BANCAIRES", ST['cond_hdr']))
        if banque: left_col.append(Paragraph(f"Banque : {banque}", ST['cond_val']))
        if rib:    left_col.append(Paragraph(f"RIB : {rib}",       ST['cond_val']))
        left_col.append(Spacer(1,2*mm))
    if notes:
        left_col.append(Paragraph("NOTES", ST['cond_hdr']))
        left_col.append(Paragraph(notes, ST['note']))

    # Signatures - largeurs fixes en cm (A4 width = 21cm, marges = 1.5cm chacune → largeur utile = 18cm)
    # On alloue 6.5 cm pour les conditions, 1 cm d'espace, 10.5 cm pour les signatures
    left_width_cm  = 6.5
    space_cm       = 0.8
    sig_width_cm   = 18 - left_width_cm - space_cm   # = 10.7 cm
    left_width_pt  = left_width_cm * cm
    space_pt       = space_cm * cm
    sig_width_pt   = sig_width_cm * cm

    sig_data = [
        [Paragraph("Signature & Cachet Entreprise", ST['sig_hdr']),
         Paragraph("Bon pour Accord — Client", ST['sig_hdr'])],
        [Spacer(1, 2.5*cm), Spacer(1, 2.5*cm)],
        [Paragraph("Lu et approuvé — Date :", ST['sig_txt']),
         Paragraph("Lu et approuvé — Date :", ST['sig_txt'])],
        [Paragraph("_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _", ST['sig_txt']),
         Paragraph("_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _", ST['sig_txt'])],
    ]
    sig_t = Table(sig_data, colWidths=[sig_width_pt/2, sig_width_pt/2])
    sig_t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,0), BLEU_MED),
        ('BACKGROUND',(1,0),(1,0), BLEU_CLAIR),
        ('BOX',(0,0),(0,-1), 1, BLEU_LIGNE),
        ('BOX',(1,0),(1,-1), 1, BLEU_LIGNE),
        ('LINEBETWEEN',(0,0),(1,-1), 4, BLANC),
        ('TOPPADDING',(0,0),(-1,-1), 5),
        ('BOTTOMPADDING',(0,0),(-1,-1), 5),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('LEFTPADDING',(0,0),(-1,-1), 2),
        ('RIGHTPADDING',(0,0),(-1,-1), 2),
    ]))

    # Table principale avec largeurs absolues
    bot_table = Table(
        [[left_col or Spacer(1,1), Spacer(space_pt,1), sig_t]],
        colWidths=[left_width_pt, space_pt, sig_width_pt]
    )
    bot_table.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),
        ('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),
    ]))
    story.append(KeepTogether(bot_table))

    doc.build(story, canvasmaker=PageCanvas)
    return output_path
