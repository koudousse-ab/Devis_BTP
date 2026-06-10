"""
app.py  –  DevisBTP v2.0 (version professionnelle sans émojis)
Interface graphique avec effets relief RAISED/SUNKEN/RIDGE/GROOVE
Logiciel de devis Génie Civil · BTP · Format Togo (FCFA)
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, sys
from pathlib import Path
from datetime import datetime

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except: pass

import db
from pdf_gen import generate_devis_pdf

# ── Palette sobre et professionnelle ────────────────────────────────────────
BG_APP  = "#F0F4F8"      # gris‑bleu très clair
BG_SIDE = "#1E3A5F"      # bleu foncé
BG_CARD = "#FFFFFF"
BG_IN   = "#FAFBFF"
BG_HDR  = "#2C5F8A"      # bleu moyen
BG_STR  = "#E9EDF2"
C_BLEU  = "#2C5F8A"
C_BLEU_F= "#1E3A5F"
C_BLEU_L= "#5A9BC7"
C_ORG   = "#D45A2B"      # orange sobre
C_VERT  = "#2E7D32"
C_ROUGE = "#C62828"
C_GRIS  = "#5D6D7E"
C_GRIS_L= "#95A5A6"
C_NOIR  = "#212121"
C_BLANC = "#FFFFFF"
C_HOVER = "#3A7CA5"

FT = ("Segoe UI", 16, "bold")
FH2 = ("Segoe UI", 12, "bold")
FH3 = ("Segoe UI", 10, "bold")
FB = ("Segoe UI", 9)
FP = ("Segoe UI", 8)

def fmt_fcfa(v):
    try: return f"{int(round(float(v))):,}".replace(",", " ") + " FCFA"
    except: return "0 FCFA"
def today_str(): return datetime.now().strftime("%Y-%m-%d")

# ── Widgets relief (inchangés, mais nettoyés) ──────────────────────────────
class RaisedCard(tk.Frame):
    def __init__(self, p, bg=BG_CARD, bd=3, **kw):
        super().__init__(p, bg=bg, relief="raised", bd=bd, **kw)

class RidgePanel(tk.Frame):
    def __init__(self, p, bg=BG_CARD, bd=2, **kw):
        super().__init__(p, bg=bg, relief="ridge", bd=bd, **kw)

class GrooveBox(tk.Frame):
    def __init__(self, p, bg=BG_APP, bd=2, **kw):
        super().__init__(p, bg=bg, relief="groove", bd=bd, **kw)

class SunkenEntry(tk.Entry):
    def __init__(self, p, textvariable=None, width=20, **kw):
        super().__init__(p, textvariable=textvariable, width=width,
                         bg=BG_IN, fg=C_NOIR, relief="sunken", bd=2,
                         font=FB, insertbackground=C_BLEU,
                         selectbackground=C_BLEU_L, **kw)

class RaisedBtn(tk.Button):
    def __init__(self, p, text="", command=None,
                 bg=C_BLEU, fg=C_BLANC, font=FB, padx=12, pady=5, **kw):
        super().__init__(p, text=text, command=command, bg=bg, fg=fg,
                         font=font, relief="raised", bd=3, cursor="hand2",
                         activebackground=C_HOVER, activeforeground=C_BLANC,
                         padx=padx, pady=pady, **kw)
        self.bind("<Enter>",          lambda _: self.config(relief="groove"))
        self.bind("<Leave>",          lambda _: self.config(relief="raised"))
        self.bind("<ButtonPress-1>",  lambda _: self.config(relief="sunken"))
        self.bind("<ButtonRelease-1>",lambda _: self.config(relief="raised"))

class NavBtn(tk.Frame):
    def __init__(self, p, text, command, **kw):
        super().__init__(p, bg=BG_SIDE, cursor="hand2", **kw)
        self.command = command; self._active = False
        self.inner = tk.Frame(self, bg=BG_SIDE, relief="flat", bd=0)
        self.inner.pack(fill="x", padx=6, pady=2)
        self.lbl = tk.Label(self.inner, text=text,
                            font=FB, fg=C_BLANC, bg=BG_SIDE,
                            anchor="w", padx=8, pady=10)
        self.lbl.pack(fill="x")
        for w in (self, self.inner, self.lbl):
            w.bind("<Enter>",          self._hon)
            w.bind("<Leave>",          self._hoff)
            w.bind("<Button-1>",       self._press)
            w.bind("<ButtonRelease-1>",self._release)
    def _hon(self, _):
        if not self._active:
            self.inner.configure(relief="raised", bd=2, bg=C_HOVER)
            self.lbl.configure(bg=C_HOVER)
    def _hoff(self, _):
        if not self._active:
            self.inner.configure(relief="flat", bd=0, bg=BG_SIDE)
            self.lbl.configure(bg=BG_SIDE)
    def _press(self, _):   self.inner.configure(relief="sunken", bd=2)
    def _release(self, _): self.command()
    def set_active(self, on):
        self._active = on
        if on:
            self.inner.configure(relief="ridge", bd=3, bg="#102A43")
            self.lbl.configure(bg="#102A43", fg="#F4D03F",
                               font=("Segoe UI", 9, "bold"))
        else:
            self.inner.configure(relief="flat", bd=0, bg=BG_SIDE)
            self.lbl.configure(bg=BG_SIDE, fg=C_BLANC, font=FB)

class ScrollFrame(tk.Frame):
    def __init__(self, p, bg=BG_APP, **kw):
        super().__init__(p, bg=bg, **kw)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win  = self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>",
            lambda e: self.canvas.itemconfig(self._win, width=e.width))
        self.canvas.bind_all("<MouseWheel>",
            lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))

def sec_bar(p, titre, bg=C_BLEU):
    """Barre de section avec relief raised (sans icône)"""
    f = tk.Frame(p, bg=bg, relief="raised", bd=2)
    f.pack(fill="x", padx=8, pady=(10,0))
    tk.Label(f, text=f"  {titre}", font=("Segoe UI", 9, "bold"),
             fg=C_BLANC, bg=bg, anchor="w", pady=6, padx=6).pack(fill="x")

def mk_tree(p, columns, headings, widths, height=12):
    st = ttk.Style(); sid = f"T{id(p)}.Treeview"
    st.configure(sid, background=BG_CARD, fieldbackground=BG_CARD,
                 rowheight=25, font=FB)
    st.configure(f"{sid}.Heading", background=BG_HDR, foreground=C_BLANC,
                 font=("Segoe UI", 8, "bold"), relief="raised")
    st.map(sid, background=[("selected",C_BLEU)],
           foreground=[("selected",C_BLANC)])
    tv = ttk.Treeview(p, columns=columns, show="headings",
                      style=sid, height=height, selectmode="browse")
    for col, hd, w in zip(columns, headings, widths):
        tv.heading(col, text=hd); tv.column(col, width=w, minwidth=30)
    tv.tag_configure("pair",    background=BG_STR)
    tv.tag_configure("impair",  background=BG_CARD)
    tv.tag_configure("section", background="#D4E6F1",
                     foreground=C_BLEU_F, font=("Segoe UI", 9, "bold"))
    tv.tag_configure("subtotal",background="#FCF3CF",
                     foreground=C_ORG, font=("Segoe UI", 8, "bold"))
    tv.tag_configure("comment", background="#F5F5F5",
                     foreground=C_GRIS, font=("Segoe UI", 8, "italic"))
    return tv

def fill_tree(tv, rows):
    tv.delete(*tv.get_children())
    for i, r in enumerate(rows):
        tv.insert("","end", values=r, tags=("pair" if i%2 else "impair",))

# ── Splash screen (sobre) ────────────────────────────────────────────────────
class Splash(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        W, H = 480, 300
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        body = tk.Frame(self, bg=C_BLEU_F, relief="raised", bd=6)
        body.pack(fill="both", expand=True)
        tk.Frame(body, bg=C_BLEU_F, height=22).pack()
        tk.Label(body, text="⚙", font=("Segoe UI", 36), bg=C_BLEU_F, fg="#F4D03F").pack()
        tk.Label(body, text="DevisBTP", font=("Segoe UI", 26, "bold"),
                 bg=C_BLEU_F, fg=C_BLANC).pack()
        tk.Label(body, text="Logiciel de Devis · Génie Civil · Togo",
                 font=("Segoe UI", 10), bg=C_BLEU_F, fg="#90CAF9").pack()
        tk.Label(body, text="Bâtiment  ·  Routes  ·  Ouvrages d'Art",
                 font=FP, bg=C_BLEU_F, fg="#64B5F6").pack(pady=(2,10))
        pf = tk.Frame(body, bg="#0A2D6E", relief="sunken", bd=3)
        pf.pack(fill="x", padx=40, pady=4)
        self.bar = tk.Frame(pf, bg="#F4D03F", height=10)
        self.bar.place(x=0, y=0, relheight=1, width=0)
        self.msg = tk.Label(body, text="Initialisation...",
                            font=FP, bg=C_BLEU_F, fg="#90CAF9")
        self.msg.pack()
        tk.Label(body, text="v2.0  ·  FCFA  ·  TVA 18%",
                 font=("Segoe UI", 7), bg=C_BLEU_F, fg="#455A64").pack(pady=(8,0))
        self.update(); self._pw = pf.winfo_width() or 400

    def progress(self, pct, msg=""):
        self.bar.place(width=int(self._pw * pct / 100))
        if msg: self.msg.configure(text=msg)
        self.update()

# ── Application principale ──────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self._run_splash()
        self.title("DevisBTP  –  Génie Civil · Togo")
        self.geometry("1350x820"); self.minsize(1050, 650)
        self.configure(bg=BG_APP)
        self._pages = {}
        self._build_ui(); self._setup_menu()
        self.show_page("dashboard")
        self.deiconify()

    def _run_splash(self):
        import time
        sp = Splash(self); sp.update(); time.sleep(0.2)
        for pct, msg in [(25,"Chargement base de données..."),
                         (55,"Préparation de l'interface..."),
                         (80,"Chargement du catalogue..."),
                         (100,"Bienvenue !")]:
            time.sleep(0.30); sp.progress(pct, msg)
        db.init_db(); time.sleep(0.2); sp.destroy()

    def _build_ui(self):
        self.sidebar = tk.Frame(self, bg=BG_SIDE, width=220,
                                relief="raised", bd=4)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        outer = tk.Frame(self, bg=BG_APP, relief="sunken", bd=2)
        outer.pack(side="left", fill="both", expand=True)
        self.content = tk.Frame(outer, bg=BG_APP)
        self.content.pack(fill="both", expand=True)
        self.statusbar = tk.Label(self, text="  Prêt",
                                  font=FP, fg=C_GRIS, bg="#CFD8DC",
                                  anchor="w", relief="groove", bd=2)
        self.statusbar.pack(side="bottom", fill="x")
        self._build_sidebar(); self._build_pages()

    def status(self, msg, color=C_GRIS):
        self.statusbar.configure(text=f"  {msg}", fg=color)
        self.after(4000, lambda: self.statusbar.configure(text="  Prêt", fg=C_GRIS))

    def _build_sidebar(self):
        sb = self.sidebar
        logo = tk.Frame(sb, bg="#102A43", relief="ridge", bd=3)
        logo.pack(fill="x", padx=6, pady=(6,4))
        tk.Label(logo, text="DevisBTP", font=("Segoe UI", 14, "bold"),
                 fg="#F4D03F", bg="#102A43", pady=10).pack()
        tk.Label(logo, text="Génie Civil · Togo",
                 font=FP, fg="#90CAF9", bg="#102A43").pack(pady=(0,8))
        tk.Frame(sb, bg="#3A7CA5", relief="ridge", bd=1,
                 height=2).pack(fill="x", padx=10, pady=4)

        nav_items = [
            ("Tableau de bord", "dashboard"),
            ("Gestion des Devis", "devis"),
            ("Clients", "clients"),
            ("Articles & Prix", "articles"),
            ("Mon Entreprise", "entreprise")
        ]
        self._nav = {}
        for label, page in nav_items:
            b = NavBtn(sb, label, command=lambda p=page: self.show_page(p))
            b.pack(fill="x")
            self._nav[page] = b

        tk.Frame(sb, bg="#3A7CA5", relief="ridge", bd=1,
                 height=2).pack(fill="x", padx=10, pady=8)
        RaisedBtn(sb, "Nouveau Devis", self._quick_new,
                  bg="#D45A2B", fg=C_BLANC, font=("Segoe UI", 9, "bold"),
                  padx=6, pady=8).pack(fill="x", padx=10, pady=2)
        tk.Label(sb, text="v2.0  ·  2025  ·  FCFA",
                 font=("Segoe UI", 7), fg="#5D6D7E",
                 bg=BG_SIDE).pack(side="bottom", pady=6)
        tk.Frame(sb, bg="#3A7CA5", relief="groove", bd=1,
                 height=1).pack(side="bottom", fill="x", padx=10, pady=2)

    def _quick_new(self):
        self.show_page("devis")
        DevisEditor(self.content, self, did=None,
                    on_save=lambda: self._pages['devis'].refresh())

    def _setup_menu(self):
        mb = tk.Menu(self); self.configure(menu=mb)
        mf = tk.Menu(mb, tearoff=0)
        mb.add_cascade(label="Fichier", menu=mf)
        mf.add_command(label="Nouveau Devis", command=self._quick_new, accelerator="Ctrl+N")
        mf.add_separator()
        mf.add_command(label="Entreprise", command=lambda: self.show_page("entreprise"))
        mf.add_separator()
        mf.add_command(label="Quitter", command=self.quit)
        mv = tk.Menu(mb, tearoff=0)
        mb.add_cascade(label="Affichage", menu=mv)
        for label, page in [("Tableau de bord","dashboard"),
                            ("Devis","devis"), ("Clients","clients"),
                            ("Articles","articles")]:
            mv.add_command(label=label, command=lambda p=page: self.show_page(p))
        mh = tk.Menu(mb, tearoff=0)
        mb.add_cascade(label="Aide", menu=mh)
        mh.add_command(label="À propos", command=self._about)
        mh.add_command(label="Guide",    command=self._guide)
        self.bind_all("<Control-n>", lambda _: self._quick_new())

    def _about(self):
        win = tk.Toplevel(self)
        win.title("À propos"); win.geometry("420x310")
        win.resizable(False,False); win.configure(bg=BG_APP); win.grab_set()
        body = RaisedCard(win, bg=C_BLEU_F, bd=4)
        body.pack(fill="both", expand=True, padx=15, pady=15)
        tk.Label(body, text="DevisBTP", font=("Segoe UI", 20, "bold"),
                 fg="#F4D03F", bg=C_BLEU_F).pack(pady=(20,5))
        tk.Label(body, text="Logiciel de Devis Génie Civil\nBâtiment · Routes · Ouvrages d'Art",
                 font=("Segoe UI", 10), fg=C_BLANC, bg=C_BLEU_F, justify="center").pack()
        tk.Frame(body, bg="#2C5F8A", height=2).pack(fill="x", padx=20, pady=10)
        for l in ["Version : 2.0","Devise : FCFA (Franc CFA)","Pays : Togo",
                  "TVA par défaut : 18 %","PDF : Blanc / Bleu A4 professionnel"]:
            tk.Label(body, text=l, font=FB, fg="#90CAF9", bg=C_BLEU_F).pack()
        tk.Frame(body, bg="#2C5F8A", height=2).pack(fill="x", padx=20, pady=10)
        RaisedBtn(body, "Fermer", win.destroy, bg="#2C5F8A").pack(pady=5)

    def _guide(self):
        win = tk.Toplevel(self)
        win.title("Guide d'utilisation"); win.geometry("620x530")
        win.configure(bg=BG_APP); win.grab_set()
        tk.Label(win, text="Guide d'utilisation", font=FH2,
                 fg=C_BLEU_F, bg=BG_APP).pack(pady=10)
        sf = ScrollFrame(win, bg=BG_APP)
        sf.pack(fill="both", expand=True, padx=10, pady=5)
        p = sf.inner
        for titre, texte in [
            ("1. Configurer votre entreprise",
             "Rendez-vous dans 'Mon Entreprise' : remplissez nom, adresse, RCCM, NIF, logo, banque.\n"
             "Ces informations apparaîtront sur tous vos devis PDF."),
            ("2. Ajouter vos clients",
             "Onglet 'Clients' : créez vos maîtres d'ouvrage.\n"
             "Types disponibles : Particulier, Entreprise, Administration, ONG."),
            ("3. Catalogue d'articles (66 pré-chargés)",
             "Onglet 'Articles & Prix' : Terrassement, Béton armé, Charpente, VRD, Électricité...\n"
             "Modifiez les prix unitaires ou ajoutez vos articles personnalisés."),
            ("4. Créer un devis",
             "Cliquez sur 'Nouveau Devis' ou Ctrl+N.\n"
             "Panneau gauche : client, chantier, dates, TVA, conditions.\n"
             "Panneau droit : sections + prestations (depuis catalogue ou manuelles).\n"
             "HT, TVA 18% et TTC calculés automatiquement."),
            ("5. Générer le PDF",
             "Bouton 'PDF' dans l'éditeur ou la liste.\n"
             "Format A4 professionnel, thème blanc/bleu, numéroté.\n"
             "Sauvegardé dans ~/DevisBTP/PDF/ — s'ouvre automatiquement."),
            ("6. Suivre les statuts",
             "Brouillon → Envoyé → Accepté / Refusé → Facturé\n"
             "Bouton 'Changer statut' dans la liste ou via l'éditeur.\n"
             "Tableau de bord : statistiques en temps réel."),
            ("7. Astuces rapides",
             "Double-clic sur un devis/client = ouverture directe.\n"
             "Dupliquer pour réutiliser un devis existant.\n"
             "Notes internes = n'apparaissent PAS sur le PDF.\n"
             "Ctrl+N = nouveau devis depuis n'importe où."),
        ]:
            bloc = RidgePanel(p, bg=BG_CARD, bd=2)
            bloc.pack(fill="x", padx=5, pady=4)
            tk.Label(bloc, text=titre, font=FH3, fg=C_BLEU_F,
                     bg=BG_CARD, anchor="w", padx=10, pady=5).pack(fill="x")
            tk.Frame(bloc, bg="#BBDEFB", height=1).pack(fill="x", padx=8)
            tk.Label(bloc, text=texte, font=FB, fg=C_NOIR,
                     bg=BG_CARD, anchor="w", justify="left",
                     padx=14, pady=7).pack(fill="x")
        RaisedBtn(win, "Fermer", win.destroy, bg=C_BLEU).pack(pady=8)

    def _build_pages(self):
        for Cls, key in [(DashboardPage,"dashboard"),(DevisPage,"devis"),
                         (ClientsPage,"clients"),(ArticlesPage,"articles"),
                         (EntreprisePage,"entreprise")]:
            pg = Cls(self.content, self)
            pg.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._pages[key] = pg

    def show_page(self, key):
        for k, b in self._nav.items(): b.set_active(k == key)
        self._pages[key].tkraise()
        if hasattr(self._pages[key], "refresh"): self._pages[key].refresh()
        self.status(f"Page : {key.capitalize()}")

# ═══════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═══════════════════════════════════════════════════════════════════
class DashboardPage(tk.Frame):
    def __init__(self, p, app):
        super().__init__(p, bg=BG_APP); self.app = app; self._build()
    def _build(self):
        hdr = tk.Frame(self, bg=C_BLEU_F, relief="raised", bd=3)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Tableau de Bord", font=("Segoe UI", 13, "bold"),
                 fg=C_BLANC, bg=C_BLEU_F, anchor="w", pady=10, padx=10).pack(side="left")
        self.lbl_date = tk.Label(hdr, text=datetime.now().strftime("%A %d %B %Y"),
                                  font=FB, fg="#90CAF9", bg=C_BLEU_F)
        self.lbl_date.pack(side="right", padx=15)
        self.cards_f = tk.Frame(self, bg=BG_APP); self.cards_f.pack(fill="x", padx=15, pady=12)
        sec_bar(self, "Derniers devis créés")
        tf = RidgePanel(self, bg=BG_CARD, bd=3)
        tf.pack(fill="both", expand=True, padx=15, pady=(4,6))
        self.tree = mk_tree(tf,
            ("num","date","client","chantier","ttc","statut"),
            ("N° Devis","Date","Client","Chantier / Objet","Montant TTC","Statut"),
            [110,88,180,230,145,90], height=10)
        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", self._open)
        row = tk.Frame(self, bg=BG_APP); row.pack(fill="x", padx=15, pady=(0,8))
        RaisedBtn(row, "Nouveau Devis", lambda: self.app.show_page("devis"),
                  bg=C_VERT).pack(side="left", padx=3)
        RaisedBtn(row, "Tous les Devis", lambda: self.app.show_page("devis"),
                  bg=C_BLEU).pack(side="left", padx=3)

    def _stat_card(self, p, val, titre, couleur, sub=""):
        c = RaisedCard(p, bg=BG_CARD, bd=4)
        c.pack(side="left", padx=6, pady=4, ipadx=8, ipady=6)
        tk.Label(c, text=val, font=("Segoe UI", 14, "bold"), fg=couleur, bg=BG_CARD).pack()
        tk.Label(c, text=titre, font=FP, fg=C_GRIS, bg=BG_CARD).pack()
        if sub: tk.Label(c, text=sub, font=("Segoe UI", 7), fg=C_GRIS_L, bg=BG_CARD).pack()

    def refresh(self):
        for w in self.cards_f.winfo_children(): w.destroy()
        s = db.get_stats()
        yr = datetime.now().year
        # Les valeurs sont des nombres, on utilise des libellés explicites
        items = [
            (str(s['total_devis']),     "Total Devis",    C_BLEU,   "Tous statuts"),
            (str(s['devis_mois']),      "Ce mois",        C_ORG,    f"{datetime.now().month}/{yr}"),
            (str(s['devis_acceptes']),  "Acceptés",       C_VERT,   ""),
            (str(s['devis_en_attente']),"En attente",     C_ORG,    "Brouillon+Envoyé"),
            (str(s['devis_refuses']),   "Refusés",        C_ROUGE,  ""),
            (str(s['nb_clients']),      "Clients",        C_BLEU_F, ""),
            (fmt_fcfa(s['ca_annee']).replace(" FCFA",""), f"CA {yr}", C_VERT, "TTC acceptés"),
        ]
        for val, titre, col, sub in items:
            self._stat_card(self.cards_f, val, titre, col, sub)
        rows = [(r['numero'], r['date_creation'], r.get('client_nom','—'),
                 r.get('chantier','')[:35], fmt_fcfa(r['montant_ttc']), r['statut'])
                for r in s['recents']]
        fill_tree(self.tree, rows)

    def _open(self, _):
        sel = self.tree.selection()
        if not sel: return
        num = self.tree.item(sel[0])['values'][0]
        for d in db.get_devis_list():
            if d['numero'] == num:
                DevisEditor(self, self.app, did=d['id'], on_save=self.refresh); break

# ═══════════════════════════════════════════════════════════════════
#  PAGE DEVIS
# ═══════════════════════════════════════════════════════════════════
class DevisPage(tk.Frame):
    def __init__(self, p, app):
        super().__init__(p, bg=BG_APP); self.app = app; self._ids = []; self._build()
    def _build(self):
        hdr = tk.Frame(self, bg=C_BLEU_F, relief="raised", bd=3); hdr.pack(fill="x")
        tk.Label(hdr, text="Gestion des Devis", font=("Segoe UI", 13, "bold"),
                 fg=C_BLANC, bg=C_BLEU_F, anchor="w", pady=10, padx=10).pack(side="left")
        RaisedBtn(hdr, "Nouveau Devis", self._new, bg=C_VERT, font=FH3, pady=4
                  ).pack(side="right", padx=10, pady=7)
        filt = GrooveBox(self, bg=BG_CARD, bd=3); filt.pack(fill="x", padx=12, pady=8)
        tk.Label(filt, text="Recherche :", font=FB, fg=C_GRIS, bg=BG_CARD
                 ).pack(side="left", pady=8)
        self.v_s = tk.StringVar()
        e = SunkenEntry(filt, textvariable=self.v_s, width=26); e.pack(side="left", padx=6)
        e.bind("<Return>", lambda _: self.refresh())
        tk.Label(filt, text="Statut :", font=FB, fg=C_GRIS, bg=BG_CARD
                 ).pack(side="left", padx=(10,4))
        self.v_st = tk.StringVar(value="Tous")
        ttk.Combobox(filt, values=["Tous","Brouillon","Envoyé","Accepté","Refusé","Facturé"],
                     textvariable=self.v_st, width=12, state="readonly", font=FB
                     ).pack(side="left")
        RaisedBtn(filt, "Filtrer", self.refresh, bg=C_BLEU, pady=3, padx=8
                  ).pack(side="left", padx=8)
        RaisedBtn(filt, "Réinitialiser", self._reset, bg=C_GRIS, pady=3
                  ).pack(side="left")
        tf = RidgePanel(self, bg=BG_CARD, bd=3); tf.pack(fill="both", expand=True, padx=12)
        self.tree = mk_tree(tf,
            ("num","date","client","chantier","ht","ttc","statut"),
            ("N° Devis","Date","Client","Chantier / Objet","HT","TTC","Statut"),
            [110,88,160,200,128,138,88])
        sb = ttk.Scrollbar(tf, command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda _: self._detail())
        act = GrooveBox(self, bg=BG_APP, bd=2); act.pack(fill="x", padx=12, pady=8)
        tk.Label(act, text="Actions :", font=FP, fg=C_GRIS, bg=BG_APP
                 ).pack(side="left", padx=5)
        for txt, cmd, col in [("Modifier",self._edit,C_BLEU),
                               ("PDF",self._pdf,C_ORG),
                               ("Changer Statut",self._statut,C_BLEU_L),
                               ("Dupliquer",self._dup,C_GRIS),
                               ("Supprimer",self._del,C_ROUGE)]:
            RaisedBtn(act, txt, cmd, bg=col, pady=3, font=FP
                      ).pack(side="left", padx=3, pady=6)

    def refresh(self):
        rows = db.get_devis_list(self.v_s.get(), self.v_st.get())
        self._ids = [r['id'] for r in rows]
        fill_tree(self.tree, [(r['numero'],r['date_creation'],
                               r.get('client_nom','')[:22], r.get('chantier','')[:28],
                               fmt_fcfa(r['montant_ht']), fmt_fcfa(r['montant_ttc']),
                               r['statut']) for r in rows])
    def _reset(self): self.v_s.set(""); self.v_st.set("Tous"); self.refresh()
    def _sel(self):
        sel = self.tree.selection()
        if not sel: messagebox.showinfo("Information", "Veuillez sélectionner un devis."); return None
        return self._ids[self.tree.index(sel[0])]
    def _new(self): DevisEditor(self, self.app, did=None, on_save=self.refresh)
    def _edit(self):
        did = self._sel()
        if did: DevisEditor(self, self.app, did=did, on_save=self.refresh)
    def _pdf(self):
        did = self._sel()
        if not did: return
        devis, lignes = db.get_devis(did); ent = db.get_entreprise()
        out = str(Path(db.APP_DIR)/"PDF"/f"{devis['numero']}.pdf")
        Path(db.APP_DIR/"PDF").mkdir(exist_ok=True)
        try:
            generate_devis_pdf(devis, lignes, ent, out)
            self.app.status(f"PDF généré : {devis['numero']}", C_VERT)
            if sys.platform=="win32": os.startfile(out)
            else: os.system(f'xdg-open "{out}" &')
        except Exception as ex: messagebox.showerror("Erreur PDF", str(ex))
    def _statut(self):
        did = self._sel()
        if not did: return
        devis, lignes = db.get_devis(did)
        if not devis: return
        win = tk.Toplevel(self); win.title("Changer le statut")
        win.geometry("300x260"); win.resizable(False,False)
        win.configure(bg=BG_APP); win.grab_set()
        tk.Label(win, text=f"Devis  {devis['numero']}", font=FH3,
                 fg=C_BLEU_F, bg=BG_APP).pack(pady=(15,5))
        tk.Label(win, text="Nouveau statut :", font=FB, fg=C_GRIS, bg=BG_APP).pack()
        v = tk.StringVar(value=devis['statut'])
        for s, bg in [("Brouillon","#FFF9C4"),("Envoyé","#E3F2FD"),
                      ("Accepté","#E8F5E9"),("Refusé","#FFEBEE"),("Facturé","#F3E5F5")]:
            f = tk.Frame(win, bg=bg, relief="ridge", bd=1)
            f.pack(fill="x", padx=20, pady=2)
            tk.Radiobutton(f, text=f"  {s}", variable=v, value=s,
                           font=FB, bg=bg, fg=C_NOIR).pack(anchor="w", padx=5, pady=3)
        def apply():
            devis['statut'] = v.get(); db.save_devis(devis, lignes)
            self.refresh(); win.destroy()
        RaisedBtn(win, "Appliquer", apply, bg=C_VERT).pack(pady=10)
    def _dup(self):
        did = self._sel()
        if not did: return
        db.duplicate_devis(did); self.refresh()
        self.app.status("Devis dupliqué avec succès.", C_VERT)
    def _del(self):
        did = self._sel()
        if not did: return
        d, _ = db.get_devis(did)
        if messagebox.askyesno("Confirmation",
                               f"Supprimer définitivement le devis {d['numero']} ?"):
            db.delete_devis(did); self.refresh()
            self.app.status("Devis supprimé.", C_ROUGE)

# ═══════════════════════════════════════════════════════════════════
#  ÉDITEUR DEVIS (version sans émojis)
# ═══════════════════════════════════════════════════════════════════
class DevisEditor(tk.Toplevel):
    def __init__(self, p, app, did=None, on_save=None):
        super().__init__(p)
        self.app = app; self.did = did; self.on_save = on_save
        self.lignes = []; self.ent = db.get_entreprise()
        self.v_cid = tk.IntVar(value=0)
        self.v_cnom = tk.StringVar(value="— Aucun client sélectionné —")
        self._vars = {}
        self.title("Nouveau Devis" if not did else "Modifier Devis")
        self.geometry("1350x850"); self.minsize(1100,700)
        self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        self._build()
        if did: self._load(did)
        else:   self._defaults()

    def _V(self, name, default=""):
        v = tk.StringVar(value=str(default)); self._vars[name] = v; return v

    def _defaults(self):
        self._vars['numero'].set(db.next_devis_numero())
        self._vars['date_creation'].set(today_str())
        self._vars['statut'].set("Brouillon")
        self._vars['tva_taux'].set(str(self.ent.get('tva_taux',18)))
        self._vars['delai_execution'].set(self.ent.get('delai_def','') or "")
        self.txt_cond.delete("1.0","end")
        self.txt_cond.insert("1.0", self.ent.get('conditions_def','') or "")

    def _build(self):
        top = tk.Frame(self, bg=C_BLEU_F, relief="raised", bd=3); top.pack(fill="x")
        tk.Label(top, text="Éditeur de Devis", font=("Segoe UI", 12, "bold"),
                 fg=C_BLANC, bg=C_BLEU_F, pady=9, padx=10).pack(side="left")
        RaisedBtn(top, "Générer PDF", self._pdf,    bg=C_ORG,  pady=3).pack(side="right", padx=5, pady=6)
        RaisedBtn(top, "Enregistrer", self._save,   bg=C_VERT, font=("Segoe UI", 10, "bold"), pady=3).pack(side="right", padx=5, pady=6)
        RaisedBtn(top, "Fermer",       self.destroy, bg="#455A64", pady=3).pack(side="right", padx=5, pady=6)
        paned = tk.PanedWindow(self, orient="horizontal", bg="#B0BEC5",
                               sashwidth=5, sashrelief="raised", bd=0)
        paned.pack(fill="both", expand=True)
        lf = tk.Frame(paned, bg=BG_APP); rf = tk.Frame(paned, bg=BG_APP)
        paned.add(lf, minsize=360, width=420); paned.add(rf, minsize=600)
        self._build_left(lf); self._build_right(rf)

    def _build_left(self, p):
        tk.Label(p, text="Informations", font=("Segoe UI", 9, "bold"),
                 fg=C_BLANC, bg=C_BLEU, relief="raised", bd=2,
                 anchor="w", padx=10, pady=7).pack(fill="x")
        sf = ScrollFrame(p, bg=BG_APP); sf.pack(fill="both", expand=True)
        q = sf.inner

        def fld(card, label, varname, default="", hint="", kind="entry", vals=None):
            tk.Label(card, text=label, font=FP, fg=C_GRIS, bg=BG_CARD, anchor="w"
                     ).pack(fill="x", padx=10, pady=(6,1))
            v = self._V(varname, default)
            if kind=="combo":
                w = ttk.Combobox(card, textvariable=v, values=vals or [],
                                 font=FB, state="readonly")
            else:
                w = SunkenEntry(card, textvariable=v)
            w.pack(fill="x", padx=10, pady=(0, 1 if hint else 3))
            if hint:
                tk.Label(card, text=hint, font=("Segoe UI", 7),
                         fg="#BDBDBD", bg=BG_CARD, anchor="w"
                         ).pack(fill="x", padx=10, pady=(0,4))

        # Référence
        sec_bar(q, "Référence du devis")
        c = RidgePanel(q, bg=BG_CARD, bd=2); c.pack(fill="x", padx=8)
        fld(c,"Numéro du devis","numero",  hint="Généré automatiquement")
        fld(c,"Date de création","date_creation", hint="AAAA-MM-JJ")
        fld(c,"Date de validité","date_validite", hint="Exemple : 2025-03-15")
        fld(c,"Statut","statut","Brouillon", kind="combo",
            vals=["Brouillon","Envoyé","Accepté","Refusé","Facturé"])
        tk.Frame(c, bg=BG_CARD, height=4).pack()

        # Client
        sec_bar(q, "Client / Maître d'ouvrage", bg=C_ORG)
        c2 = RidgePanel(q, bg=BG_CARD, bd=2); c2.pack(fill="x", padx=8)
        tk.Label(c2, text="Client sélectionné", font=FP, fg=C_GRIS,
                 bg=BG_CARD, anchor="w").pack(fill="x", padx=10, pady=(8,2))
        tk.Label(c2, textvariable=self.v_cnom,
                 font=("Segoe UI", 9, "bold"), fg=C_BLEU,
                 bg=BG_STR, relief="sunken", bd=2,
                 anchor="w", padx=8, pady=7).pack(fill="x", padx=10, pady=(0,6))
        bf = tk.Frame(c2, bg=BG_CARD); bf.pack(fill="x", padx=10, pady=(0,10))
        RaisedBtn(bf,"Choisir client", self._pick_client, bg=C_BLEU, pady=3, font=FP
                  ).pack(side="left", padx=(0,4))
        RaisedBtn(bf,"Nouveau client", self._new_client, bg=C_VERT, pady=3, font=FP
                  ).pack(side="left")

        # Chantier
        sec_bar(q, "Chantier et localisation")
        c3 = RidgePanel(q, bg=BG_CARD, bd=2); c3.pack(fill="x", padx=8)
        fld(c3,"Intitulé du chantier","chantier",
            hint="Exemple : Construction Villa R+1 – Adidogomé")
        fld(c3,"Localisation","localisation",
            hint="Exemple : Lomé, Tokoin, Lot 45")
        tk.Label(c3, text="Description des travaux", font=FP, fg=C_GRIS,
                 bg=BG_CARD, anchor="w").pack(fill="x", padx=10, pady=(6,2))
        self.txt_desc = tk.Text(c3, height=4, font=FB, bg=BG_IN, fg=C_NOIR,
                                relief="sunken", bd=2, wrap="word", padx=5, pady=4)
        self.txt_desc.pack(fill="x", padx=10, pady=(0,8))

        # Conditions
        sec_bar(q, "Conditions financières", bg="#1B5E20")
        c4 = RidgePanel(q, bg=BG_CARD, bd=2); c4.pack(fill="x", padx=8)
        fld(c4,"Taux TVA (%)","tva_taux","18.0", hint="Togo : 18 %")
        fld(c4,"Délai d'exécution","delai_execution",
            hint="Exemple : 6 mois, 90 jours...")
        tk.Label(c4, text="Conditions de règlement", font=FP, fg=C_GRIS,
                 bg=BG_CARD, anchor="w").pack(fill="x", padx=10, pady=(6,2))
        self.txt_cond = tk.Text(c4, height=3, font=FB, bg=BG_IN, fg=C_NOIR,
                                relief="sunken", bd=2, wrap="word", padx=5, pady=4)
        self.txt_cond.pack(fill="x", padx=10, pady=(0,4))
        tk.Label(c4, text="Notes internes (non imprimées)", font=FP, fg=C_GRIS,
                 bg=BG_CARD, anchor="w").pack(fill="x", padx=10, pady=(6,2))
        self.txt_notes = tk.Text(c4, height=3, font=FB, bg=BG_IN, fg=C_NOIR,
                                  relief="sunken", bd=2, wrap="word", padx=5, pady=4)
        self.txt_notes.pack(fill="x", padx=10, pady=(0,10))
        tk.Frame(q, bg=BG_APP, height=10).pack()

    def _build_right(self, p):
        tk.Label(p, text="Détail des Prestations", font=("Segoe UI", 9, "bold"),
                 fg=C_BLANC, bg=C_ORG, relief="raised", bd=2,
                 anchor="w", padx=10, pady=7).pack(fill="x")
        tb = GrooveBox(p, bg=BG_CARD, bd=3); tb.pack(fill="x")
        r1 = tk.Frame(tb, bg=BG_CARD); r1.pack(fill="x", padx=8, pady=(8,3))
        tk.Label(r1, text="Ajouter :", font=FP, fg=C_GRIS, bg=BG_CARD
                 ).pack(side="left", padx=(0,6))
        for txt, tl, col in [("Prestation","item",C_VERT),
                             ("Section","section",C_BLEU),
                             ("Sous-total","subtotal",C_ORG),
                             ("Commentaire","comment",C_GRIS)]:
            RaisedBtn(r1, txt, lambda t=tl: self._add(t),
                      bg=col, font=FP, pady=3, padx=8).pack(side="left", padx=3)
        RaisedBtn(r1, "Catalogue", self._catalog, bg=C_BLEU_F,
                  font=("Segoe UI", 9, "bold"), pady=3).pack(side="left", padx=(15,3))
        r2 = tk.Frame(tb, bg=BG_CARD); r2.pack(fill="x", padx=8, pady=(0,8))
        tk.Label(r2, text="Ligne :", font=FP, fg=C_GRIS, bg=BG_CARD
                 ).pack(side="left", padx=(0,6))
        for txt, cmd, col in [("Modifier",self._edit_ligne,C_BLEU),
                               ("Monter",lambda: self._move(-1),C_GRIS),
                               ("Descendre",lambda: self._move(1),C_GRIS),
                               ("Supprimer",self._del_ligne,C_ROUGE)]:
            RaisedBtn(r2, txt, cmd, bg=col, font=FP, pady=3, padx=8
                      ).pack(side="left", padx=3)
        tk.Label(tb, text="Astuce : double-clic pour modifier — flèches pour réordonner",
                 font=("Segoe UI", 7), fg="#90A4AE", bg=BG_CARD
                 ).pack(fill="x", padx=10, pady=(0,6))
        tf = RidgePanel(p, bg=BG_CARD, bd=3); tf.pack(fill="both", expand=True)
        self.tv = mk_tree(tf,
            ("num","desig","unite","qte","pu","mont"),
            ("N°","Désignation des Travaux","Unité","Quantité","Prix U. (FCFA)","Montant (FCFA)"),
            [40,355,65,72,132,132])
        self.tv.column("pu",   anchor="e"); self.tv.column("mont",  anchor="e")
        self.tv.column("num",  anchor="center"); self.tv.column("unite", anchor="center")
        self.tv.column("qte",  anchor="center")
        sb = ttk.Scrollbar(tf, command=self.tv.yview)
        self.tv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); self.tv.pack(side="left", fill="both", expand=True)
        self.tv.bind("<Double-1>", lambda _: self._edit_ligne())
        tot = RaisedCard(p, bg="#E8EAF6", bd=4); tot.pack(fill="x")
        tk.Label(tot, text="Montants : Quantité × Prix Unitaire",
                 font=("Segoe UI", 7), fg=C_GRIS, bg="#E8EAF6"
                 ).pack(side="left", padx=10)
        tr = tk.Frame(tot, bg="#E8EAF6"); tr.pack(side="right")
        for lbl, attr, bg, fg, bold in [
            ("Montant HT","lbl_ht","#E8EAF6",C_NOIR,False),
            ("TVA","lbl_tva","#E8EAF6",C_GRIS,False),
            ("TOTAL TTC","lbl_ttc",C_BLEU_F,C_BLANC,True)]:
            f = tk.Frame(tr, bg=bg, relief="groove" if bold else "flat",
                         bd=2 if bold else 0, padx=14, pady=8)
            f.pack(side="left")
            tk.Label(f, text=lbl, font=("Segoe UI", 7, "bold") if bold else FP,
                     fg="white" if bold else C_GRIS, bg=bg).pack()
            v = tk.Label(f, text="0 FCFA",
                         font=("Segoe UI", 10, "bold") if bold else FB,
                         fg="white" if bold else C_NOIR, bg=bg)
            v.pack(); setattr(self, attr, v)
            if not bold:
                tk.Frame(tr, bg="#9FA8DA", width=1).pack(side="left", fill="y")

    def _load(self, did):
        d, lignes = db.get_devis(did)
        if not d: return
        for k, v in self._vars.items():
            val = d.get(k)
            if val is not None: v.set(str(val))
        if d.get('client_id'):
            self.v_cid.set(d['client_id']); self.v_cnom.set(d.get('client_nom',''))
        self.txt_desc.delete("1.0","end"); self.txt_desc.insert("1.0", d.get('description','') or "")
        self.txt_cond.delete("1.0","end"); self.txt_cond.insert("1.0", d.get('conditions_reglement','') or "")
        self.txt_notes.delete("1.0","end"); self.txt_notes.insert("1.0", d.get('notes','') or "")
        self.lignes = lignes; self._refresh()

    def _refresh(self):
        self.tv.delete(*self.tv.get_children())
        sn = 0; it = 0
        for i, l in enumerate(self.lignes):
            tl = l.get('type_ligne','item'); mo = float(l.get('montant',0) or 0)
            if tl=='section':
                sn+=1; it=0
                self.tv.insert("","end",iid=str(i),tags=("section",),
                    values=(str(sn),l.get('designation','').upper(),"","","",""))
            elif tl=='subtotal':
                self.tv.insert("","end",iid=str(i),tags=("subtotal",),
                    values=("Σ",l.get('designation','Sous-total'),"","","",
                            f"{int(mo):,}".replace(',',' ')))
            elif tl=='comment':
                self.tv.insert("","end",iid=str(i),tags=("comment",),
                    values=("💬",l.get('designation',''),"","","",""))
            else:
                it+=1; num=f"{sn}.{it}" if sn else str(it)
                qte=float(l.get('quantite',0) or 0); pu=float(l.get('prix_unitaire',0) or 0)
                tag="pair" if it%2 else "impair"
                qs=str(int(qte)) if qte==int(qte) else f"{qte:.2f}"
                self.tv.insert("","end",iid=str(i),tags=(tag,),
                    values=(num,l.get('designation',''),l.get('unite',''),qs,
                            f"{int(pu):,}".replace(',',' '),
                            f"{int(mo):,}".replace(',',' ')))
        self._recalc()

    def _recalc(self):
        ht = sum(float(l.get('montant',0) or 0)
                 for l in self.lignes if l.get('type_ligne','item')=='item')
        try: tva_t = float(self._vars['tva_taux'].get() or 18)
        except: tva_t = 18
        tva = ht*tva_t/100; ttc = ht+tva
        self.lbl_ht.configure(text=fmt_fcfa(ht))
        self.lbl_tva.configure(text=f"({tva_t:.0f}%)  "+fmt_fcfa(tva))
        self.lbl_ttc.configure(text=fmt_fcfa(ttc))

    def _sel(self):
        sel = self.tv.selection(); return int(sel[0]) if sel else None

    def _add(self, tl): LigneEditor(self, tl, None, self._on_ligne)
    def _edit_ligne(self):
        idx = self._sel()
        if idx is None: return
        LigneEditor(self, self.lignes[idx].get('type_ligne','item'),
                    self.lignes[idx], self._on_ligne, idx=idx)
    def _on_ligne(self, data, idx=None):
        if idx is None: self.lignes.append(data)
        else:           self.lignes[idx] = data
        self._refresh()
        try:
            t = len(self.lignes)-1 if idx is None else idx
            self.tv.selection_set(str(t)); self.tv.see(str(t))
        except: pass
    def _del_ligne(self):
        idx = self._sel()
        if idx is None: messagebox.showinfo("Information", "Veuillez sélectionner une ligne."); return
        self.lignes.pop(idx); self._refresh()
    def _move(self, d):
        idx = self._sel()
        if idx is None: return
        nw = idx+d
        if 0<=nw<len(self.lignes):
            self.lignes[idx],self.lignes[nw]=self.lignes[nw],self.lignes[idx]
            self._refresh()
            try: self.tv.selection_set(str(nw)); self.tv.see(str(nw))
            except: pass
    def _catalog(self):
        CatalogPicker(self, lambda arts: [
            self._on_ligne({'type_ligne':'item','designation':a['designation'],
                            'unite':a.get('unite','U'),'quantite':1,
                            'prix_unitaire':a.get('prix_unitaire',0),
                            'montant':a.get('prix_unitaire',0)})
            for a in arts])
    def _pick_client(self):
        ClientPicker(self, lambda c: (self.v_cid.set(c['id']), self.v_cnom.set(c['nom'])))
    def _new_client(self):
        ClientEditor(self, None, on_save=lambda c: (
            self.v_cid.set(c.get('id') or 0), self.v_cnom.set(c.get('nom',''))))

    def _save(self):
        num = self._vars.get('numero',tk.StringVar()).get().strip()
        if not num: messagebox.showwarning("Attention", "Le numéro de devis est obligatoire."); return
        try: tva_t = float(self._vars['tva_taux'].get() or 18)
        except: tva_t = 18
        ht  = sum(float(l.get('montant',0) or 0)
                  for l in self.lignes if l.get('type_ligne','item')=='item')
        tva = ht*tva_t/100; ttc = ht+tva
        data = {'id':self.did,'numero':num,
                'date_creation':self._vars.get('date_creation',tk.StringVar()).get() or today_str(),
                'date_validite':self._vars.get('date_validite',tk.StringVar()).get(),
                'client_id':self.v_cid.get() or None,
                'chantier':self._vars.get('chantier',tk.StringVar()).get(),
                'localisation':self._vars.get('localisation',tk.StringVar()).get(),
                'description':self.txt_desc.get("1.0","end-1c"),
                'statut':self._vars.get('statut',tk.StringVar(value='Brouillon')).get(),
                'tva_taux':tva_t,'montant_ht':ht,'montant_tva':tva,'montant_ttc':ttc,
                'delai_execution':self._vars.get('delai_execution',tk.StringVar()).get(),
                'conditions_reglement':self.txt_cond.get("1.0","end-1c"),
                'notes':self.txt_notes.get("1.0","end-1c")}
        self.did = db.save_devis(data, self.lignes)
        if self.on_save: self.on_save()
        orig = self.title(); self.title("Devis enregistré !")
        self.after(1800, lambda: self.title(orig))

    def _pdf(self):
        self._save()
        if not self.did: return
        devis, lignes = db.get_devis(self.did); ent = db.get_entreprise()
        out_dir = Path(db.APP_DIR)/"PDF"; out_dir.mkdir(exist_ok=True)
        out = str(out_dir/f"{devis['numero']}.pdf")
        try:
            generate_devis_pdf(devis, lignes, ent, out)
            if sys.platform=="win32": os.startfile(out)
            else: os.system(f'xdg-open "{out}" &')
        except Exception as ex: messagebox.showerror("Erreur PDF", str(ex))

# ═══════════════════════════════════════════════════════════════════
#  ÉDITEUR LIGNE
# ═══════════════════════════════════════════════════════════════════
class LigneEditor(tk.Toplevel):
    NOMS = {'item':'Prestation','section':'Section / Titre',
            'subtotal':'Sous-total','comment':'Commentaire'}
    def __init__(self, p, tl, data, cb, idx=None):
        super().__init__(p)
        self.cb=cb; self.idx=idx; self.tl=tl; self.data=data or {}
        self.title(f"Modifier : {self.NOMS.get(tl,tl)}")
        self.resizable(False,False); self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        self._build()
    def _build(self):
        cols={'item':C_VERT,'section':C_BLEU,'subtotal':C_ORG,'comment':C_GRIS}
        hdr = tk.Frame(self, bg=cols.get(self.tl,C_BLEU), relief="raised", bd=3)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"  {self.NOMS.get(self.tl,self.tl)}",
                 font=FH3, fg=C_BLANC, bg=cols.get(self.tl,C_BLEU),
                 anchor="w", pady=8, padx=8).pack(fill="x")
        body = RidgePanel(self, bg=BG_CARD, bd=3)
        body.pack(padx=15, pady=10, fill="x")
        def row(lbl, w):
            f=tk.Frame(body,bg=BG_CARD); f.pack(fill="x",padx=12,pady=5)
            tk.Label(f,text=lbl,font=FB,fg=C_GRIS,bg=BG_CARD,width=18,anchor="w").pack(side="left")
            w.pack(side="left",fill="x",expand=True)
        self.v_desig = tk.StringVar(value=self.data.get('designation',''))
        row("Désignation :", SunkenEntry(body, textvariable=self.v_desig, width=42))
        if self.tl=='item':
            self.v_unite = tk.StringVar(value=self.data.get('unite','U'))
            self.v_qte   = tk.StringVar(value=str(self.data.get('quantite',1)))
            self.v_pu    = tk.StringVar(value=str(self.data.get('prix_unitaire',0)))
            self.v_mont  = tk.StringVar(value=str(self.data.get('montant',0)))
            row("Unité :", ttk.Combobox(body, textvariable=self.v_unite,
                values=["U","ml","m²","m³","kg","t","h","j","forfait","lot"],
                width=12, font=FB, state="normal"))
            row("Quantité :",          SunkenEntry(body, textvariable=self.v_qte, width=16))
            row("Prix unitaire (FCFA):",SunkenEntry(body, textvariable=self.v_pu,  width=20))
            mf = tk.Frame(body, bg=BG_CARD); mf.pack(fill="x", padx=12, pady=5)
            tk.Label(mf, text="Montant calculé :", font=FB, fg=C_GRIS,
                     bg=BG_CARD, width=18, anchor="w").pack(side="left")
            tk.Label(mf, textvariable=self.v_mont,
                     font=("Segoe UI", 11, "bold"), fg=C_BLEU_F,
                     bg=BG_STR, relief="groove", bd=2, padx=10, pady=4
                     ).pack(side="left")
            self.v_qte.trace_add("write", lambda *_: self._calc())
            self.v_pu.trace_add("write",  lambda *_: self._calc())
        bot = tk.Frame(self, bg=BG_APP, relief="groove", bd=2)
        bot.pack(fill="x", padx=15, pady=(0,12))
        RaisedBtn(bot, "Valider", self._ok, bg=C_VERT,
                  font=("Segoe UI", 10, "bold")).pack(side="right", padx=8, pady=8)
        RaisedBtn(bot, "Annuler", self.destroy, bg=C_GRIS
                  ).pack(side="right", padx=4, pady=8)
    def _calc(self):
        try:
            q=float(self.v_qte.get() or 0); pu=float(self.v_pu.get() or 0)
            self.v_mont.set(f"{int(q*pu):,}".replace(',',' '))
        except: pass
    def _ok(self):
        data={'type_ligne':self.tl,'designation':self.v_desig.get()}
        if self.tl=='item':
            try: q=float(self.v_qte.get() or 0)
            except: q=0
            try: pu=float(self.v_pu.get() or 0)
            except: pu=0
            data.update({'unite':self.v_unite.get(),'quantite':q,
                         'prix_unitaire':pu,'montant':q*pu})
        self.cb(data, self.idx); self.destroy()

# ═══════════════════════════════════════════════════════════════════
#  CATALOGUE PICKER
# ═══════════════════════════════════════════════════════════════════
class CatalogPicker(tk.Toplevel):
    def __init__(self, p, cb):
        super().__init__(p); self.cb=cb; self._arts=[]
        self.title("Catalogue des Articles"); self.geometry("860x580")
        self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        self._build(); self._load()
    def _build(self):
        hdr=tk.Frame(self,bg=C_BLEU_F,relief="raised",bd=3); hdr.pack(fill="x")
        tk.Label(hdr,text="Choisir depuis le catalogue",font=FH2,
                 fg=C_BLANC,bg=C_BLEU_F,anchor="w",pady=10,padx=10).pack(side="left")
        filt=GrooveBox(self,bg=BG_CARD,bd=3); filt.pack(fill="x",padx=10,pady=8)
        tk.Label(filt,text="Recherche :",font=FB,fg=C_GRIS,bg=BG_CARD
                 ).pack(side="left",pady=8)
        self.v_s=tk.StringVar()
        e=SunkenEntry(filt,textvariable=self.v_s,width=25); e.pack(side="left",padx=6)
        e.bind("<Return>",lambda _:self._load())
        self.v_cat=tk.StringVar(value="Toutes")
        cats=["Toutes"]+db.get_categories_articles()
        ttk.Combobox(filt,values=cats,textvariable=self.v_cat,
                     width=24,font=FB,state="readonly").pack(side="left",padx=5)
        RaisedBtn(filt,"Rechercher",self._load,bg=C_BLEU,pady=3).pack(side="left",padx=5)
        tf=RidgePanel(self,bg=BG_CARD,bd=3); tf.pack(fill="both",expand=True,padx=10)
        self.tree=mk_tree(tf,("cat","desig","unite","pu"),
            ("Catégorie","Désignation","Unité","Prix Unitaire (FCFA)"),
            [150,370,65,150])
        sb=ttk.Scrollbar(tf,command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y"); self.tree.pack(side="left",fill="both",expand=True)
        bot=GrooveBox(self,bg=BG_APP,bd=2); bot.pack(fill="x",padx=10,pady=8)
        tk.Label(bot,text="Ctrl+clic : sélection multiple",
                 font=FP,fg=C_GRIS,bg=BG_APP).pack(side="left",padx=5)
        RaisedBtn(bot,"Ajouter la sélection",self._pick,bg=C_VERT,
                  font=("Segoe UI", 10, "bold")).pack(side="right",padx=8,pady=6)
        RaisedBtn(bot,"Fermer",self.destroy,bg=C_GRIS).pack(side="right",padx=4,pady=6)
    def _load(self,*_):
        self._arts=db.get_articles(self.v_s.get(),self.v_cat.get())
        fill_tree(self.tree,[(a['categorie'],a['designation'],
                              a['unite'],fmt_fcfa(a['prix_unitaire'])) for a in self._arts])
    def _pick(self):
        sels=self.tree.selection()
        if not sels: messagebox.showinfo("Information", "Veuillez sélectionner au moins un article."); return
        self.cb([self._arts[self.tree.index(s)] for s in sels]); self.destroy()

# ═══════════════════════════════════════════════════════════════════
#  CLIENT PICKER
# ═══════════════════════════════════════════════════════════════════
class ClientPicker(tk.Toplevel):
    def __init__(self,p,cb):
        super().__init__(p); self.cb=cb; self._cl=[]
        self.title("Choisir un client"); self.geometry("580x420")
        self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        self._build(); self._load()
    def _build(self):
        hdr=tk.Frame(self,bg=C_ORG,relief="raised",bd=3); hdr.pack(fill="x")
        tk.Label(hdr,text="Sélectionner un client",font=FH2,
                 fg=C_BLANC,bg=C_ORG,anchor="w",pady=10,padx=10).pack(side="left")
        filt=GrooveBox(self,bg=BG_CARD,bd=3); filt.pack(fill="x",padx=10,pady=8)
        self.v_s=tk.StringVar()
        e=SunkenEntry(filt,textvariable=self.v_s,width=30); e.pack(side="left",padx=(10,6),pady=8)
        e.bind("<Return>",lambda _:self._load())
        RaisedBtn(filt,"Rechercher",self._load,bg=C_BLEU,pady=3).pack(side="left")
        tf=RidgePanel(self,bg=BG_CARD,bd=3); tf.pack(fill="both",expand=True,padx=10)
        self.tree=mk_tree(tf,("nom","type","ville","tel"),
            ("Nom / Raison sociale","Type","Ville","Téléphone"),
            [215,110,115,125])
        sb=ttk.Scrollbar(tf,command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y"); self.tree.pack(side="left",fill="both",expand=True)
        self.tree.bind("<Double-1>",lambda _:self._pick())
        bot=GrooveBox(self,bg=BG_APP,bd=2); bot.pack(fill="x",padx=10,pady=8)
        RaisedBtn(bot,"Sélectionner",self._pick,bg=C_VERT,
                  font=("Segoe UI", 10, "bold")).pack(side="right",padx=8,pady=6)
        RaisedBtn(bot,"Fermer",self.destroy,bg=C_GRIS).pack(side="right",padx=4,pady=6)
    def _load(self,*_):
        self._cl=db.get_clients(self.v_s.get())
        fill_tree(self.tree,[(c['nom'],c.get('type_client',''),
                              c['ville'],c['telephone']) for c in self._cl])
    def _pick(self):
        sel=self.tree.selection()
        if not sel: messagebox.showinfo("Information", "Veuillez sélectionner un client."); return
        self.cb(self._cl[self.tree.index(sel[0])]); self.destroy()

# ═══════════════════════════════════════════════════════════════════
#  PAGE CLIENTS
# ═══════════════════════════════════════════════════════════════════
class ClientsPage(tk.Frame):
    def __init__(self, p, app):
        super().__init__(p, bg=BG_APP); self.app=app; self._cl=[]; self._build()
    def _build(self):
        hdr=tk.Frame(self,bg=C_ORG,relief="raised",bd=3); hdr.pack(fill="x")
        tk.Label(hdr,text="Clients / Maîtres d'Ouvrage",
                 font=("Segoe UI", 13, "bold"),fg=C_BLANC,bg=C_ORG,
                 anchor="w",pady=10,padx=10).pack(side="left")
        RaisedBtn(hdr,"Nouveau Client",self._new,bg=C_VERT,font=FH3,pady=4
                  ).pack(side="right",padx=10,pady=7)
        filt=GrooveBox(self,bg=BG_CARD,bd=3); filt.pack(fill="x",padx=12,pady=8)
        tk.Label(filt,text="Recherche :",font=FB,fg=C_GRIS,bg=BG_CARD
                 ).pack(side="left",pady=8)
        self.v_s=tk.StringVar()
        e=SunkenEntry(filt,textvariable=self.v_s,width=30); e.pack(side="left",padx=6)
        e.bind("<Return>",lambda _:self.refresh())
        RaisedBtn(filt,"Filtrer",self.refresh,bg=C_BLEU,pady=3,padx=8).pack(side="left",padx=8)
        RaisedBtn(filt,"Réinitialiser",lambda:(self.v_s.set(""),self.refresh()),
                  bg=C_GRIS,pady=3).pack(side="left")
        tf=RidgePanel(self,bg=BG_CARD,bd=3); tf.pack(fill="both",expand=True,padx=12)
        self.tree=mk_tree(tf,
            ("nom","type","adresse","ville","tel","email","nif"),
            ("Nom / Raison sociale","Type","Adresse","Ville","Téléphone","Email","NIF"),
            [195,95,185,100,120,170,105])
        sb=ttk.Scrollbar(tf,command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y"); self.tree.pack(side="left",fill="both",expand=True)
        self.tree.bind("<Double-1>",lambda _:self._detail_client())
        act=GrooveBox(self,bg=BG_APP,bd=2); act.pack(fill="x",padx=12,pady=8)
        tk.Label(act,text="Actions :",font=FP,fg=C_GRIS,bg=BG_APP).pack(side="left",padx=5)
        for txt,cmd,col in [("Modifier",self._edit,C_BLEU),
                             ("Supprimer",self._del,C_ROUGE)]:
            RaisedBtn(act,txt,cmd,bg=col,pady=3,font=FP).pack(side="left",padx=4,pady=6)
    def refresh(self):
        self._cl=db.get_clients(self.v_s.get())
        fill_tree(self.tree,[(c['nom'],c.get('type_client',''),
                              c.get('adresse','')[:25],c['ville'],
                              c['telephone'],c.get('email','')[:25],
                              c.get('nif','')) for c in self._cl])
    def _sel(self):
        sel=self.tree.selection()
        if not sel: messagebox.showinfo("Information", "Veuillez sélectionner un client."); return None
        return self._cl[self.tree.index(sel[0])]['id']
    def _new(self):  ClientEditor(self,None,on_save=lambda _:self.refresh())
    def _edit(self):
        cid=self._sel()
        if cid: ClientEditor(self,cid,on_save=lambda _:self.refresh())
    def _del(self):
        cid=self._sel()
        if not cid: return
        if db.count_devis_client(cid)>0:
            messagebox.showwarning("Impossible","Ce client possède des devis. Supprimez-les d'abord."); return
        if messagebox.askyesno("Confirmer","Supprimer définitivement ce client ?"):
            db.delete_client(cid); self.refresh()
            self.app.status("Client supprimé.", C_ROUGE)

# ═══════════════════════════════════════════════════════════════════
#  FORMULAIRE CLIENT
# ═══════════════════════════════════════════════════════════════════
class ClientEditor(tk.Toplevel):
    def __init__(self, p, cid, on_save=None):
        super().__init__(p)
        self.cid=cid; self.on_save=on_save; self._vars={}
        nouveau = not cid
        self._col = C_VERT if nouveau else C_ORG
        self.title("Nouveau Client" if nouveau else "Modifier Client")
        self.geometry("600x650"); self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        self._build()
        if cid:
            c=db.get_client(cid)
            for k,v in c.items():
                if k in self._vars: self._vars[k].set(str(v) if v else "")
            self._sel_type(c.get('type_client','Particulier'))

    def _V(self,name,default=""):
        v=tk.StringVar(value=str(default)); self._vars[name]=v; return v

    def _build(self):
        # Bandeau RAISED
        hdr=tk.Frame(self,bg=self._col,relief="raised",bd=3); hdr.pack(fill="x")
        ico="+" if not self.cid else "✏"
        txt="Ajouter un nouveau client" if not self.cid else "Modifier le client"
        tk.Label(hdr,text=f"  {ico}   {txt}",font=FH2,fg=C_BLANC,bg=self._col,
                 anchor="w",pady=12,padx=10).pack(side="left")

        sf=ScrollFrame(self,bg=BG_APP); sf.pack(fill="both",expand=True)
        p=sf.inner

        def sec(titre,color=C_BLEU): sec_bar(p, titre, bg=color)

        def card(cols=2):
            c=RidgePanel(p,bg=BG_CARD,bd=2); c.pack(fill="x",padx=8)
            for i in range(cols*2): c.columnconfigure(i,weight=1 if i%2==1 else 0)
            return c

        def fld(card,row,col,lbl,varname,default="",hint="",kind="entry",vals=None,full=False):
            span=4 if full else 1; lc=0 if full else col*2
            tk.Label(card,text=lbl,font=FP,fg=C_GRIS,bg=BG_CARD,anchor="w"
                     ).grid(row=row*3,column=lc,columnspan=span,
                            sticky="w",padx=(12,4),pady=(8,1))
            v=self._V(varname,default)
            if kind=="combo":
                w=ttk.Combobox(card,textvariable=v,values=vals or [],font=FB,state="readonly")
            else:
                w=SunkenEntry(card,textvariable=v)
            w.grid(row=row*3+1,column=lc,columnspan=span,
                   sticky="ew",padx=(12,12 if full else 6),pady=(0,1))
            if hint:
                tk.Label(card,text=hint,font=("Segoe UI",7),fg="#BDBDBD",
                         bg=BG_CARD,anchor="w").grid(row=row*3+2,column=lc,
                         columnspan=span,sticky="w",padx=12,pady=(0,4))

        # ── Section identité ────────────────────────────────────────
        sec("Identité",color=self._col)
        c1=card(1); c1.columnconfigure(1,weight=1)

        # Nom (toute la largeur)
        tk.Label(c1,text="Nom complet / Raison sociale  *(obligatoire)",
                 font=FP,fg=C_GRIS,bg=BG_CARD,anchor="w"
                 ).grid(row=0,column=0,columnspan=2,sticky="w",padx=12,pady=(10,1))
        vn=self._V('nom')
        self._e_nom=tk.Entry(c1,textvariable=vn,font=("Segoe UI",11,"bold"),bg=BG_IN,fg=C_BLEU_F,relief="sunken",bd=2,insertbackground=C_BLEU,selectbackground=C_BLEU_L)
        self._e_nom.configure(fg=C_BLEU_F)
        self._e_nom.grid(row=1,column=0,columnspan=2,sticky="ew",padx=12,pady=(0,2))
        tk.Label(c1,text="Exemple : M. KODJO AMEWOU   —   SARL CONSTRUCTION TOGO",
                 font=("Segoe UI",7),fg="#BDBDBD",bg=BG_CARD,anchor="w"
                 ).grid(row=2,column=0,columnspan=2,sticky="w",padx=12,pady=(0,6))

        # Type — boutons radio RAISED/SUNKEN
        tk.Label(c1,text="Type de client",font=FP,fg=C_GRIS,bg=BG_CARD,anchor="w"
                 ).grid(row=3,column=0,columnspan=2,sticky="w",padx=12,pady=(4,2))
        type_row=tk.Frame(c1,bg=BG_CARD)
        type_row.grid(row=4,column=0,columnspan=2,sticky="w",padx=12,pady=(0,6))
        self._v_type=self._V('type_client','Particulier')
        self._tbtns={}
        for t in ["Particulier","Entreprise","Administration","ONG"]:
            b=tk.Button(type_row,text=t,font=FP,
                        relief="raised",bd=2,padx=8,pady=5,cursor="hand2",
                        command=lambda x=t:self._sel_type(x))
            b.pack(side="left",padx=3); self._tbtns[t]=b
        self._sel_type('Particulier')

        fld(c1,3,0,"NIF (Identifiant Fiscal)",'nif',
            hint="Laisser vide pour les particuliers",full=True)
        tk.Frame(c1,bg=BG_CARD,height=4).grid(row=11,column=0)

        # ── Section adresse ─────────────────────────────────────────
        sec("Localisation / Adresse",color=C_ORG)
        c2=card(2); c2.columnconfigure(1,weight=2); c2.columnconfigure(3,weight=1)
        tk.Label(c2,text="Adresse complète (rue, BP, lot…)",
                 font=FP,fg=C_GRIS,bg=BG_CARD,anchor="w"
                 ).grid(row=0,column=0,columnspan=4,sticky="w",padx=12,pady=(10,1))
        SunkenEntry(c2,textvariable=self._V('adresse')).grid(
            row=1,column=0,columnspan=4,sticky="ew",padx=12,pady=(0,2))
        tk.Label(c2,text="Exemple : Rue des Cocotiers, Lot 12  —  BP 450",
                 font=("Segoe UI",7),fg="#BDBDBD",bg=BG_CARD,anchor="w"
                 ).grid(row=2,column=0,columnspan=4,sticky="w",padx=12,pady=(0,6))

        for col_idx,lbl,varname,defval in [(0,"Quartier / Zone",'quartier',""),
                                            (1,"Ville",'ville',"Lomé")]:
            tk.Label(c2,text=lbl,font=FP,fg=C_GRIS,bg=BG_CARD,anchor="w"
                     ).grid(row=3,column=col_idx*2,columnspan=2,
                            sticky="w",padx=(12,4) if col_idx==0 else (4,4),pady=(4,1))
            SunkenEntry(c2,textvariable=self._V(varname,defval)).grid(
                row=4,column=col_idx*2,columnspan=2,
                sticky="ew",padx=(12,4) if col_idx==0 else (4,12),pady=(0,8))

        # ── Section contacts ────────────────────────────────────────
        sec("Contacts",color="#1B5E20")
        c3=card(2); c3.columnconfigure(1,weight=1); c3.columnconfigure(3,weight=1)
        for col_idx,lbl,varname,hint in [
            (0,"Numéro de téléphone",'telephone',"Exemple : +228 90 12 34 56"),
            (1,"Adresse e-mail",'email',"Exemple : nom@domaine.tg")]:
            px1=(12,4) if col_idx==0 else (4,4)
            px2=(12,4) if col_idx==0 else (4,12)
            tk.Label(c3,text=lbl,font=FP,fg=C_GRIS,bg=BG_CARD,anchor="w"
                     ).grid(row=0,column=col_idx*2,columnspan=2,
                            sticky="w",padx=px1,pady=(10,1))
            SunkenEntry(c3,textvariable=self._V(varname)).grid(
                row=1,column=col_idx*2,columnspan=2,
                sticky="ew",padx=px2,pady=(0,2))
            tk.Label(c3,text=hint,font=("Segoe UI",7),fg="#BDBDBD",
                     bg=BG_CARD,anchor="w").grid(
                row=2,column=col_idx*2,columnspan=2,
                sticky="w",padx=px1,pady=(0,10))

        tk.Frame(p,bg=BG_APP,height=8).pack()

        # ── Barre actions bas GROOVE ─────────────────────────────────
        bot=tk.Frame(self,bg="#CFD8DC",relief="groove",bd=3); bot.pack(fill="x",side="bottom")
        RaisedBtn(bot,"Annuler",self.destroy,bg=C_GRIS,pady=6
                  ).pack(side="left",padx=12,pady=10)
        tk.Label(bot,text="* Champ obligatoire",font=("Segoe UI",7),
                 fg=C_GRIS,bg="#CFD8DC").pack(side="right",padx=12)
        RaisedBtn(bot,"Enregistrer le client",self._save,
                  bg=self._col,font=("Segoe UI",10,"bold"),pady=6
                  ).pack(side="right",padx=10,pady=10)
        self._e_nom.focus_set()

    def _sel_type(self, t):
        self._v_type.set(t)
        for k,b in self._tbtns.items():
            if k==t: b.configure(bg=C_BLEU,fg=C_BLANC,relief="sunken",bd=2)
            else:    b.configure(bg=BG_CARD,fg=C_GRIS,relief="raised",bd=2)

    def _save(self):
        nom=self._vars['nom'].get().strip()
        if not nom:
            messagebox.showwarning("Attention", "Le nom / raison sociale est obligatoire."); return
        data={k:v.get() for k,v in self._vars.items()}
        if self.cid: data['id']=self.cid
        db.save_client(data)
        if self.on_save: self.on_save(data)
        self.destroy()

# ═══════════════════════════════════════════════════════════════════
#  PAGE ARTICLES
# ═══════════════════════════════════════════════════════════════════
class ArticlesPage(tk.Frame):
    def __init__(self, p, app):
        super().__init__(p, bg=BG_APP); self.app=app; self._arts=[]; self._build()
    def _build(self):
        hdr=tk.Frame(self,bg=C_BLEU_F,relief="raised",bd=3); hdr.pack(fill="x")
        tk.Label(hdr,text="Catalogue des Articles & Prix Unitaires",
                 font=("Segoe UI",13,"bold"),fg=C_BLANC,bg=C_BLEU_F,
                 anchor="w",pady=10,padx=10).pack(side="left")
        RaisedBtn(hdr,"Nouvel Article",self._new,bg=C_VERT,font=FH3,pady=4
                  ).pack(side="right",padx=10,pady=7)
        filt=GrooveBox(self,bg=BG_CARD,bd=3); filt.pack(fill="x",padx=12,pady=8)
        tk.Label(filt,text="Recherche :",font=FB,fg=C_GRIS,bg=BG_CARD
                 ).pack(side="left",pady=8)
        self.v_s=tk.StringVar()
        e=SunkenEntry(filt,textvariable=self.v_s,width=25); e.pack(side="left",padx=6)
        e.bind("<Return>",lambda _:self.refresh())
        tk.Label(filt,text="Catégorie :",font=FB,fg=C_GRIS,bg=BG_CARD
                 ).pack(side="left",padx=(10,4))
        self.v_cat=tk.StringVar(value="Toutes")
        self.cb_cat=ttk.Combobox(filt,values=["Toutes"],textvariable=self.v_cat,
                                  width=22,font=FB,state="readonly")
        self.cb_cat.pack(side="left")
        RaisedBtn(filt,"Filtrer",self.refresh,bg=C_BLEU,pady=3,padx=8
                  ).pack(side="left",padx=8)
        RaisedBtn(filt,"Réinitialiser",lambda:(self.v_s.set(""),
                  self.v_cat.set("Toutes"),self.refresh()),
                  bg=C_GRIS,pady=3).pack(side="left")
        tf=RidgePanel(self,bg=BG_CARD,bd=3); tf.pack(fill="both",expand=True,padx=12)
        self.tree=mk_tree(tf,("cat","desig","unite","pu","desc"),
            ("Catégorie","Désignation","Unité","Prix Unitaire (FCFA)","Description"),
            [155,330,68,160,200])
        sb=ttk.Scrollbar(tf,command=self.tree.yview); self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right",fill="y"); self.tree.pack(side="left",fill="both",expand=True)
        self.tree.bind("<Double-1>",lambda _:self._edit())
        act=GrooveBox(self,bg=BG_APP,bd=2); act.pack(fill="x",padx=12,pady=8)
        self.lbl_count=tk.Label(act,text="",font=FP,fg=C_GRIS,bg=BG_APP)
        self.lbl_count.pack(side="left",padx=8)
        for txt,cmd,col in [("Modifier",self._edit,C_BLEU),
                             ("Supprimer",self._del,C_ROUGE)]:
            RaisedBtn(act,txt,cmd,bg=col,pady=3,font=FP
                      ).pack(side="right",padx=4,pady=6)
    def refresh(self):
        cats=["Toutes"]+db.get_categories_articles()
        self.cb_cat.configure(values=cats)
        self._arts=db.get_articles(self.v_s.get(),self.v_cat.get())
        self.lbl_count.configure(text=f"  {len(self._arts)} article(s) affiché(s)")
        fill_tree(self.tree,[(a['categorie'],a['designation'],a['unite'],
                              fmt_fcfa(a['prix_unitaire']),a.get('description',''))
                             for a in self._arts])
    def _sel(self):
        sel=self.tree.selection()
        if not sel: messagebox.showinfo("Information", "Veuillez sélectionner un article."); return None
        return self._arts[self.tree.index(sel[0])]
    def _new(self):  ArticleEditor(self,None,on_save=self.refresh)
    def _edit(self):
        a=self._sel()
        if a: ArticleEditor(self,a,on_save=self.refresh)
    def _del(self):
        a=self._sel()
        if a and messagebox.askyesno("Confirmer","Supprimer définitivement cet article ?"):
            db.delete_article(a['id']); self.refresh()

# ─────────────────────────────────────────────────────────────────
class ArticleEditor(tk.Toplevel):
    def __init__(self, p, data, on_save=None):
        super().__init__(p)
        self.data=data or {}; self.on_save=on_save
        self.title("Nouvel Article" if not data else "Modifier Article")
        self.geometry("500x410"); self.resizable(False,False)
        self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        self._build()
    def _build(self):
        hdr=tk.Frame(self,bg=C_BLEU_F,relief="raised",bd=3); hdr.pack(fill="x")
        tk.Label(hdr,text="  "+("Nouvel Article" if not self.data else "Modifier l'article"),
                 font=FH2,fg=C_BLANC,bg=C_BLEU_F,anchor="w",pady=10,padx=10).pack(side="left")
        body=RidgePanel(self,bg=BG_CARD,bd=3); body.pack(padx=15,pady=10,fill="both",expand=True)
        cats=db.get_categories_articles() or ["Général"]
        def row(lbl,w):
            f=tk.Frame(body,bg=BG_CARD); f.pack(fill="x",padx=12,pady=5)
            tk.Label(f,text=lbl,font=FB,fg=C_GRIS,bg=BG_CARD,width=22,anchor="w").pack(side="left")
            w.pack(side="left",fill="x",expand=True)
        self.v_cat=tk.StringVar(value=self.data.get('categorie',cats[0]))
        self.v_desig=tk.StringVar(value=self.data.get('designation',''))
        self.v_unite=tk.StringVar(value=self.data.get('unite','U'))
        self.v_pu=tk.StringVar(value=str(self.data.get('prix_unitaire',0)))
        row("Catégorie :", ttk.Combobox(body,textvariable=self.v_cat,
            values=cats,font=FB,state="normal"))
        row("Désignation :", SunkenEntry(body,textvariable=self.v_desig,width=35))
        row("Unité :", ttk.Combobox(body,textvariable=self.v_unite,
            values=["U","ml","m²","m³","kg","t","h","j","forfait","lot"],
            width=14,font=FB,state="normal"))
        row("Prix unitaire (FCFA) :", SunkenEntry(body,textvariable=self.v_pu,width=20))
        tk.Label(body,text="Description :",font=FB,fg=C_GRIS,bg=BG_CARD,anchor="w"
                 ).pack(anchor="w",padx=12,pady=(5,2))
        self.txt=tk.Text(body,height=3,font=FB,bg=BG_IN,fg=C_NOIR,
                         relief="sunken",bd=2,wrap="word",padx=5,pady=4)
        self.txt.pack(fill="x",padx=12,pady=(0,5))
        self.txt.insert("1.0",self.data.get('description','') or "")
        bot=tk.Frame(self,bg=BG_APP,relief="groove",bd=2)
        bot.pack(fill="x",padx=15,pady=(0,12))
        RaisedBtn(bot,"Enregistrer",self._save,bg=C_VERT,
                  font=("Segoe UI",10,"bold")).pack(side="right",padx=8,pady=8)
        RaisedBtn(bot,"Annuler",self.destroy,bg=C_GRIS).pack(side="right",padx=4,pady=8)
    def _save(self):
        try: pu=float(self.v_pu.get() or 0)
        except: pu=0
        data={'id':self.data.get('id'),'categorie':self.v_cat.get(),
              'designation':self.v_desig.get(),'unite':self.v_unite.get(),
              'prix_unitaire':pu,'description':self.txt.get("1.0","end-1c")}
        if not data['designation'].strip():
            messagebox.showwarning("Attention", "La désignation est obligatoire."); return
        db.save_article(data)
        if self.on_save: self.on_save()
        self.destroy()

# ═══════════════════════════════════════════════════════════════════
#  PAGE ENTREPRISE (sans émojis)
# ═══════════════════════════════════════════════════════════════════
class EntreprisePage(tk.Frame):
    def __init__(self, p, app):
        super().__init__(p,bg=BG_APP); self.app=app
        self._logo_path=""; self._logo_img=None; self._vars={}; self._tbtns={}
        self._build()

    def _V(self,name,default=""):
        v=tk.StringVar(value=str(default)); self._vars[name]=v; return v

    def _build(self):
        hdr=tk.Frame(self,bg=C_BLEU_F,relief="raised",bd=3); hdr.pack(fill="x")
        tk.Label(hdr,text="Paramètres de Mon Entreprise",
                 font=("Segoe UI",13,"bold"),fg=C_BLANC,bg=C_BLEU_F,
                 anchor="w",pady=10,padx=10).pack(side="left")
        RaisedBtn(hdr,"Enregistrer les modifications",self._save,
                  bg=C_VERT,font=("Segoe UI",10,"bold"),pady=4
                  ).pack(side="right",padx=10,pady=7)

        sf=ScrollFrame(self,bg=BG_APP); sf.pack(fill="both",expand=True)
        p=sf.inner

        def sec(titre,color=C_BLEU): sec_bar(p, titre, bg=color)

        def card(cols=2):
            c=RidgePanel(p,bg=BG_CARD,bd=2); c.pack(fill="x",padx=8)
            for i in range(cols*2): c.columnconfigure(i,weight=1 if i%2==1 else 0)
            return c

        def fld(card,row,col,lbl,varname,default="",hint="",
                kind="entry",vals=None,full=False):
            span=4 if full else 1; lc=0 if full else col*2
            tk.Label(card,text=lbl,font=FP,fg=C_GRIS,bg=BG_CARD,anchor="w"
                     ).grid(row=row*3,column=lc,columnspan=span,
                            sticky="w",padx=(12,4),pady=(8,1))
            v=self._V(varname,default)
            if kind=="combo":
                w=ttk.Combobox(card,textvariable=v,values=vals or [],
                               font=FB,state="normal")
            else:
                w=SunkenEntry(card,textvariable=v)
            w.grid(row=row*3+1,column=lc,columnspan=span,
                   sticky="ew",padx=(12,12 if full else 6),pady=(0,1))
            if hint:
                tk.Label(card,text=hint,font=("Segoe UI",7),fg="#BDBDBD",
                         bg=BG_CARD,anchor="w").grid(row=row*3+2,column=lc,
                         columnspan=span,sticky="w",padx=12,pady=(0,4))

        # ── Identité ────────────────────────────────────────────────
        sec("Identité de l'Entreprise")
        c1=card(2); c1.columnconfigure(1,weight=2); c1.columnconfigure(3,weight=1)
        fld(c1,0,0,"Nom complet de l'entreprise *",'nom',
            hint="Exemple : Bâtisseurs du Togo SARL")
        fld(c1,0,1,"Sigle / Abréviation",'sigle',hint="Exemple : BTG")
        fld(c1,1,0,"Forme juridique",'forme_juridique','SARL',kind="combo",
            vals=["SARL","SA","SAS","EI","EURL","GIE","Association","Autre"])
        fld(c1,1,1,"Slogan",'slogan',hint="Exemple : Construire l'excellence")

        # ── Localisation ────────────────────────────────────────────
        sec("Localisation / Adresse",color=C_ORG)
        c2=card(2); c2.columnconfigure(1,weight=2); c2.columnconfigure(3,weight=1)
        fld(c2,0,0,"Adresse (rue, BP…)",'adresse',hint="Exemple : Rue de la Paix, BP 1234")
        fld(c2,0,1,"Quartier / Zone",'quartier',hint="Exemple : Hédzranawoé")
        fld(c2,1,0,"Ville",'ville','Lomé',hint="Exemple : Lomé")
        fld(c2,1,1,"Pays",'pays','Togo',hint="Exemple : Togo")

        # ── Contacts ────────────────────────────────────────────────
        sec("Contacts",color="#1B5E20")
        c3=card(2); c3.columnconfigure(1,weight=1); c3.columnconfigure(3,weight=1)
        fld(c3,0,0,"Téléphone principal",'telephone1',hint="Exemple : +228 90 00 00 00")
        fld(c3,0,1,"Téléphone secondaire",'telephone2',hint="Exemple : +228 92 00 00 00")
        fld(c3,1,0,"Adresse e-mail",'email',hint="Exemple : contact@entreprise.tg")
        fld(c3,1,1,"Site Web",'site_web',hint="Exemple : www.entreprise.tg")

        # ── Identifiants légaux ─────────────────────────────────────
        sec("Identifiants Légaux (RCCM / NIF)")
        c4=card(2); c4.columnconfigure(1,weight=1); c4.columnconfigure(3,weight=1)
        fld(c4,0,0,"N° RCCM",'rccm',hint="Exemple : TG-LOM-2020-B-12345")
        fld(c4,0,1,"NIF",'nif',hint="Exemple : 1234567890123")

        # ── Bancaire ────────────────────────────────────────────────
        sec("Coordonnées Bancaires")
        c5=card(2); c5.columnconfigure(1,weight=1); c5.columnconfigure(3,weight=2)
        fld(c5,0,0,"Nom de la banque",'banque',hint="Exemple : Ecobank / BSIC Togo")
        fld(c5,0,1,"RIB / Numéro de compte",'rib',
            hint="Exemple : TG53 TG007 01234 5678901234567 89")

        # ── TVA ─────────────────────────────────────────────────────
        sec("Fiscalité (TVA)",color=C_BLEU_F)
        c6=card(1)
        fld(c6,0,0,"Taux de TVA appliqué (%)",'tva_taux','18.0',
            hint="Taux standard au Togo : 18 %",full=True)

        # ── Logo ────────────────────────────────────────────────────
        sec("Logo de l'Entreprise (affiché sur les devis PDF)")
        c7=RidgePanel(p,bg=BG_CARD,bd=2); c7.pack(fill="x",padx=8)
        lrow=tk.Frame(c7,bg=BG_CARD); lrow.pack(fill="x",padx=14,pady=12)
        prev_box=tk.Frame(lrow,bg="#E3F2FD",width=170,height=110,
                          relief="sunken",bd=3)
        prev_box.pack(side="left",padx=(0,20)); prev_box.pack_propagate(False)
        self.logo_lbl=tk.Label(prev_box,text="Aucun logo",
                               font=("Segoe UI",9),fg=C_GRIS_L,
                               bg="#E3F2FD",justify="center")
        self.logo_lbl.place(relx=.5,rely=.5,anchor="center")
        lbtns=tk.Frame(lrow,bg=BG_CARD); lbtns.pack(side="left",anchor="n")
        tk.Label(lbtns,text="Format recommandé : PNG transparent 300×150 px",
                 font=FP,fg=C_GRIS,bg=BG_CARD).pack(anchor="w",pady=(0,8))
        RaisedBtn(lbtns,"Choisir un logo…",self._pick_logo,
                  bg=C_BLEU,pady=4).pack(anchor="w",pady=3)
        RaisedBtn(lbtns,"Retirer le logo",self._clear_logo,
                  bg=C_ROUGE,pady=4).pack(anchor="w",pady=3)

        # ── Textes par défaut ───────────────────────────────────────
        sec("Textes par défaut (pré-remplis dans chaque nouveau devis)")
        c8=RidgePanel(p,bg=BG_CARD,bd=2); c8.pack(fill="x",padx=8)
        tk.Label(c8,text="Conditions de règlement par défaut :",
                 font=FB,fg=C_GRIS,bg=BG_CARD,anchor="w"
                 ).pack(fill="x",padx=12,pady=(10,2))
        self.txt_cond=tk.Text(c8,height=3,font=FB,bg=BG_IN,fg=C_NOIR,
                              relief="sunken",bd=2,wrap="word",padx=5,pady=4)
        self.txt_cond.pack(fill="x",padx=12,pady=(0,6))
        tk.Label(c8,text="Délai d'exécution habituel :",
                 font=FB,fg=C_GRIS,bg=BG_CARD,anchor="w"
                 ).pack(fill="x",padx=12,pady=(4,2))
        self.txt_delai=tk.Text(c8,height=2,font=FB,bg=BG_IN,fg=C_NOIR,
                                relief="sunken",bd=2,wrap="word",padx=5,pady=4)
        self.txt_delai.pack(fill="x",padx=12,pady=(0,12))

        bot=RaisedCard(p,bg="#E8F5E9",bd=3); bot.pack(fill="x",padx=8,pady=12)
        RaisedBtn(bot,"Enregistrer toutes les modifications",self._save,
                  bg=C_VERT,font=("Segoe UI",11,"bold"),pady=8).pack(pady=10)
        tk.Label(bot,text="Données enregistrées dans  ~/DevisBTP/",
                 font=FP,fg=C_GRIS,bg="#E8F5E9").pack(pady=(0,10))

    def refresh(self):
        ent=db.get_entreprise()
        for k,v in self._vars.items():
            val=ent.get(k,""); v.set(str(val) if val is not None else "")
        self._logo_path=ent.get('logo_path','') or ""
        self.txt_cond.delete("1.0","end")
        self.txt_cond.insert("1.0",ent.get('conditions_def','') or "")
        self.txt_delai.delete("1.0","end")
        self.txt_delai.insert("1.0",ent.get('delai_def','') or "")
        self._upd_logo()

    def _pick_logo(self):
        path=filedialog.askopenfilename(
            title="Choisir le logo",
            filetypes=[("Images","*.png *.jpg *.jpeg *.bmp *.gif")])
        if path:
            self._logo_path=db.save_logo(path); self._upd_logo()

    def _clear_logo(self):
        self._logo_path=""
        self.logo_lbl.configure(image="",text="Aucun logo"); self._logo_img=None

    def _upd_logo(self):
        if self._logo_path and os.path.exists(self._logo_path):
            try:
                from PIL import Image,ImageTk
                img=Image.open(self._logo_path); img.thumbnail((160,100))
                self._logo_img=ImageTk.PhotoImage(img)
                self.logo_lbl.configure(image=self._logo_img,text=""); return
            except: pass
        self.logo_lbl.configure(image="",text="Aucun logo"); self._logo_img=None

    def _save(self):
        data={k:v.get() for k,v in self._vars.items()}
        try:    data['tva_taux']=float(data.get('tva_taux',18))
        except: data['tva_taux']=18.0
        data['logo_path']     =self._logo_path
        data['conditions_def']=self.txt_cond.get("1.0","end-1c")
        data['delai_def']     =self.txt_delai.get("1.0","end-1c")
        db.save_entreprise(data)
        self.app.status("Informations entreprise sauvegardées !",C_VERT)
        orig=self.cget('bg'); self.configure(bg="#E8F5E9")
        self.after(700,lambda:self.configure(bg=orig))

# ═══════════════════════════════════════════════════════════════════
#  DÉTAIL DEVIS
# ═══════════════════════════════════════════════════════════════════
class DevisDetailView(tk.Toplevel):
    def __init__(self, parent, did, on_edit=None):
        super().__init__(parent)
        self.did     = did
        self.on_edit = on_edit
        self.title("Détail du Devis")
        self.geometry("1020x720")
        self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        devis, lignes = db.get_devis(did)
        if not devis: self.destroy(); return
        self._build(devis, lignes)

    def _build(self, d, lignes):
        ent = db.get_entreprise()
        hdr = tk.Frame(self, bg=C_BLEU_F, relief="raised", bd=3)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"Devis  {d['numero']}",
                 font=("Segoe UI",13,"bold"), fg=C_BLANC,
                 bg=C_BLEU_F, anchor="w", pady=10, padx=10).pack(side="left")

        def edit_close():
            self.destroy()
            DevisEditor(self.master, None, did=self.did, on_save=self.on_edit)

        RaisedBtn(hdr, "Modifier",   edit_close,  bg=C_BLEU, pady=3
                  ).pack(side="right", padx=5, pady=7)
        RaisedBtn(hdr, "Générer PDF", self._pdf,   bg=C_ORG,  pady=3
                  ).pack(side="right", padx=5, pady=7)
        RaisedBtn(hdr, "Fermer",      self.destroy,bg="#455A64", pady=3
                  ).pack(side="right", padx=5, pady=7)

        colors_st = {'Accepté':'#E8F5E9','Envoyé':'#E3F2FD','Facturé':'#F3E5F5',
                     'Refusé':'#FFEBEE','Brouillon':'#FFF9C4'}
        fg_st     = {'Accepté':C_VERT,'Envoyé':C_BLEU,'Facturé':'#6A1B9A',
                     'Refusé':C_ROUGE,'Brouillon':C_ORG}
        st = d.get('statut','Brouillon')
        tk.Label(self,
                 text=f"Statut : {st}",
                 font=("Segoe UI",10,"bold"),
                 bg=colors_st.get(st,'#F5F5F5'),
                 fg=fg_st.get(st,C_NOIR),
                 relief="ridge", bd=2
                 ).pack(anchor="e", padx=12, pady=4)

        sf = ScrollFrame(self, bg=BG_APP)
        sf.pack(fill="both", expand=True)
        p = sf.inner

        def info_card(titre, rows, color=C_BLEU):
            sec_bar(p, titre, bg=color)
            card = RidgePanel(p, bg=BG_CARD, bd=2)
            card.pack(fill="x", padx=8, pady=0)
            for lbl, val in rows:
                f = tk.Frame(card, bg=BG_CARD); f.pack(fill="x", padx=12, pady=3)
                tk.Label(f, text=lbl, font=("Segoe UI",8,"bold"),
                         fg=C_GRIS, bg=BG_CARD, width=22, anchor="w").pack(side="left")
                tk.Label(f, text=str(val) if val else "—",
                         font=FB, fg=C_NOIR, bg=BG_CARD, anchor="w",
                         wraplength=500).pack(side="left", fill="x")
            tk.Frame(card, bg=BG_CARD, height=4).pack()

        def fdate(s):
            try: return datetime.strptime(s, "%Y-%m-%d").strftime("%d/%m/%Y")
            except: return s or "—"

        two = tk.Frame(p, bg=BG_APP); two.pack(fill="x", padx=8, pady=(8,0))
        two.columnconfigure(0, weight=1); two.columnconfigure(1, weight=1)

        def col_card(parent, col, titre, rows, color=C_BLEU):
            f = tk.Frame(parent, bg=BG_APP)
            f.grid(row=0, column=col, sticky="nsew", padx=(0,4) if col==0 else (4,0))
            tk.Label(f, text=titre, font=("Segoe UI",9,"bold"),
                     fg=C_BLANC, bg=color, relief="raised", bd=2,
                     anchor="w", padx=6, pady=5).pack(fill="x")
            card = RidgePanel(f, bg=BG_CARD, bd=2); card.pack(fill="both", expand=True)
            for lbl, val in rows:
                rf = tk.Frame(card, bg=BG_CARD); rf.pack(fill="x", padx=10, pady=3)
                tk.Label(rf, text=lbl, font=("Segoe UI",8,"bold"),
                         fg=C_GRIS, bg=BG_CARD, width=18, anchor="w").pack(side="left")
                tk.Label(rf, text=str(val) if val else "—",
                         font=FB, fg=C_NOIR, bg=BG_CARD, anchor="w").pack(side="left")
            tk.Frame(card, bg=BG_CARD, height=4).pack()

        col_card(two, 0, "Informations Devis", [
            ("N° Devis :",        d.get('numero','')),
            ("Date création :",   fdate(d.get('date_creation',''))),
            ("Date validité :",   fdate(d.get('date_validite',''))),
            ("Statut :",          d.get('statut','')),
            ("Chantier :",        d.get('chantier','')),
            ("Localisation :",    d.get('localisation','')),
            ("Délai exécution :", d.get('delai_execution','')),
            ("TVA :",             f"{d.get('tva_taux',18):.0f} %"),
        ])

        col_card(two, 1, "Client / Maître d'ouvrage", [
            ("Nom :",      d.get('client_nom','')),
            ("Adresse :",  d.get('client_adresse','')),
            ("Ville :",    d.get('client_ville','')),
            ("Téléphone :",d.get('client_tel','')),
            ("Email :",    d.get('client_email','')),
            ("NIF :",      d.get('client_nif','')),
        ], color=C_ORG)

        if d.get('description'):
            sec_bar(p, "Description des travaux")
            dc = RidgePanel(p, bg=BG_CARD, bd=2); dc.pack(fill="x", padx=8)
            tk.Label(dc, text=d['description'], font=FB, fg=C_NOIR, bg=BG_CARD,
                     anchor="w", justify="left", padx=12, pady=8, wraplength=900
                     ).pack(fill="x")

        sec_bar(p, "Détail des Prestations")
        tf = RidgePanel(p, bg=BG_CARD, bd=2); tf.pack(fill="x", padx=8, pady=0)

        tv = mk_tree(tf,
            ("num","desig","unite","qte","pu","mont"),
            ("N°","Désignation","Unité","Quantité","Prix U. (FCFA)","Montant (FCFA)"),
            [38, 370, 65, 72, 128, 128], height=min(len(lignes)+2, 14))
        tv.column("pu",   anchor="e"); tv.column("mont",  anchor="e")
        tv.column("num",  anchor="center"); tv.column("unite", anchor="center")
        tv.column("qte",  anchor="center")
        sb = ttk.Scrollbar(tf, command=tv.yview)
        tv.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y"); tv.pack(side="left", fill="x", expand=True)

        sn = 0; it = 0
        for i, l in enumerate(lignes):
            tl = l.get('type_ligne','item')
            mo = float(l.get('montant',0) or 0)
            if tl == 'section':
                sn += 1; it = 0
                tv.insert("","end", tags=("section",),
                    values=(str(sn), l.get('designation','').upper(),"","","",""))
            elif tl == 'subtotal':
                tv.insert("","end", tags=("subtotal",),
                    values=("Σ", l.get('designation','Sous-total'),"","","",
                            f"{int(mo):,}".replace(',',' ')))
            elif tl == 'comment':
                tv.insert("","end", tags=("comment",),
                    values=("💬", l.get('designation',''),"","","",""))
            else:
                it += 1
                num = f"{sn}.{it}" if sn else str(it)
                tag = "pair" if it%2 else "impair"
                qte = float(l.get('quantite',0) or 0)
                pu  = float(l.get('prix_unitaire',0) or 0)
                qs  = str(int(qte)) if qte==int(qte) else f"{qte:.2f}"
                tv.insert("","end", tags=(tag,),
                    values=(num, l.get('designation',''),
                            l.get('unite',''), qs,
                            f"{int(pu):,}".replace(',',' '),
                            f"{int(mo):,}".replace(',',' ')))

        ht  = float(d.get('montant_ht',0)  or 0)
        tva = float(d.get('montant_tva',0) or 0)
        ttc = float(d.get('montant_ttc',0) or 0)
        tva_t = float(d.get('tva_taux',18) or 18)

        tot_frame = tk.Frame(p, bg=BG_APP); tot_frame.pack(anchor="e", padx=8, pady=6)
        for lbl, val, bold, bg in [
            ("Montant HT :",      fmt_fcfa(ht),  False, BG_STR),
            (f"TVA ({tva_t:.0f}%) :", fmt_fcfa(tva), False, BG_STR),
            ("TOTAL TTC :",       fmt_fcfa(ttc), True,  C_BLEU_F),
        ]:
            row = tk.Frame(tot_frame, bg=bg, relief="ridge" if bold else "groove",
                           bd=2 if bold else 1)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=lbl, font=("Segoe UI",9,"bold") if bold else FH3,
                     fg=C_BLANC if bold else C_GRIS, bg=bg,
                     width=18, anchor="e", padx=8, pady=6).pack(side="left")
            tk.Label(row, text=val, font=("Segoe UI",11,"bold") if bold else FH3,
                     fg=C_BLANC if bold else C_NOIR, bg=bg,
                     anchor="e", padx=12, pady=6).pack(side="right")

        for titre, val in [("Conditions de règlement", d.get('conditions_reglement','')),
                            ("Notes internes",          d.get('notes',''))]:
            if val and val.strip():
                sec_bar(p, titre, bg=C_GRIS)
                vc = RidgePanel(p, bg=BG_CARD, bd=2); vc.pack(fill="x", padx=8)
                tk.Label(vc, text=val, font=FB, fg=C_NOIR, bg=BG_CARD,
                         anchor="w", justify="left", padx=12, pady=8, wraplength=900
                         ).pack(fill="x")

        tk.Frame(p, bg=BG_APP, height=12).pack()

    def _pdf(self):
        devis, lignes = db.get_devis(self.did)
        ent = db.get_entreprise()
        out_dir = Path(db.APP_DIR)/"PDF"; out_dir.mkdir(exist_ok=True)
        out = str(out_dir/f"{devis['numero']}.pdf")
        try:
            generate_devis_pdf(devis, lignes, ent, out)
            if sys.platform=="win32": os.startfile(out)
            else: os.system(f'xdg-open "{out}" &')
        except Exception as ex:
            messagebox.showerror("Erreur PDF", str(ex))


class ClientDetailView(tk.Toplevel):
    def __init__(self, parent, cid, on_edit=None):
        super().__init__(parent)
        self.cid     = cid
        self.on_edit = on_edit
        self.title("Détail du Client")
        self.geometry("820x620")
        self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        client = db.get_client(cid)
        if not client: self.destroy(); return
        self._build(client)

    def _build(self, c):
        type_colors = {'Particulier':C_BLEU,'Entreprise':C_ORG,
                       'Administration':C_VERT,'ONG':'#6A1B9A'}
        tc = type_colors.get(c.get('type_client',''), C_BLEU)

        hdr = tk.Frame(self, bg=tc, relief="raised", bd=3); hdr.pack(fill="x")
        tk.Label(hdr, text=f"{c['nom']}",
                 font=("Segoe UI",13,"bold"), fg=C_BLANC,
                 bg=tc, anchor="w", pady=10, padx=10).pack(side="left")

        def edit_close():
            self.destroy()
            ClientEditor(self.master, self.cid, on_save=self.on_edit)

        RaisedBtn(hdr, "Modifier",   edit_close,   bg=C_BLEU, pady=3
                  ).pack(side="right", padx=5, pady=7)
        RaisedBtn(hdr, "Fermer",      self.destroy, bg="#455A64", pady=3
                  ).pack(side="right", padx=5, pady=7)

        tk.Label(self, text=f"  {c.get('type_client','Inconnu')}  ",
                 font=("Segoe UI",9,"bold"), fg=C_BLANC, bg=tc,
                 relief="ridge", bd=2).pack(anchor="e", padx=12, pady=4)

        sf = ScrollFrame(self, bg=BG_APP); sf.pack(fill="both", expand=True)
        p = sf.inner

        sec_bar(p, "Fiche Identité", bg=tc)
        id_card = RidgePanel(p, bg=BG_CARD, bd=2); id_card.pack(fill="x", padx=8)
        id_card.columnconfigure(1, weight=1); id_card.columnconfigure(3, weight=1)

        infos = [
            ("Nom / Raison sociale :", c.get('nom',''),          0, 0),
            ("Type de client :",       c.get('type_client',''),  1, 0),
            ("NIF :",                  c.get('nif','') or "—",   1, 1),
        ]
        for row, (lbl, val, r, col) in enumerate(infos):
            lc = col*2
            tk.Label(id_card, text=lbl, font=("Segoe UI",8,"bold"),
                     fg=C_GRIS, bg=BG_CARD, anchor="w"
                     ).grid(row=r, column=lc,   sticky="w", padx=(12,4), pady=5)
            tk.Label(id_card, text=str(val) if val else "—",
                     font=FB if lbl!="Nom / Raison sociale :" else ("Segoe UI",10,"bold"),
                     fg=tc if lbl=="Nom / Raison sociale :" else C_NOIR,
                     bg=BG_CARD, anchor="w"
                     ).grid(row=r, column=lc+1, sticky="w", padx=(0,12), pady=5)
        tk.Frame(id_card, bg=BG_CARD, height=4).grid(row=10, column=0)

        sec_bar(p, "Adresse / Localisation", bg=C_ORG)
        ac = RidgePanel(p, bg=BG_CARD, bd=2); ac.pack(fill="x", padx=8)
        for lbl, val in [("Adresse :",  c.get('adresse','')),
                          ("Quartier :", c.get('quartier','')),
                          ("Ville :",    c.get('ville',''))]:
            af = tk.Frame(ac, bg=BG_CARD); af.pack(fill="x", padx=12, pady=3)
            tk.Label(af, text=lbl, font=("Segoe UI",8,"bold"),
                     fg=C_GRIS, bg=BG_CARD, width=16, anchor="w").pack(side="left")
            tk.Label(af, text=str(val) if val else "—",
                     font=FB, fg=C_NOIR, bg=BG_CARD).pack(side="left")
        tk.Frame(ac, bg=BG_CARD, height=4).pack()

        sec_bar(p, "Contacts", bg="#1B5E20")
        cc = RidgePanel(p, bg=BG_CARD, bd=2); cc.pack(fill="x", padx=8)
        for lbl, val in [("Téléphone :", c.get('telephone','')),
                          ("Email :",     c.get('email',''))]:
            cf = tk.Frame(cc, bg=BG_CARD); cf.pack(fill="x", padx=12, pady=3)
            tk.Label(cf, text=lbl, font=("Segoe UI",8,"bold"),
                     fg=C_GRIS, bg=BG_CARD, width=16, anchor="w").pack(side="left")
            tk.Label(cf, text=str(val) if val else "—",
                     font=("Segoe UI",9,"bold"), fg=C_BLEU,
                     bg=BG_CARD).pack(side="left")
        tk.Frame(cc, bg=BG_CARD, height=4).pack()

        devis_client = [d for d in db.get_devis_list() if d.get('client_id')==self.cid]

        sec_bar(p, f"Devis associés  ({len(devis_client)} devis)")
        if devis_client:
            tf = RidgePanel(p, bg=BG_CARD, bd=2); tf.pack(fill="x", padx=8)
            tv = mk_tree(tf,
                ("num","date","chantier","ht","ttc","statut"),
                ("N° Devis","Date","Chantier / Objet","HT","TTC","Statut"),
                [108, 88, 240, 125, 135, 88],
                height=min(len(devis_client)+1, 8))
            tv.column("ht",  anchor="e"); tv.column("ttc", anchor="e")
            tv.pack(fill="x", padx=4, pady=4)
            fill_tree(tv, [(d['numero'], d['date_creation'],
                            d.get('chantier','')[:35],
                            fmt_fcfa(d['montant_ht']),
                            fmt_fcfa(d['montant_ttc']),
                            d['statut']) for d in devis_client])

            def open_linked(event, tv=tv, dl=devis_client):
                sel = tv.selection()
                if not sel: return
                idx = tv.index(sel[0])
                DevisDetailView(self, dl[idx]['id'])
            tv.bind("<Double-1>", open_linked)

            total_ttc = sum(float(d.get('montant_ttc',0) or 0) for d in devis_client)
            total_acc = sum(float(d.get('montant_ttc',0) or 0)
                           for d in devis_client if d['statut'] in ('Accepté','Facturé'))
            tf2 = tk.Frame(p, bg=BG_APP); tf2.pack(anchor="e", padx=8, pady=4)
            for lbl, val, bg in [
                ("Total devis (tous statuts) :", fmt_fcfa(total_ttc), BG_STR),
                ("Total acceptés + facturés :",  fmt_fcfa(total_acc), "#E8F5E9"),
            ]:
                rf = tk.Frame(tf2, bg=bg, relief="groove", bd=1)
                rf.pack(fill="x", pady=2)
                tk.Label(rf, text=lbl, font=FH3, fg=C_GRIS,
                         bg=bg, width=28, anchor="e", padx=8, pady=5).pack(side="left")
                tk.Label(rf, text=val, font=("Segoe UI",10,"bold"),
                         fg=C_VERT, bg=bg, padx=12).pack(side="right")
        else:
            nc = RidgePanel(p, bg=BG_CARD, bd=2); nc.pack(fill="x", padx=8)
            tk.Label(nc, text="Aucun devis pour ce client.",
                     font=FB, fg=C_GRIS_L, bg=BG_CARD, pady=14).pack()

        tk.Frame(p, bg=BG_APP, height=12).pack()

# ═══════════════════════════════════════════════════════════════════
#  DYNAMIC METHOD INJECTION
# ═══════════════════════════════════════════════════════════════════
def _devis_detail_patch(self):
    did = self._sel()
    if not did: return
    DevisDetailView(self, did, on_edit=lambda: (self.refresh(),))

def _client_detail_patch(self):
    cid = self._sel()
    if not cid: return
    ClientDetailView(self, cid, on_edit=lambda: self.refresh())

DevisPage._detail          = _devis_detail_patch
ClientsPage._detail_client = _client_detail_patch

# ═══════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = App()
    app.mainloop()
