"""
app.py  –  DevisBTP v2.0 - Interface graphique professionnelle
Effets relief, palette moderne, TVA par défaut 0%, double‑clic fonctionnel
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, sys
from pathlib import Path
from datetime import datetime

try:
    from ctypes import windll
    windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

import db
from pdf_gen import generate_devis_pdf

# ═══════════════════════════════════════════════════════════════════
#  PALETTE MODERNE
# ═══════════════════════════════════════════════════════════════════
BG_APP    = "#F5F7FA"
BG_SIDE   = "#1E2F4F"
BG_CARD   = "#FFFFFF"
BG_IN     = "#F8FAFE"
BG_HDR    = "#2B4F6E"
BG_STR    = "#EDF2F7"
C_PRIMARY = "#2B4F6E"
C_SECOND  = "#3A6B8C"
C_ACCENT  = "#D97941"
C_SUCCESS = "#2E7D32"
C_DANGER  = "#C62828"
C_WARNING = "#F57C00"
C_GRAY    = "#6B7A8A"
C_GRAY_L  = "#9BA8B8"
C_DARK    = "#1E2F4F"
C_LIGHT   = "#FFFFFF"

FT_TITLE = ("Segoe UI", 14, "bold")
FT_H2    = ("Segoe UI", 11, "bold")
FT_H3    = ("Segoe UI", 10, "bold")
FT_NORM  = ("Segoe UI", 9)
FT_SMALL = ("Segoe UI", 8)

def fmt_fcfa(v):
    try:
        return f"{int(round(float(v))):,}".replace(",", " ") + " FCFA"
    except:
        return "0 FCFA"

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

# ═══════════════════════════════════════════════════════════════════
#  WIDGETS AVEC RELIEF (CORRECTION BUG bd)
# ═══════════════════════════════════════════════════════════════════
class RaisedCard(tk.Frame):
    def __init__(self, parent, bg=BG_CARD, bd=2, **kwargs):
        if 'bd' in kwargs:
            kwargs.pop('bd')
        super().__init__(parent, bg=bg, relief="raised", bd=bd, **kwargs)

class RidgePanel(tk.Frame):
    def __init__(self, parent, bg=BG_CARD, bd=1, **kwargs):
        if 'bd' in kwargs:
            kwargs.pop('bd')
        super().__init__(parent, bg=bg, relief="ridge", bd=bd, **kwargs)

class GrooveBox(tk.Frame):
    def __init__(self, parent, bg=BG_APP, bd=1, **kwargs):
        if 'bd' in kwargs:
            kwargs.pop('bd')
        super().__init__(parent, bg=bg, relief="groove", bd=bd, **kwargs)

class SunkenEntry(tk.Entry):
    def __init__(self, parent, textvariable=None, width=20, **kwargs):
        super().__init__(parent, textvariable=textvariable, width=width,
                         bg=BG_IN, fg=C_DARK, relief="sunken", bd=2,
                         font=FT_NORM, insertbackground=C_PRIMARY,
                         selectbackground=C_SECOND, **kwargs)

class ModernButton(tk.Button):
    def __init__(self, parent, text="", command=None,
                 bg=C_PRIMARY, fg=C_LIGHT, font=FT_NORM, padx=15, pady=5, **kwargs):
        super().__init__(parent, text=text, command=command, bg=bg, fg=fg,
                         font=font, relief="raised", bd=2, cursor="hand2",
                         activebackground=C_SECOND, activeforeground=C_LIGHT,
                         padx=padx, pady=pady, **kwargs)
        self.bind("<Enter>", lambda e: self.config(relief="groove"))
        self.bind("<Leave>", lambda e: self.config(relief="raised"))
        self.bind("<ButtonPress-1>", lambda e: self.config(relief="sunken"))
        self.bind("<ButtonRelease-1>", lambda e: self.config(relief="raised"))

class NavButton(tk.Frame):
    def __init__(self, parent, text, command, **kwargs):
        super().__init__(parent, bg=BG_SIDE, cursor="hand2", **kwargs)
        self.command = command
        self.active = False
        self.inner = tk.Frame(self, bg=BG_SIDE, relief="flat", bd=0)
        self.inner.pack(fill="x", padx=8, pady=4)
        self.label = tk.Label(self.inner, text=text, font=FT_NORM,
                              fg=C_LIGHT, bg=BG_SIDE, anchor="w", padx=12, pady=8)
        self.label.pack(fill="x")
        for w in (self, self.inner, self.label):
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)
            w.bind("<Button-1>", self._on_press)
            w.bind("<ButtonRelease-1>", self._on_release)

    def _on_enter(self, e):
        if not self.active:
            self.inner.config(relief="raised", bd=1, bg=C_SECOND)
            self.label.config(bg=C_SECOND)

    def _on_leave(self, e):
        if not self.active:
            self.inner.config(relief="flat", bd=0, bg=BG_SIDE)
            self.label.config(bg=BG_SIDE)

    def _on_press(self, e):
        self.inner.config(relief="sunken", bd=1)

    def _on_release(self, e):
        self.command()

    def set_active(self, state):
        self.active = state
        if state:
            self.inner.config(relief="ridge", bd=2, bg="#0F2440")
            self.label.config(bg="#0F2440", fg="#F4D03F", font=("Segoe UI", 9, "bold"))
        else:
            self.inner.config(relief="flat", bd=0, bg=BG_SIDE)
            self.label.config(bg=BG_SIDE, fg=C_LIGHT, font=FT_NORM)

class ScrollFrame(tk.Frame):
    def __init__(self, parent, bg=BG_APP, **kwargs):
        super().__init__(parent, bg=bg, **kwargs)
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.window_id = self.canvas.create_window((0,0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.window_id, width=e.width))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))

# ═══════════════════════════════════════════════════════════════════
#  FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════
def section_header(parent, title, bg=C_PRIMARY):
    frame = tk.Frame(parent, bg=bg, relief="raised", bd=1)
    frame.pack(fill="x", padx=12, pady=(12,6))
    tk.Label(frame, text=f"  {title}", font=FT_H3, fg=C_LIGHT, bg=bg,
             anchor="w", pady=5, padx=8).pack(fill="x")
def create_tree(parent, columns, headings, widths, height=12):
    tree = ttk.Treeview(parent, columns=columns, show="headings",
                        height=height, selectmode="browse")
    for col, hd, w in zip(columns, headings, widths):
        tree.heading(col, text=hd)
        tree.column(col, width=w, minwidth=30)
    tree.tag_configure("pair", background=BG_STR)
    tree.tag_configure("impair", background=BG_CARD)
    tree.tag_configure("section", background="#D9E6F2", foreground=C_PRIMARY, font=("Segoe UI", 9, "bold"))
    tree.tag_configure("subtotal", background="#FFF3E0", foreground=C_ACCENT, font=("Segoe UI", 9, "bold"))
    tree.tag_configure("comment", background="#F5F5F5", foreground=C_GRAY, font=("Segoe UI", 8, "italic"))
    return tree

def fill_tree(tree, rows):
    tree.delete(*tree.get_children())
    for i, row in enumerate(rows):
        tree.insert("", "end", values=row, tags=("pair" if i%2 else "impair",))

# ═══════════════════════════════════════════════════════════════════
#  SPLASH SCREEN
# ═══════════════════════════════════════════════════════════════════
class Splash(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.overrideredirect(True)
        w, h = 500, 320
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        body = tk.Frame(self, bg=C_PRIMARY, relief="raised", bd=5)
        body.pack(fill="both", expand=True)
        tk.Label(body, text="⚙", font=("Segoe UI", 40), bg=C_PRIMARY, fg="#F4D03F").pack(pady=(30,5))
        tk.Label(body, text="DevisBTP", font=("Segoe UI", 28, "bold"), bg=C_PRIMARY, fg=C_LIGHT).pack()
        tk.Label(body, text="Logiciel de devis · Génie Civil · Togo",
                 font=("Segoe UI", 11), bg=C_PRIMARY, fg="#B0D4FF").pack()
        tk.Label(body, text="Bâtiment · Routes · Ouvrages d'Art",
                 font=FT_SMALL, bg=C_PRIMARY, fg="#89CFF0").pack(pady=(5,15))
        bar_bg = tk.Frame(body, bg="#0F2440", relief="sunken", bd=2)
        bar_bg.pack(fill="x", padx=50, pady=5)
        self.bar = tk.Frame(bar_bg, bg="#F4D03F", height=8)
        self.bar.place(x=0, y=0, relheight=1, width=0)
        self.msg = tk.Label(body, text="Initialisation...", font=FT_SMALL,
                            bg=C_PRIMARY, fg="#B0D4FF")
        self.msg.pack(pady=(10,5))
        tk.Label(body, text="v2.0 · FCFA · TVA par défaut 0%",
                 font=("Segoe UI", 7), bg=C_PRIMARY, fg="#6B9EC7").pack()
        self.update()
        self._bar_width = bar_bg.winfo_width() or 400

    def progress(self, pct, msg=""):
        self.bar.place(width=int(self._bar_width * pct / 100))
        if msg:
            self.msg.config(text=msg)
        self.update()

# ═══════════════════════════════════════════════════════════════════
#  APPLICATION PRINCIPALE
# ═══════════════════════════════════════════════════════════════════
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self._run_splash()
        self.title("DevisBTP – Génie Civil · Togo")
        self.geometry("1380x860")
        self.minsize(1100, 700)
        self.configure(bg=BG_APP)
        self._pages = {}
        self._build_ui()
        self._setup_menu()
        self.show_page("dashboard")
        self.deiconify()

    def _run_splash(self):
        import time
        sp = Splash(self)
        sp.update()
        time.sleep(0.2)
        for pct, msg in [(20, "Chargement base de données..."),
                         (50, "Préparation de l'interface..."),
                         (80, "Chargement du catalogue..."),
                         (100, "Bienvenue !")]:
            time.sleep(0.3)
            sp.progress(pct, msg)
        db.init_db()
        time.sleep(0.2)
        sp.destroy()

    def _build_ui(self):
        self.sidebar = tk.Frame(self, bg=BG_SIDE, width=240, relief="raised", bd=3)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        outer = tk.Frame(self, bg=BG_APP, relief="sunken", bd=1)
        outer.pack(side="left", fill="both", expand=True)
        self.content = tk.Frame(outer, bg=BG_APP)
        self.content.pack(fill="both", expand=True)
        self.statusbar = tk.Label(self, text="  Prêt", font=FT_SMALL,
                                  fg=C_GRAY, bg="#E2E8F0", anchor="w",
                                  relief="groove", bd=1)
        self.statusbar.pack(side="bottom", fill="x")
        self._build_sidebar()
        self._build_pages()

    def status(self, msg, color=C_GRAY):
        self.statusbar.config(text=f"  {msg}", fg=color)
        self.after(3500, lambda: self.statusbar.config(text="  Prêt", fg=C_GRAY))

    def _build_sidebar(self):
        sb = self.sidebar
        logo_frame = tk.Frame(sb, bg="#0F2440", relief="ridge", bd=2)
        logo_frame.pack(fill="x", padx=10, pady=(10,5))
        tk.Label(logo_frame, text="DevisBTP", font=("Segoe UI", 16, "bold"),
                 fg="#F4D03F", bg="#0F2440", pady=8).pack()
        tk.Label(logo_frame, text="Génie Civil · Togo",
                 font=FT_SMALL, fg="#89CFF0", bg="#0F2440").pack(pady=(0,8))
        tk.Frame(sb, height=2, bg=C_SECOND, relief="ridge").pack(fill="x", padx=10, pady=5)
        self.nav_btns = {}
        for label, page in [("Tableau de bord", "dashboard"),
                            ("Gestion des Devis", "devis"),
                            ("Clients", "clients"),
                            ("Articles & Prix", "articles"),
                            ("Mon Entreprise", "entreprise")]:
            btn = NavButton(sb, label, command=lambda p=page: self.show_page(p))
            btn.pack(fill="x")
            self.nav_btns[page] = btn
        tk.Frame(sb, height=2, bg=C_SECOND, relief="ridge").pack(fill="x", padx=10, pady=8)
        ModernButton(sb, "Nouveau Devis", self._quick_new, bg=C_ACCENT, font=FT_NORM,
                     padx=5, pady=5).pack(fill="x", padx=10, pady=5)
        tk.Label(sb, text="v2.0 · 2025 · FCFA", font=("Segoe UI", 7),
                 fg=C_GRAY_L, bg=BG_SIDE).pack(side="bottom", pady=10)

    def _quick_new(self):
        self.show_page("devis")
        DevisEditor(self.content, self, did=None,
                    on_save=lambda: self._pages['devis'].refresh())

    def _setup_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Fichier", menu=file_menu)
        file_menu.add_command(label="Nouveau Devis", command=self._quick_new, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="Entreprise", command=lambda: self.show_page("entreprise"))
        file_menu.add_separator()
        file_menu.add_command(label="Quitter", command=self.quit)
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Affichage", menu=view_menu)
        for label, page in [("Tableau de bord", "dashboard"), ("Devis", "devis"),
                            ("Clients", "clients"), ("Articles", "articles")]:
            view_menu.add_command(label=label, command=lambda p=page: self.show_page(p))
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Aide", menu=help_menu)
        help_menu.add_command(label="À propos", command=self._about)
        help_menu.add_command(label="Guide", command=self._guide)
        self.bind_all("<Control-n>", lambda e: self._quick_new())

    def _about(self):
        win = tk.Toplevel(self)
        win.title("À propos")
        win.geometry("450x350")
        win.resizable(False, False)
        win.configure(bg=BG_APP)
        win.grab_set()
        body = RaisedCard(win, bg=C_PRIMARY, bd=4)
        body.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(body, text="DevisBTP", font=("Segoe UI", 22, "bold"),
                 fg="#F4D03F", bg=C_PRIMARY).pack(pady=(20,5))
        tk.Label(body, text="Logiciel de devis pour le BTP\nBâtiment · Routes · Ouvrages d'Art",
                 font=FT_NORM, fg=C_LIGHT, bg=C_PRIMARY, justify="center").pack()
        tk.Frame(body, height=2, bg=C_SECOND).pack(fill="x", padx=30, pady=10)
        for line in ["Version 2.0", "Devise : FCFA (Franc CFA)", "Pays : Togo",
                     "TVA par défaut : 0%", "PDF professionnel A4"]:
            tk.Label(body, text=line, font=FT_SMALL, fg="#B0D4FF", bg=C_PRIMARY).pack()
        tk.Frame(body, height=2, bg=C_SECOND).pack(fill="x", padx=30, pady=10)
        ModernButton(body, "Fermer", win.destroy, bg=C_SECOND).pack(pady=10)

    def _guide(self):
        win = tk.Toplevel(self)
        win.title("Guide d'utilisation")
        win.geometry("650x550")
        win.configure(bg=BG_APP)
        win.grab_set()
        tk.Label(win, text="Guide d'utilisation", font=FT_TITLE,
                 fg=C_PRIMARY, bg=BG_APP).pack(pady=15)
        sf = ScrollFrame(win, bg=BG_APP)
        sf.pack(fill="both", expand=True, padx=15, pady=5)
        p = sf.inner
        items = [
            ("1. Configurer votre entreprise",
             "Rendez-vous dans 'Mon Entreprise' : remplissez nom, adresse, RCCM, NIF, logo, banque.\n"
             "Ces informations apparaîtront sur tous vos devis PDF."),
            ("2. Ajouter vos clients",
             "Onglet 'Clients' : créez vos maîtres d'ouvrage.\n"
             "Types : Particulier, Entreprise, Administration, ONG."),
            ("3. Catalogue d'articles",
             "Onglet 'Articles & Prix' : 66 articles pré-chargés.\n"
             "Modifiez les prix unitaires ou ajoutez des articles personnalisés."),
            ("4. Créer un devis",
             "Cliquez sur 'Nouveau Devis' ou Ctrl+N.\n"
             "Panneau gauche : client, chantier, dates, TVA, conditions.\n"
             "Panneau droit : sections + prestations (catalogue ou manuelles).\n"
             "HT, TVA et TTC calculés automatiquement."),
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
             "Ctrl+N = nouveau devis depuis n'importe où.")
        ]
        for titre, texte in items:
            bloc = RidgePanel(p, bg=BG_CARD, bd=1)
            bloc.pack(fill="x", padx=5, pady=6)
            tk.Label(bloc, text=titre, font=FT_H3, fg=C_PRIMARY,
                     bg=BG_CARD, anchor="w", padx=12, pady=6).pack(fill="x")
            tk.Frame(bloc, height=1, bg=C_GRAY_L).pack(fill="x", padx=12)
            tk.Label(bloc, text=texte, font=FT_NORM, fg=C_DARK,
                     bg=BG_CARD, anchor="w", justify="left",
                     padx=15, pady=8).pack(fill="x")
        ModernButton(win, "Fermer", win.destroy, bg=C_PRIMARY).pack(pady=15)

    def _build_pages(self):
        for cls, key in [(DashboardPage, "dashboard"),
                         (DevisPage, "devis"),
                         (ClientsPage, "clients"),
                         (ArticlesPage, "articles"),
                         (EntreprisePage, "entreprise")]:
            page = cls(self.content, self)
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            self._pages[key] = page

    def show_page(self, key):
        for k, btn in self.nav_btns.items():
            btn.set_active(k == key)
        self._pages[key].tkraise()
        if hasattr(self._pages[key], "refresh"):
            self._pages[key].refresh()
        self.status(f"Page : {key.capitalize()}")

# ═══════════════════════════════════════════════════════════════════
#  PAGE TABLEAU DE BORD
# ═══════════════════════════════════════════════════════════════════
class DashboardPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_APP)
        self.app = app
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=C_PRIMARY, relief="raised", bd=2)
        header.pack(fill="x")
        tk.Label(header, text="Tableau de Bord", font=FT_TITLE,
                 fg=C_LIGHT, bg=C_PRIMARY, anchor="w", pady=10, padx=15).pack(side="left")
        self.date_label = tk.Label(header, text=datetime.now().strftime("%A %d %B %Y"),
                                   font=FT_SMALL, fg="#B0D4FF", bg=C_PRIMARY)
        self.date_label.pack(side="right", padx=15)
        self.cards_frame = tk.Frame(self, bg=BG_APP)
        self.cards_frame.pack(fill="x", padx=20, pady=15)
        section_header(self, "Derniers devis créés")
        tree_frame = RidgePanel(self, bg=BG_CARD, bd=1)
        tree_frame.pack(fill="both", expand=True, padx=15, pady=(5,15))
        self.tree = create_tree(tree_frame,
            ("num","date","client","chantier","ttc","statut"),
            ("N° Devis","Date","Client","Chantier / Objet","Montant TTC","Statut"),
            [110,90,180,230,150,95], height=9)
        scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", self._open_devis)
        btn_frame = tk.Frame(self, bg=BG_APP)
        btn_frame.pack(fill="x", padx=20, pady=(0,15))
        ModernButton(btn_frame, "Nouveau Devis", lambda: self.app.show_page("devis"),
                     bg=C_SUCCESS).pack(side="left", padx=5)
        ModernButton(btn_frame, "Tous les Devis", lambda: self.app.show_page("devis"),
                     bg=C_PRIMARY).pack(side="left", padx=5)

    def _stat_card(self, parent, value, label, color, subtext=""):
        card = RaisedCard(parent, bg=BG_CARD, bd=2)
        card.pack(side="left", padx=8, pady=4, ipadx=10, ipady=8)
        tk.Label(card, text=value, font=("Segoe UI", 18, "bold"),
                 fg=color, bg=BG_CARD).pack()
        tk.Label(card, text=label, font=FT_NORM, fg=C_GRAY, bg=BG_CARD).pack()
        if subtext:
            tk.Label(card, text=subtext, font=FT_SMALL, fg=C_GRAY_L, bg=BG_CARD).pack()

    def refresh(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()
        stats = db.get_stats()
        year = datetime.now().year
        items = [
            (str(stats['total_devis']), "Total Devis", C_PRIMARY, "Tous statuts"),
            (str(stats['devis_mois']), "Ce mois", C_ACCENT, f"{datetime.now().month}/{year}"),
            (str(stats['devis_acceptes']), "Acceptés", C_SUCCESS, ""),
            (str(stats['devis_en_attente']), "En attente", C_WARNING, "Brouillon+Envoyé"),
            (str(stats['devis_refuses']), "Refusés", C_DANGER, ""),
            (str(stats['nb_clients']), "Clients", C_SECOND, ""),
            (fmt_fcfa(stats['ca_annee']).replace(" FCFA",""), f"CA {year}", C_SUCCESS, "TTC acceptés"),
        ]
        for val, lbl, col, sub in items:
            self._stat_card(self.cards_frame, val, lbl, col, sub)
        rows = [(r['numero'], r['date_creation'], r.get('client_nom','—'),
                 r.get('chantier','')[:35], fmt_fcfa(r['montant_ttc']), r['statut'])
                for r in stats['recents']]
        fill_tree(self.tree, rows)

    def _open_devis(self, event):
        sel = self.tree.selection()
        if not sel:
            return
        num = self.tree.item(sel[0])['values'][0]
        for d in db.get_devis_list():
            if d['numero'] == num:
                DevisEditor(self, self.app, did=d['id'], on_save=self.refresh)
                break

# ═══════════════════════════════════════════════════════════════════
#  PAGE GESTION DES DEVIS
# ═══════════════════════════════════════════════════════════════════
class DevisPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_APP)
        self.app = app
        self.devis_ids = []
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=C_PRIMARY, relief="raised", bd=2)
        header.pack(fill="x")
        tk.Label(header, text="Gestion des Devis", font=FT_TITLE,
                 fg=C_LIGHT, bg=C_PRIMARY, anchor="w", pady=10, padx=15).pack(side="left")
        ModernButton(header, "Nouveau Devis", self._new, bg=C_SUCCESS, font=FT_NORM,
                     padx=10, pady=4).pack(side="right", padx=15)
        filter_frame = GrooveBox(self, bg=BG_CARD, bd=1)
        filter_frame.pack(fill="x", padx=15, pady=10)
        tk.Label(filter_frame, text="Recherche :", font=FT_NORM, fg=C_GRAY, bg=BG_CARD
                 ).pack(side="left", padx=(15,5), pady=8)
        self.search_var = tk.StringVar()
        search_entry = SunkenEntry(filter_frame, textvariable=self.search_var, width=25)
        search_entry.pack(side="left", padx=5)
        search_entry.bind("<Return>", lambda e: self.refresh())
        tk.Label(filter_frame, text="Statut :", font=FT_NORM, fg=C_GRAY, bg=BG_CARD
                 ).pack(side="left", padx=(15,5))
        self.status_var = tk.StringVar(value="Tous")
        status_combo = ttk.Combobox(filter_frame,
            values=["Tous","Brouillon","Envoyé","Accepté","Refusé","Facturé"],
            textvariable=self.status_var, width=12, state="readonly", font=FT_NORM)
        status_combo.pack(side="left")
        ModernButton(filter_frame, "Filtrer", self.refresh, bg=C_PRIMARY, padx=8
                     ).pack(side="left", padx=10)
        ModernButton(filter_frame, "Réinitialiser", self._reset, bg=C_GRAY, padx=8
                     ).pack(side="left")
        tree_frame = RidgePanel(self, bg=BG_CARD, bd=1)
        tree_frame.pack(fill="both", expand=True, padx=15, pady=5)
        self.tree = create_tree(tree_frame,
            ("num","date","client","chantier","ht","ttc","statut"),
            ("N° Devis","Date","Client","Chantier / Objet","HT","TTC","Statut"),
            [110,90,170,210,135,145,95])
        scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._detail())
        action_frame = GrooveBox(self, bg=BG_APP, bd=1)
        action_frame.pack(fill="x", padx=15, pady=10)
        tk.Label(action_frame, text="Actions :", font=FT_NORM, fg=C_GRAY, bg=BG_APP
                 ).pack(side="left", padx=10)
        for text, cmd, color in [("Modifier", self._edit, C_PRIMARY),
                                 ("PDF", self._pdf, C_ACCENT),
                                 ("Changer Statut", self._change_status, C_SECOND),
                                 ("Dupliquer", self._duplicate, C_GRAY),
                                 ("Supprimer", self._delete, C_DANGER)]:
            ModernButton(action_frame, text, cmd, bg=color, padx=10, pady=3
                         ).pack(side="left", padx=5)

    def refresh(self):
        rows = db.get_devis_list(self.search_var.get(), self.status_var.get())
        self.devis_ids = [r['id'] for r in rows]
        fill_tree(self.tree,
            [(r['numero'], r['date_creation'],
              r.get('client_nom','')[:24], r.get('chantier','')[:30],
              fmt_fcfa(r['montant_ht']), fmt_fcfa(r['montant_ttc']),
              r['statut']) for r in rows])

    def _reset(self):
        self.search_var.set("")
        self.status_var.set("Tous")
        self.refresh()

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Information", "Veuillez sélectionner un devis.")
            return None
        return self.devis_ids[self.tree.index(sel[0])]

    def _new(self):
        DevisEditor(self, self.app, did=None, on_save=self.refresh)

    def _edit(self):
        did = self._selected_id()
        if did:
            DevisEditor(self, self.app, did=did, on_save=self.refresh)

    def _pdf(self):
        did = self._selected_id()
        if not did:
            return
        devis, lignes = db.get_devis(did)
        ent = db.get_entreprise()
        out = Path(db.APP_DIR) / "PDF" / f"{devis['numero']}.pdf"
        out.parent.mkdir(exist_ok=True)
        try:
            generate_devis_pdf(devis, lignes, ent, str(out))
            self.app.status(f"PDF généré : {devis['numero']}", C_SUCCESS)
            if sys.platform == "win32":
                os.startfile(out)
            else:
                os.system(f'xdg-open "{out}" &')
        except Exception as e:
            messagebox.showerror("Erreur PDF", str(e))

    def _change_status(self):
        did = self._selected_id()
        if not did:
            return
        devis, lignes = db.get_devis(did)
        if not devis:
            return
        win = tk.Toplevel(self)
        win.title("Changer le statut")
        win.geometry("320x280")
        win.resizable(False, False)
        win.configure(bg=BG_APP)
        win.grab_set()
        tk.Label(win, text=f"Devis {devis['numero']}", font=FT_H3,
                 fg=C_PRIMARY, bg=BG_APP).pack(pady=15)
        tk.Label(win, text="Nouveau statut :", font=FT_NORM, fg=C_GRAY, bg=BG_APP).pack()
        var = tk.StringVar(value=devis['statut'])
        for s, bg_color in [("Brouillon","#FFF9C4"), ("Envoyé","#E3F2FD"),
                            ("Accepté","#E8F5E9"), ("Refusé","#FFEBEE"), ("Facturé","#F3E5F5")]:
            frame = tk.Frame(win, bg=bg_color, relief="ridge", bd=1)
            frame.pack(fill="x", padx=25, pady=3)
            tk.Radiobutton(frame, text=f"  {s}", variable=var, value=s,
                           font=FT_NORM, bg=bg_color, fg=C_DARK).pack(anchor="w", padx=8, pady=3)
        def apply():
            devis['statut'] = var.get()
            db.save_devis(devis, lignes)
            self.refresh()
            win.destroy()
        ModernButton(win, "Appliquer", apply, bg=C_SUCCESS).pack(pady=15)

    def _duplicate(self):
        did = self._selected_id()
        if did:
            db.duplicate_devis(did)
            self.refresh()
            self.app.status("Devis dupliqué.", C_SUCCESS)

    def _delete(self):
        did = self._selected_id()
        if not did:
            return
        d, _ = db.get_devis(did)
        if messagebox.askyesno("Confirmation", f"Supprimer définitivement le devis {d['numero']} ?"):
            db.delete_devis(did)
            self.refresh()
            self.app.status("Devis supprimé.", C_DANGER)

# ═══════════════════════════════════════════════════════════════════
#  PAGE CLIENTS
# ═══════════════════════════════════════════════════════════════════
class ClientsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_APP)
        self.app = app
        self.clients = []
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=C_ACCENT, relief="raised", bd=2)
        header.pack(fill="x")
        tk.Label(header, text="Clients / Maîtres d'Ouvrage", font=FT_TITLE,
                 fg=C_LIGHT, bg=C_ACCENT, anchor="w", pady=10, padx=15).pack(side="left")
        ModernButton(header, "Nouveau Client", self._new, bg=C_SUCCESS, font=FT_NORM,
                     padx=10, pady=4).pack(side="right", padx=15)
        filter_frame = GrooveBox(self, bg=BG_CARD, bd=1)
        filter_frame.pack(fill="x", padx=15, pady=10)
        tk.Label(filter_frame, text="Recherche :", font=FT_NORM, fg=C_GRAY, bg=BG_CARD
                 ).pack(side="left", padx=(15,5), pady=8)
        self.search_var = tk.StringVar()
        search_entry = SunkenEntry(filter_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=5)
        search_entry.bind("<Return>", lambda e: self.refresh())
        ModernButton(filter_frame, "Filtrer", self.refresh, bg=C_PRIMARY, padx=8
                     ).pack(side="left", padx=10)
        ModernButton(filter_frame, "Réinitialiser", lambda: (self.search_var.set(""), self.refresh()),
                     bg=C_GRAY, padx=8).pack(side="left")
        tree_frame = RidgePanel(self, bg=BG_CARD, bd=1)
        tree_frame.pack(fill="both", expand=True, padx=15, pady=5)
        self.tree = create_tree(tree_frame,
            ("nom","type","adresse","ville","tel","email","nif"),
            ("Nom / Raison sociale","Type","Adresse","Ville","Téléphone","Email","NIF"),
            [200,100,190,105,120,170,105])
        scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._detail_client())
        action_frame = GrooveBox(self, bg=BG_APP, bd=1)
        action_frame.pack(fill="x", padx=15, pady=10)
        tk.Label(action_frame, text="Actions :", font=FT_NORM, fg=C_GRAY, bg=BG_APP
                 ).pack(side="left", padx=10)
        ModernButton(action_frame, "Modifier", self._edit, bg=C_PRIMARY, padx=10
                     ).pack(side="left", padx=5)
        ModernButton(action_frame, "Supprimer", self._delete, bg=C_DANGER, padx=10
                     ).pack(side="left", padx=5)

    def refresh(self):
        self.clients = db.get_clients(self.search_var.get())
        fill_tree(self.tree,
            [(c['nom'], c.get('type_client',''),
              c.get('adresse','')[:28], c['ville'],
              c['telephone'], c.get('email','')[:28],
              c.get('nif','')) for c in self.clients])

    def _selected_id(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Information", "Veuillez sélectionner un client.")
            return None
        return self.clients[self.tree.index(sel[0])]['id']

    def _new(self):
        ClientEditor(self, None, on_save=lambda _: self.refresh())

    def _edit(self):
        cid = self._selected_id()
        if cid:
            ClientEditor(self, cid, on_save=lambda _: self.refresh())

    def _delete(self):
        cid = self._selected_id()
        if not cid:
            return
        if db.count_devis_client(cid) > 0:
            messagebox.showwarning("Impossible", "Ce client possède des devis. Supprimez-les d'abord.")
            return
        if messagebox.askyesno("Confirmer", "Supprimer définitivement ce client ?"):
            db.delete_client(cid)
            self.refresh()
            self.app.status("Client supprimé.", C_DANGER)

# ═══════════════════════════════════════════════════════════════════
#  ÉDITEUR CLIENT
# ═══════════════════════════════════════════════════════════════════
class ClientEditor(tk.Toplevel):
    def __init__(self, parent, cid, on_save=None):
        super().__init__(parent)
        self.cid = cid
        self.on_save = on_save
        self.vars = {}
        is_new = not cid
        self.color = C_SUCCESS if is_new else C_ACCENT
        self.title("Nouveau Client" if is_new else "Modifier Client")
        self.geometry("620x680")
        self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        self._build()
        if cid:
            client = db.get_client(cid)
            for k, v in client.items():
                if k in self.vars:
                    self.vars[k].set(str(v) if v else "")
            self._select_type(client.get('type_client', 'Particulier'))

    def _var(self, name, default=""):
        v = tk.StringVar(value=str(default))
        self.vars[name] = v
        return v

    def _build(self):
        header = tk.Frame(self, bg=self.color, relief="raised", bd=2)
        header.pack(fill="x")
        tk.Label(header, text=f"  {'+ Nouveau Client' if not self.cid else '✏ Modifier Client'}",
                 font=FT_H2, fg=C_LIGHT, bg=self.color, anchor="w", pady=12, padx=15).pack()
        scroll = ScrollFrame(self, bg=BG_APP)
        scroll.pack(fill="both", expand=True)
        p = scroll.inner

        def section(title, col=C_PRIMARY):
            section_header(p, title, bg=col)

        def field(card, row, col, label, vname, default="", hint="", kind="entry", values=None, full=False):
            span = 4 if full else 1
            lc = 0 if full else col*2
            tk.Label(card, text=label, font=FT_SMALL, fg=C_GRAY, bg=BG_CARD, anchor="w"
                     ).grid(row=row*3, column=lc, columnspan=span,
                            sticky="w", padx=(12,4), pady=(6,1))
            v = self._var(vname, default)
            if kind == "combo":
                w = ttk.Combobox(card, textvariable=v, values=values or [], font=FT_NORM, state="readonly")
            else:
                w = SunkenEntry(card, textvariable=v)
            w.grid(row=row*3+1, column=lc, columnspan=span,
                   sticky="ew", padx=(12,12 if full else 6), pady=(0,1))
            if hint:
                tk.Label(card, text=hint, font=("Segoe UI", 7), fg="#BDBDBD",
                         bg=BG_CARD, anchor="w").grid(row=row*3+2, column=lc,
                         columnspan=span, sticky="w", padx=12, pady=(0,3))

        section("Identité", self.color)
        card1 = RidgePanel(p, bg=BG_CARD, bd=1)
        card1.pack(fill="x", padx=10, pady=5)
        card1.columnconfigure(1, weight=1)
        tk.Label(card1, text="Nom complet / Raison sociale  *(obligatoire)",
                 font=FT_SMALL, fg=C_GRAY, bg=BG_CARD, anchor="w"
                 ).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(8,1))
        self.nom_entry = SunkenEntry(card1, textvariable=self._var('nom'), width=40)
        self.nom_entry.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0,5))
        tk.Label(card1, text="Ex: M. KODJO AMEWOU  —  SARL CONSTRUCTION TOGO",
                 font=("Segoe UI",7), fg="#BDBDBD", bg=BG_CARD, anchor="w"
                 ).grid(row=2, column=0, columnspan=2, sticky="w", padx=12, pady=(0,8))

        tk.Label(card1, text="Type de client", font=FT_SMALL, fg=C_GRAY, bg=BG_CARD, anchor="w"
                 ).grid(row=3, column=0, columnspan=2, sticky="w", padx=12, pady=(4,2))
        type_row = tk.Frame(card1, bg=BG_CARD)
        type_row.grid(row=4, column=0, columnspan=2, sticky="w", padx=12, pady=(0,8))
        self.type_var = self._var('type_client', 'Particulier')
        self.type_btns = {}
        for t in ["Particulier", "Entreprise", "Administration", "ONG"]:
            btn = tk.Button(type_row, text=t, font=FT_SMALL,
                            relief="raised", bd=1, padx=8, pady=3, cursor="hand2",
                            command=lambda x=t: self._select_type(x))
            btn.pack(side="left", padx=3)
            self.type_btns[t] = btn
        self._select_type('Particulier')

        field(card1, 3, 0, "NIF (Identifiant Fiscal)", 'nif',
              hint="Laisser vide pour les particuliers", full=True)
        tk.Frame(card1, height=5, bg=BG_CARD).grid(row=11, column=0)

        section("Localisation / Adresse", C_ACCENT)
        card2 = RidgePanel(p, bg=BG_CARD, bd=1)
        card2.pack(fill="x", padx=10, pady=5)
        card2.columnconfigure(1, weight=2)
        card2.columnconfigure(3, weight=1)
        tk.Label(card2, text="Adresse complète (rue, BP, lot…)",
                 font=FT_SMALL, fg=C_GRAY, bg=BG_CARD, anchor="w"
                 ).grid(row=0, column=0, columnspan=4, sticky="w", padx=12, pady=(8,1))
        SunkenEntry(card2, textvariable=self._var('adresse')).grid(
            row=1, column=0, columnspan=4, sticky="ew", padx=12, pady=(0,5))
        tk.Label(card2, text="Ex: Rue des Cocotiers, Lot 12 — BP 450",
                 font=("Segoe UI",7), fg="#BDBDBD", bg=BG_CARD, anchor="w"
                 ).grid(row=2, column=0, columnspan=4, sticky="w", padx=12, pady=(0,8))
        for col_idx, lbl, vname, defval in [(0,"Quartier / Zone", 'quartier', ""),
                                            (1,"Ville", 'ville', "Lomé")]:
            tk.Label(card2, text=lbl, font=FT_SMALL, fg=C_GRAY, bg=BG_CARD, anchor="w"
                     ).grid(row=3, column=col_idx*2, columnspan=2,
                            sticky="w", padx=(12,4) if col_idx==0 else (4,4), pady=(4,1))
            SunkenEntry(card2, textvariable=self._var(vname, defval)).grid(
                row=4, column=col_idx*2, columnspan=2,
                sticky="ew", padx=(12,4) if col_idx==0 else (4,12), pady=(0,8))

        section("Contacts", C_SECOND)
        card3 = RidgePanel(p, bg=BG_CARD, bd=1)
        card3.pack(fill="x", padx=10, pady=5)
        card3.columnconfigure(1, weight=1)
        card3.columnconfigure(3, weight=1)
        for col_idx, lbl, vname, hint in [
            (0,"Numéro de téléphone", 'telephone', "Ex: +228 90 12 34 56"),
            (1,"Adresse e-mail", 'email', "Ex: nom@domaine.tg")]:
            px1 = (12,4) if col_idx==0 else (4,4)
            px2 = (12,4) if col_idx==0 else (4,12)
            tk.Label(card3, text=lbl, font=FT_SMALL, fg=C_GRAY, bg=BG_CARD, anchor="w"
                     ).grid(row=0, column=col_idx*2, columnspan=2,
                            sticky="w", padx=px1, pady=(8,1))
            SunkenEntry(card3, textvariable=self._var(vname)).grid(
                row=1, column=col_idx*2, columnspan=2,
                sticky="ew", padx=px2, pady=(0,2))
            tk.Label(card3, text=hint, font=("Segoe UI",7), fg="#BDBDBD",
                     bg=BG_CARD, anchor="w").grid(
                row=2, column=col_idx*2, columnspan=2,
                sticky="w", padx=px1, pady=(0,8))

        bottom = tk.Frame(self, bg="#CFD8DC", relief="groove", bd=1)
        bottom.pack(fill="x", side="bottom")
        ModernButton(bottom, "Annuler", self.destroy, bg=C_GRAY, padx=15
                     ).pack(side="left", padx=15, pady=8)
        tk.Label(bottom, text="* Champ obligatoire", font=("Segoe UI",7),
                 fg=C_GRAY, bg="#CFD8DC").pack(side="right", padx=15)
        ModernButton(bottom, "Enregistrer le client", self._save,
                     bg=self.color, font=FT_NORM, padx=15).pack(side="right", padx=10, pady=8)
        self.nom_entry.focus_set()

    def _select_type(self, t):
        self.type_var.set(t)
        for k, btn in self.type_btns.items():
            if k == t:
                btn.config(bg=C_PRIMARY, fg=C_LIGHT, relief="sunken", bd=2)
            else:
                btn.config(bg=BG_CARD, fg=C_GRAY, relief="raised", bd=1)

    def _save(self):
        nom = self.vars['nom'].get().strip()
        if not nom:
            messagebox.showwarning("Attention", "Le nom / raison sociale est obligatoire.")
            return
        data = {k: v.get() for k, v in self.vars.items()}
        if self.cid:
            data['id'] = self.cid
        db.save_client(data)
        if self.on_save:
            self.on_save(data)
        self.destroy()

# ═══════════════════════════════════════════════════════════════════
#  PAGE ARTICLES
# ═══════════════════════════════════════════════════════════════════
class ArticlesPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_APP)
        self.app = app
        self.articles = []
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=C_PRIMARY, relief="raised", bd=2)
        header.pack(fill="x")
        tk.Label(header, text="Catalogue des Articles & Prix", font=FT_TITLE,
                 fg=C_LIGHT, bg=C_PRIMARY, anchor="w", pady=10, padx=15).pack(side="left")
        ModernButton(header, "Nouvel Article", self._new, bg=C_SUCCESS, font=FT_NORM,
                     padx=10, pady=4).pack(side="right", padx=15)
        filter_frame = GrooveBox(self, bg=BG_CARD, bd=1)
        filter_frame.pack(fill="x", padx=15, pady=10)
        tk.Label(filter_frame, text="Recherche :", font=FT_NORM, fg=C_GRAY, bg=BG_CARD
                 ).pack(side="left", padx=(15,5), pady=8)
        self.search_var = tk.StringVar()
        search_entry = SunkenEntry(filter_frame, textvariable=self.search_var, width=25)
        search_entry.pack(side="left", padx=5)
        search_entry.bind("<Return>", lambda e: self.refresh())
        tk.Label(filter_frame, text="Catégorie :", font=FT_NORM, fg=C_GRAY, bg=BG_CARD
                 ).pack(side="left", padx=(15,5))
        self.cat_var = tk.StringVar(value="Toutes")
        self.cat_combo = ttk.Combobox(filter_frame, values=["Toutes"], textvariable=self.cat_var,
                                      width=22, font=FT_NORM, state="readonly")
        self.cat_combo.pack(side="left")
        ModernButton(filter_frame, "Filtrer", self.refresh, bg=C_PRIMARY, padx=8
                     ).pack(side="left", padx=10)
        ModernButton(filter_frame, "Réinitialiser", lambda: (self.search_var.set(""),
                     self.cat_var.set("Toutes"), self.refresh()),
                     bg=C_GRAY, padx=8).pack(side="left")
        tree_frame = RidgePanel(self, bg=BG_CARD, bd=1)
        tree_frame.pack(fill="both", expand=True, padx=15, pady=5)
        self.tree = create_tree(tree_frame,
            ("cat","desig","unite","pu","desc"),
            ("Catégorie","Désignation","Unité","Prix (FCFA)","Description"),
            [150,340,70,150,210])
        scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._edit())
        action_frame = GrooveBox(self, bg=BG_APP, bd=1)
        action_frame.pack(fill="x", padx=15, pady=10)
        self.count_label = tk.Label(action_frame, text="", font=FT_SMALL, fg=C_GRAY, bg=BG_APP)
        self.count_label.pack(side="left", padx=10)
        ModernButton(action_frame, "Modifier", self._edit, bg=C_PRIMARY, padx=10
                     ).pack(side="right", padx=5)
        ModernButton(action_frame, "Supprimer", self._delete, bg=C_DANGER, padx=10
                     ).pack(side="right", padx=5)

    def refresh(self):
        cats = ["Toutes"] + db.get_categories_articles()
        self.cat_combo.configure(values=cats)
        self.articles = db.get_articles(self.search_var.get(), self.cat_var.get())
        self.count_label.config(text=f"  {len(self.articles)} article(s) affiché(s)")
        fill_tree(self.tree,
            [(a['categorie'], a['designation'], a['unite'],
              fmt_fcfa(a['prix_unitaire']), a.get('description','')[:40])
             for a in self.articles])

    def _selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Information", "Veuillez sélectionner un article.")
            return None
        return self.articles[self.tree.index(sel[0])]

    def _new(self):
        ArticleEditor(self, None, on_save=self.refresh)

    def _edit(self):
        art = self._selected()
        if art:
            ArticleEditor(self, art, on_save=self.refresh)

    def _delete(self):
        art = self._selected()
        if art and messagebox.askyesno("Confirmer", "Supprimer définitivement cet article ?"):
            db.delete_article(art['id'])
            self.refresh()

class ArticleEditor(tk.Toplevel):
    def __init__(self, parent, data, on_save=None):
        super().__init__(parent)
        self.data = data or {}
        self.on_save = on_save
        self.title("Nouvel Article" if not data else "Modifier Article")
        self.geometry("520x440")
        self.resizable(False, False)
        self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        self._build()

    def _build(self):
        header = tk.Frame(self, bg=C_PRIMARY, relief="raised", bd=2)
        header.pack(fill="x")
        tk.Label(header, text="  " + ("Nouvel Article" if not self.data else "Modifier l'article"),
                 font=FT_H2, fg=C_LIGHT, bg=C_PRIMARY, anchor="w", pady=10, padx=15).pack()
        body = RidgePanel(self, bg=BG_CARD, bd=1)
        body.pack(padx=15, pady=15, fill="both", expand=True)
        cats = db.get_categories_articles() or ["Général"]

        def row(lbl, w):
            f = tk.Frame(body, bg=BG_CARD)
            f.pack(fill="x", padx=12, pady=5)
            tk.Label(f, text=lbl, font=FT_NORM, fg=C_GRAY, bg=BG_CARD,
                     width=22, anchor="w").pack(side="left")
            w.pack(side="left", fill="x", expand=True)

        self.cat_var = tk.StringVar(value=self.data.get('categorie', cats[0]))
        self.desig_var = tk.StringVar(value=self.data.get('designation',''))
        self.unite_var = tk.StringVar(value=self.data.get('unite','U'))
        self.pu_var = tk.StringVar(value=str(self.data.get('prix_unitaire',0)))
        row("Catégorie :", ttk.Combobox(body, textvariable=self.cat_var,
            values=cats, font=FT_NORM, state="normal"))
        row("Désignation :", SunkenEntry(body, textvariable=self.desig_var, width=35))
        row("Unité :", ttk.Combobox(body, textvariable=self.unite_var,
            values=["U","ml","m²","m³","kg","t","h","j","forfait","lot"],
            width=14, font=FT_NORM, state="normal"))
        row("Prix unitaire (FCFA) :", SunkenEntry(body, textvariable=self.pu_var, width=20))
        tk.Label(body, text="Description :", font=FT_NORM, fg=C_GRAY, bg=BG_CARD, anchor="w"
                 ).pack(anchor="w", padx=12, pady=(5,2))
        self.desc_text = tk.Text(body, height=3, font=FT_NORM, bg=BG_IN, fg=C_DARK,
                                 relief="sunken", bd=1, wrap="word", padx=5, pady=4)
        self.desc_text.pack(fill="x", padx=12, pady=(0,5))
        self.desc_text.insert("1.0", self.data.get('description','') or "")

        bottom = tk.Frame(self, bg=BG_APP, relief="groove", bd=1)
        bottom.pack(fill="x", padx=15, pady=(0,15))
        ModernButton(bottom, "Enregistrer", self._save, bg=C_SUCCESS, padx=15
                     ).pack(side="right", padx=8, pady=8)
        ModernButton(bottom, "Annuler", self.destroy, bg=C_GRAY, padx=15
                     ).pack(side="right", padx=5, pady=8)

    def _save(self):
        try:
            pu = float(self.pu_var.get() or 0)
        except:
            pu = 0
        data = {
            'id': self.data.get('id'),
            'categorie': self.cat_var.get(),
            'designation': self.desig_var.get(),
            'unite': self.unite_var.get(),
            'prix_unitaire': pu,
            'description': self.desc_text.get("1.0", "end-1c")
        }
        if not data['designation'].strip():
            messagebox.showwarning("Attention", "La désignation est obligatoire.")
            return
        db.save_article(data)
        if self.on_save:
            self.on_save()
        self.destroy()

# ═══════════════════════════════════════════════════════════════════
#  PAGE ENTREPRISE
# ═══════════════════════════════════════════════════════════════════
class EntreprisePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_APP)
        self.app = app
        self.logo_path = ""
        self.logo_img = None
        self.vars = {}
        self._build()

    def _var(self, name, default=""):
        v = tk.StringVar(value=str(default))
        self.vars[name] = v
        return v

    def _build(self):
        header = tk.Frame(self, bg=C_PRIMARY, relief="raised", bd=2)
        header.pack(fill="x")
        tk.Label(header, text="Paramètres de Mon Entreprise", font=FT_TITLE,
                 fg=C_LIGHT, bg=C_PRIMARY, anchor="w", pady=10, padx=15).pack(side="left")
        ModernButton(header, "Enregistrer", self._save, bg=C_SUCCESS, font=FT_NORM,
                     padx=15, pady=4).pack(side="right", padx=15)

        scroll = ScrollFrame(self, bg=BG_APP)
        scroll.pack(fill="both", expand=True)
        p = scroll.inner

        def section(title, col=C_PRIMARY):
            section_header(p, title, bg=col)

        def card(cols=2):
            c = RidgePanel(p, bg=BG_CARD, bd=1)
            c.pack(fill="x", padx=12, pady=6)
            for i in range(cols*2):
                c.columnconfigure(i, weight=1 if i%2==1 else 0)
            return c

        def field(card, row, col, label, vname, default="", hint="", kind="entry", values=None, full=False):
            span = 4 if full else 1
            lc = 0 if full else col*2
            tk.Label(card, text=label, font=FT_SMALL, fg=C_GRAY, bg=BG_CARD, anchor="w"
                     ).grid(row=row*3, column=lc, columnspan=span,
                            sticky="w", padx=(12,4), pady=(6,1))
            v = self._var(vname, default)
            if kind == "combo":
                w = ttk.Combobox(card, textvariable=v, values=values or [], font=FT_NORM, state="normal")
            else:
                w = SunkenEntry(card, textvariable=v)
            w.grid(row=row*3+1, column=lc, columnspan=span,
                   sticky="ew", padx=(12,12 if full else 6), pady=(0,1))
            if hint:
                tk.Label(card, text=hint, font=("Segoe UI",7), fg="#BDBDBD",
                         bg=BG_CARD, anchor="w").grid(row=row*3+2, column=lc,
                         columnspan=span, sticky="w", padx=12, pady=(0,3))

        section("Identité")
        c1 = card(2)
        c1.columnconfigure(1, weight=2)
        c1.columnconfigure(3, weight=1)
        field(c1, 0, 0, "Nom complet *", 'nom', hint="Ex: Bâtisseurs du Togo SARL")
        field(c1, 0, 1, "Sigle", 'sigle', hint="Ex: BTG")
        field(c1, 1, 0, "Forme juridique", 'forme_juridique', 'SARL', kind="combo",
              values=["SARL","SA","SAS","EI","EURL","GIE","Association","Autre"])
        field(c1, 1, 1, "Slogan", 'slogan', hint="Ex: Construire l'excellence")

        section("Localisation / Adresse", C_ACCENT)
        c2 = card(2)
        c2.columnconfigure(1, weight=2)
        c2.columnconfigure(3, weight=1)
        field(c2, 0, 0, "Adresse", 'adresse', hint="Ex: Rue de la Paix, BP 1234")
        field(c2, 0, 1, "Quartier", 'quartier', hint="Ex: Hédzranawoé")
        field(c2, 1, 0, "Ville", 'ville', 'Lomé', hint="Ex: Lomé")
        field(c2, 1, 1, "Pays", 'pays', 'Togo', hint="Ex: Togo")

        section("Contacts", C_SECOND)
        c3 = card(2)
        c3.columnconfigure(1, weight=1)
        c3.columnconfigure(3, weight=1)
        field(c3, 0, 0, "Tél principal", 'telephone1', hint="Ex: +228 90 00 00 00")
        field(c3, 0, 1, "Tél secondaire", 'telephone2', hint="Ex: +228 92 00 00 00")
        field(c3, 1, 0, "Email", 'email', hint="Ex: contact@entreprise.tg")
        field(c3, 1, 1, "Site Web", 'site_web', hint="Ex: www.entreprise.tg")

        section("Identifiants légaux")
        c4 = card(2)
        c4.columnconfigure(1, weight=1)
        c4.columnconfigure(3, weight=1)
        field(c4, 0, 0, "N° RCCM", 'rccm', hint="Ex: TG-LOM-2020-B-12345")
        field(c4, 0, 1, "NIF", 'nif', hint="Ex: 1234567890123")

        section("Coordonnées bancaires")
        c5 = card(2)
        c5.columnconfigure(1, weight=1)
        c5.columnconfigure(3, weight=2)
        field(c5, 0, 0, "Banque", 'banque', hint="Ex: Ecobank / BSIC")
        field(c5, 0, 1, "RIB", 'rib', hint="Ex: TG53 TG007 01234 5678901234567 89")

        section("Fiscalité (TVA)", C_SUCCESS)
        c6 = card(1)
        field(c6, 0, 0, "Taux TVA (%)", 'tva_taux', '0.0',
              hint="Togo: 18% standard — modifiable ici", full=True)

        section("Logo de l'entreprise")
        logo_card = RidgePanel(p, bg=BG_CARD, bd=1)
        logo_card.pack(fill="x", padx=12, pady=6)
        logo_row = tk.Frame(logo_card, bg=BG_CARD)
        logo_row.pack(fill="x", padx=15, pady=12)
        preview = tk.Frame(logo_row, bg="#E3F2FD", width=170, height=110,
                           relief="sunken", bd=2)
        preview.pack(side="left", padx=(0,20))
        preview.pack_propagate(False)
        self.logo_label = tk.Label(preview, text="Aucun logo", font=FT_SMALL,
                                   fg=C_GRAY_L, bg="#E3F2FD", justify="center")
        self.logo_label.place(relx=.5, rely=.5, anchor="center")
        btn_frame = tk.Frame(logo_row, bg=BG_CARD)
        btn_frame.pack(side="left", anchor="n")
        tk.Label(btn_frame, text="Format recommandé : PNG transparent 300×150 px",
                 font=FT_SMALL, fg=C_GRAY, bg=BG_CARD).pack(anchor="w", pady=(0,8))
        ModernButton(btn_frame, "Choisir un logo", self._pick_logo, bg=C_PRIMARY, pady=3
                     ).pack(anchor="w", pady=3)
        ModernButton(btn_frame, "Retirer le logo", self._clear_logo, bg=C_DANGER, pady=3
                     ).pack(anchor="w", pady=3)

        section("Textes par défaut")
        text_card = RidgePanel(p, bg=BG_CARD, bd=1)
        text_card.pack(fill="x", padx=12, pady=6)
        tk.Label(text_card, text="Conditions de règlement par défaut :",
                 font=FT_NORM, fg=C_GRAY, bg=BG_CARD, anchor="w"
                 ).pack(fill="x", padx=12, pady=(8,2))
        self.cond_text = tk.Text(text_card, height=3, font=FT_NORM, bg=BG_IN, fg=C_DARK,
                                 relief="sunken", bd=1, wrap="word", padx=5, pady=4)
        self.cond_text.pack(fill="x", padx=12, pady=(0,5))
        tk.Label(text_card, text="Délai d'exécution habituel :",
                 font=FT_NORM, fg=C_GRAY, bg=BG_CARD, anchor="w"
                 ).pack(fill="x", padx=12, pady=(4,2))
        self.delay_text = tk.Text(text_card, height=2, font=FT_NORM, bg=BG_IN, fg=C_DARK,
                                  relief="sunken", bd=1, wrap="word", padx=5, pady=4)
        self.delay_text.pack(fill="x", padx=12, pady=(0,10))

        bottom = RaisedCard(p, bg="#E8F5E9", bd=1)
        bottom.pack(fill="x", padx=12, pady=12)
        ModernButton(bottom, "Enregistrer toutes les modifications", self._save,
                     bg=C_SUCCESS, font=FT_NORM, padx=20, pady=6).pack(pady=10)
        tk.Label(bottom, text="Données enregistrées dans ~/DevisBTP/",
                 font=FT_SMALL, fg=C_GRAY, bg="#E8F5E9").pack(pady=(0,8))

    def refresh(self):
        ent = db.get_entreprise()
        for k, v in self.vars.items():
            val = ent.get(k, "")
            v.set(str(val) if val is not None else "")
        self.logo_path = ent.get('logo_path', '') or ""
        self.cond_text.delete("1.0", "end")
        self.cond_text.insert("1.0", ent.get('conditions_def', '') or "")
        self.delay_text.delete("1.0", "end")
        self.delay_text.insert("1.0", ent.get('delai_def', '') or "")
        self._update_logo()

    def _pick_logo(self):
        path = filedialog.askopenfilename(
            title="Choisir le logo",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif")]
        )
        if path:
            self.logo_path = db.save_logo(path)
            self._update_logo()

    def _clear_logo(self):
        self.logo_path = ""
        self.logo_label.config(image="", text="Aucun logo")
        self.logo_img = None

    def _update_logo(self):
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                from PIL import Image, ImageTk
                img = Image.open(self.logo_path)
                img.thumbnail((160,100))
                self.logo_img = ImageTk.PhotoImage(img)
                self.logo_label.config(image=self.logo_img, text="")
                return
            except:
                pass
        self.logo_label.config(image="", text="Aucun logo")
        self.logo_img = None

    def _save(self):
        data = {k: v.get() for k, v in self.vars.items()}
        try:
            data['tva_taux'] = float(data.get('tva_taux', 0))
        except:
            data['tva_taux'] = 0.0
        data['logo_path'] = self.logo_path
        data['conditions_def'] = self.cond_text.get("1.0", "end-1c")
        data['delai_def'] = self.delay_text.get("1.0", "end-1c")
        db.save_entreprise(data)
        self.app.status("Informations entreprise sauvegardées !", C_SUCCESS)
        orig = self.cget('bg')
        self.configure(bg="#E8F5E9")
        self.after(700, lambda: self.configure(bg=orig))

# ═══════════════════════════════════════════════════════════════════
#  ÉDITEUR DEVIS (LA CLASSE LA PLUS LONGUE)
# ═══════════════════════════════════════════════════════════════════
class DevisEditor(tk.Toplevel):
    def __init__(self, parent, app, did=None, on_save=None):
        super().__init__(parent)
        self.app = app
        self.did = did
        self.on_save = on_save
        self.lignes = []
        self.ent = db.get_entreprise()
        self.client_id = tk.IntVar(value=0)
        self.client_nom = tk.StringVar(value="— Aucun client sélectionné —")
        self._vars = {}
        self.title("Nouveau Devis" if not did else "Modifier Devis")
        self.geometry("1350x850")
        self.minsize(1100, 700)
        self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        self._build()
        if did:
            self._load(did)
        else:
            self._defaults()

    def _var(self, name, default=""):
        v = tk.StringVar(value=str(default))
        self._vars[name] = v
        return v

    def _defaults(self):
        self._var('numero', db.next_devis_numero())
        self._var('date_creation', today_str())
        self._var('statut', "Brouillon")
        self._var('tva_taux', str(self.ent.get('tva_taux', 0)))
        self._var('delai_execution', self.ent.get('delai_def', '') or "")
        self.cond_text.delete("1.0", "end")
        self.cond_text.insert("1.0", self.ent.get('conditions_def', '') or "")

    def _build(self):
        top_bar = tk.Frame(self, bg=C_PRIMARY, relief="raised", bd=2)
        top_bar.pack(fill="x")
        tk.Label(top_bar, text="Éditeur de Devis", font=FT_TITLE,
                 fg=C_LIGHT, bg=C_PRIMARY, pady=8, padx=15).pack(side="left")
        ModernButton(top_bar, "Générer PDF", self._pdf, bg=C_ACCENT, pady=3
                     ).pack(side="right", padx=5, pady=5)
        ModernButton(top_bar, "Enregistrer", self._save, bg=C_SUCCESS, font=FT_NORM, pady=3
                     ).pack(side="right", padx=5, pady=5)
        ModernButton(top_bar, "Fermer", self.destroy, bg=C_GRAY, pady=3
                     ).pack(side="right", padx=5, pady=5)

        paned = tk.PanedWindow(self, orient="horizontal", bg="#B0BEC5",
                               sashwidth=5, sashrelief="raised", bd=0)
        paned.pack(fill="both", expand=True)
        left = tk.Frame(paned, bg=BG_APP)
        right = tk.Frame(paned, bg=BG_APP)
        paned.add(left, minsize=360, width=420)
        paned.add(right, minsize=600)
        self._build_left(left)
        self._build_right(right)

    def _build_left(self, parent):
        tk.Label(parent, text="Informations", font=FT_H2,
                 fg=C_LIGHT, bg=C_PRIMARY, relief="raised", bd=1,
                 anchor="w", padx=10, pady=6).pack(fill="x")
        scroll = ScrollFrame(parent, bg=BG_APP)
        scroll.pack(fill="both", expand=True)
        q = scroll.inner

        def field(card, label, vname, default="", hint="", kind="entry", values=None):
            tk.Label(card, text=label, font=FT_SMALL, fg=C_GRAY, bg=BG_CARD, anchor="w"
                     ).pack(fill="x", padx=10, pady=(6,1))
            v = self._var(vname, default)
            if kind == "combo":
                w = ttk.Combobox(card, textvariable=v, values=values or [], font=FT_NORM, state="readonly")
            else:
                w = SunkenEntry(card, textvariable=v)
            w.pack(fill="x", padx=10, pady=(0,1 if hint else 3))
            if hint:
                tk.Label(card, text=hint, font=("Segoe UI",7), fg="#BDBDBD",
                         bg=BG_CARD, anchor="w").pack(fill="x", padx=10, pady=(0,4))

        section_header(q, "Référence du devis")
        c1 = RidgePanel(q, bg=BG_CARD, bd=1)
        c1.pack(fill="x", padx=8, pady=4)
        field(c1, "Numéro du devis", "numero", hint="Généré automatiquement")
        field(c1, "Date de création", "date_creation", hint="AAAA-MM-JJ")
        field(c1, "Date de validité", "date_validite", hint="Ex: 2025-03-15")
        field(c1, "Statut", "statut", "Brouillon", kind="combo",
              values=["Brouillon","Envoyé","Accepté","Refusé","Facturé"])
        tk.Frame(c1, height=4, bg=BG_CARD).pack()

        section_header(q, "Client / Maître d'ouvrage", C_ACCENT)
        c2 = RidgePanel(q, bg=BG_CARD, bd=1)
        c2.pack(fill="x", padx=8, pady=4)
        tk.Label(c2, text="Client sélectionné", font=FT_SMALL, fg=C_GRAY,
                 bg=BG_CARD, anchor="w").pack(fill="x", padx=10, pady=(8,2))
        tk.Label(c2, textvariable=self.client_nom, font=FT_H3, fg=C_PRIMARY,
                 bg=BG_STR, relief="sunken", bd=1, anchor="w", padx=8, pady=6
                 ).pack(fill="x", padx=10, pady=(0,6))
        btn_frame = tk.Frame(c2, bg=BG_CARD)
        btn_frame.pack(fill="x", padx=10, pady=(0,10))
        ModernButton(btn_frame, "Choisir client", self._pick_client, bg=C_PRIMARY, pady=3, font=FT_SMALL
                     ).pack(side="left", padx=(0,4))
        ModernButton(btn_frame, "Nouveau client", self._new_client, bg=C_SUCCESS, pady=3, font=FT_SMALL
                     ).pack(side="left")

        section_header(q, "Chantier et localisation")
        c3 = RidgePanel(q, bg=BG_CARD, bd=1)
        c3.pack(fill="x", padx=8, pady=4)
        field(c3, "Intitulé du chantier", "chantier", hint="Ex: Construction Villa R+1")
        field(c3, "Localisation", "localisation", hint="Ex: Lomé, Tokoin, Lot 45")
        tk.Label(c3, text="Description des travaux", font=FT_SMALL, fg=C_GRAY,
                 bg=BG_CARD, anchor="w").pack(fill="x", padx=10, pady=(6,2))
        self.desc_text = tk.Text(c3, height=4, font=FT_NORM, bg=BG_IN, fg=C_DARK,
                                 relief="sunken", bd=1, wrap="word", padx=5, pady=4)
        self.desc_text.pack(fill="x", padx=10, pady=(0,8))

        section_header(q, "Conditions financières", C_SUCCESS)
        c4 = RidgePanel(q, bg=BG_CARD, bd=1)
        c4.pack(fill="x", padx=8, pady=4)
        field(c4, "Taux TVA (%)", "tva_taux", "0", hint="Togo: 0% par défaut")
        field(c4, "Délai d'exécution", "delai_execution", hint="Ex: 6 mois, 90 jours...")
        tk.Label(c4, text="Conditions de règlement", font=FT_SMALL, fg=C_GRAY,
                 bg=BG_CARD, anchor="w").pack(fill="x", padx=10, pady=(6,2))
        self.cond_text = tk.Text(c4, height=3, font=FT_NORM, bg=BG_IN, fg=C_DARK,
                                 relief="sunken", bd=1, wrap="word", padx=5, pady=4)
        self.cond_text.pack(fill="x", padx=10, pady=(0,4))
        tk.Label(c4, text="Notes internes (non imprimées)", font=FT_SMALL, fg=C_GRAY,
                 bg=BG_CARD, anchor="w").pack(fill="x", padx=10, pady=(6,2))
        self.notes_text = tk.Text(c4, height=3, font=FT_NORM, bg=BG_IN, fg=C_DARK,
                                  relief="sunken", bd=1, wrap="word", padx=5, pady=4)
        self.notes_text.pack(fill="x", padx=10, pady=(0,10))

    def _build_right(self, parent):
        tk.Label(parent, text="Détail des Prestations", font=FT_H2,
                 fg=C_LIGHT, bg=C_ACCENT, relief="raised", bd=1,
                 anchor="w", padx=10, pady=6).pack(fill="x")
        toolbar = GrooveBox(parent, bg=BG_CARD, bd=1)
        toolbar.pack(fill="x")
        row1 = tk.Frame(toolbar, bg=BG_CARD)
        row1.pack(fill="x", padx=8, pady=(8,3))
        tk.Label(row1, text="Ajouter :", font=FT_NORM, fg=C_GRAY, bg=BG_CARD
                 ).pack(side="left", padx=(0,6))
        for txt, tl, col in [("Prestation", "item", C_SUCCESS),
                             ("Section", "section", C_PRIMARY),
                             ("Sous-total", "subtotal", C_ACCENT),
                             ("Commentaire", "comment", C_GRAY)]:
            ModernButton(row1, txt, lambda t=tl: self._add(t), bg=col, font=FT_SMALL,
                         padx=8, pady=2).pack(side="left", padx=3)
        ModernButton(row1, "Catalogue", self._catalog, bg=C_SECOND, font=FT_SMALL,
                     padx=8, pady=2).pack(side="left", padx=(15,3))
        row2 = tk.Frame(toolbar, bg=BG_CARD)
        row2.pack(fill="x", padx=8, pady=(0,8))
        tk.Label(row2, text="Ligne :", font=FT_NORM, fg=C_GRAY, bg=BG_CARD
                 ).pack(side="left", padx=(0,6))
        for txt, cmd, col in [("Modifier", self._edit_ligne, C_PRIMARY),
                              ("Monter", lambda: self._move(-1), C_GRAY),
                              ("Descendre", lambda: self._move(1), C_GRAY),
                              ("Supprimer", self._del_ligne, C_DANGER)]:
            ModernButton(row2, txt, cmd, bg=col, font=FT_SMALL, padx=8, pady=2
                         ).pack(side="left", padx=3)
        tk.Label(toolbar, text="Astuce : double-clic pour modifier — flèches pour réordonner",
                 font=FT_SMALL, fg=C_GRAY_L, bg=BG_CARD).pack(fill="x", padx=10, pady=(0,6))

        table_frame = RidgePanel(parent, bg=BG_CARD, bd=1)
        table_frame.pack(fill="both", expand=True)
        self.tv = create_tree(table_frame,
            ("num","desig","unite","qte","pu","mont"),
            ("N°","Désignation des Travaux","Unité","Quantité","Prix U. (FCFA)","Montant (FCFA)"),
            [40,355,65,72,132,132])
        self.tv.column("pu", anchor="e")
        self.tv.column("mont", anchor="e")
        self.tv.column("num", anchor="center")
        self.tv.column("unite", anchor="center")
        self.tv.column("qte", anchor="center")
        scroll = ttk.Scrollbar(table_frame, command=self.tv.yview)
        self.tv.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tv.pack(side="left", fill="both", expand=True)
        self.tv.bind("<Double-1>", lambda e: self._edit_ligne())

        total_frame = RaisedCard(parent, bg="#E8EAF6", bd=2)
        total_frame.pack(fill="x")
        tk.Label(total_frame, text="Montants : Quantité × Prix Unitaire",
                 font=FT_SMALL, fg=C_GRAY, bg="#E8EAF6").pack(side="left", padx=10)
        tr = tk.Frame(total_frame, bg="#E8EAF6")
        tr.pack(side="right")
        for lbl, attr, bg, fg, bold in [
            ("Montant HT", "lbl_ht", "#E8EAF6", C_DARK, False),
            ("TVA", "lbl_tva", "#E8EAF6", C_GRAY, False),
            ("TOTAL TTC", "lbl_ttc", C_PRIMARY, C_LIGHT, True)]:
            f = tk.Frame(tr, bg=bg, relief="groove" if bold else "flat",
                         bd=2 if bold else 0, padx=14, pady=8)
            f.pack(side="left")
            tk.Label(f, text=lbl, font=FT_SMALL if not bold else FT_H3,
                     fg="white" if bold else C_GRAY, bg=bg).pack()
            v = tk.Label(f, text="0 FCFA", font=FT_NORM if not bold else ("Segoe UI", 10, "bold"),
                         fg="white" if bold else C_DARK, bg=bg)
            v.pack()
            setattr(self, attr, v)

    def _load(self, did):
        d, lignes = db.get_devis(did)
        if not d:
            return
        for k, v in self._vars.items():
            val = d.get(k)
            if val is not None:
                v.set(str(val))
        if d.get('client_id'):
            self.client_id.set(d['client_id'])
            self.client_nom.set(d.get('client_nom', ''))
        self.desc_text.delete("1.0", "end")
        self.desc_text.insert("1.0", d.get('description', '') or "")
        self.cond_text.delete("1.0", "end")
        self.cond_text.insert("1.0", d.get('conditions_reglement', '') or "")
        self.notes_text.delete("1.0", "end")
        self.notes_text.insert("1.0", d.get('notes', '') or "")
        self.lignes = lignes
        self._refresh()

    def _refresh(self):
        self.tv.delete(*self.tv.get_children())
        sec_num = 0
        item_num = 0
        for i, l in enumerate(self.lignes):
            tl = l.get('type_ligne', 'item')
            mont = float(l.get('montant', 0) or 0)
            if tl == 'section':
                sec_num += 1
                item_num = 0
                self.tv.insert("", "end", iid=str(i), tags=("section",),
                    values=(str(sec_num), l.get('designation','').upper(), "", "", "", ""))
            elif tl == 'subtotal':
                self.tv.insert("", "end", iid=str(i), tags=("subtotal",),
                    values=("Σ", l.get('designation','Sous-total'), "", "", "",
                            f"{int(mont):,}".replace(',',' ')))
            elif tl == 'comment':
                self.tv.insert("", "end", iid=str(i), tags=("comment",),
                    values=("💬", l.get('designation',''), "", "", "", ""))
            else:
                item_num += 1
                num = f"{sec_num}.{item_num}" if sec_num else str(item_num)
                qte = float(l.get('quantite', 0) or 0)
                pu = float(l.get('prix_unitaire', 0) or 0)
                qs = str(int(qte)) if qte == int(qte) else f"{qte:.2f}"
                tag = "pair" if item_num%2 else "impair"
                self.tv.insert("", "end", iid=str(i), tags=(tag,),
                    values=(num, l.get('designation',''), l.get('unite',''), qs,
                            f"{int(pu):,}".replace(',',' '),
                            f"{int(mont):,}".replace(',',' ')))
        self._recalc()

    def _recalc(self):
        ht = sum(float(l.get('montant',0) or 0)
                 for l in self.lignes if l.get('type_ligne','item') == 'item')
        try:
            tva_t = float(self._vars['tva_taux'].get() or 0)
        except:
            tva_t = 0
        tva = ht * tva_t / 100
        ttc = ht + tva
        self.lbl_ht.config(text=fmt_fcfa(ht))
        self.lbl_tva.config(text=f"({tva_t:.0f}%)  "+fmt_fcfa(tva))
        self.lbl_ttc.config(text=fmt_fcfa(ttc))

    def _sel(self):
        sel = self.tv.selection()
        return int(sel[0]) if sel else None

    def _add(self, tl):
        LigneEditor(self, tl, None, self._on_ligne)

    def _edit_ligne(self):
        idx = self._sel()
        if idx is None:
            return
        LigneEditor(self, self.lignes[idx].get('type_ligne','item'),
                    self.lignes[idx], self._on_ligne, idx=idx)

    def _on_ligne(self, data, idx=None):
        if idx is None:
            self.lignes.append(data)
        else:
            self.lignes[idx] = data
        self._refresh()
        try:
            t = len(self.lignes)-1 if idx is None else idx
            self.tv.selection_set(str(t))
            self.tv.see(str(t))
        except:
            pass

    def _del_ligne(self):
        idx = self._sel()
        if idx is None:
            messagebox.showinfo("Information", "Veuillez sélectionner une ligne.")
            return
        self.lignes.pop(idx)
        self._refresh()

    def _move(self, delta):
        idx = self._sel()
        if idx is None:
            return
        new = idx + delta
        if 0 <= new < len(self.lignes):
            self.lignes[idx], self.lignes[new] = self.lignes[new], self.lignes[idx]
            self._refresh()
            try:
                self.tv.selection_set(str(new))
                self.tv.see(str(new))
            except:
                pass

    def _catalog(self):
        CatalogPicker(self, lambda arts: [
            self._on_ligne({'type_ligne':'item', 'designation':a['designation'],
                            'unite':a.get('unite','U'), 'quantite':1,
                            'prix_unitaire':a.get('prix_unitaire',0),
                            'montant':a.get('prix_unitaire',0)})
            for a in arts])

    def _pick_client(self):
        ClientPicker(self, lambda c: (self.client_id.set(c['id']), self.client_nom.set(c['nom'])))

    def _new_client(self):
        ClientEditor(self, None, on_save=lambda c: (self.client_id.set(c.get('id') or 0),
                                                    self.client_nom.set(c.get('nom',''))))

    def _save(self):
        num = self._vars.get('numero', tk.StringVar()).get().strip()
        if not num:
            messagebox.showwarning("Attention", "Le numéro de devis est obligatoire.")
            return
        try:
            tva_t = float(self._vars['tva_taux'].get() or 0)
        except:
            tva_t = 0
        ht = sum(float(l.get('montant',0) or 0)
                 for l in self.lignes if l.get('type_ligne','item') == 'item')
        tva = ht * tva_t / 100
        ttc = ht + tva
        data = {
            'id': self.did,
            'numero': num,
            'date_creation': self._vars.get('date_creation', tk.StringVar()).get() or today_str(),
            'date_validite': self._vars.get('date_validite', tk.StringVar()).get(),
            'client_id': self.client_id.get() or None,
            'chantier': self._vars.get('chantier', tk.StringVar()).get(),
            'localisation': self._vars.get('localisation', tk.StringVar()).get(),
            'description': self.desc_text.get("1.0", "end-1c"),
            'statut': self._vars.get('statut', tk.StringVar(value='Brouillon')).get(),
            'tva_taux': tva_t,
            'montant_ht': ht,
            'montant_tva': tva,
            'montant_ttc': ttc,
            'delai_execution': self._vars.get('delai_execution', tk.StringVar()).get(),
            'conditions_reglement': self.cond_text.get("1.0", "end-1c"),
            'notes': self.notes_text.get("1.0", "end-1c")
        }
        self.did = db.save_devis(data, self.lignes)
        if self.on_save:
            self.on_save()
        orig = self.title()
        self.title("Devis enregistré !")
        self.after(1800, lambda: self.title(orig))

    def _pdf(self):
        self._save()
        if not self.did:
            return
        devis, lignes = db.get_devis(self.did)
        ent = db.get_entreprise()
        out_dir = Path(db.APP_DIR) / "PDF"
        out_dir.mkdir(exist_ok=True)
        out = str(out_dir / f"{devis['numero']}.pdf")
        try:
            generate_devis_pdf(devis, lignes, ent, out)
            if sys.platform == "win32":
                os.startfile(out)
            else:
                os.system(f'xdg-open "{out}" &')
        except Exception as e:
            messagebox.showerror("Erreur PDF", str(e))

# ═══════════════════════════════════════════════════════════════════
#  LIGNE EDITOR, CATALOG PICKER, CLIENT PICKER, DETAIL VIEWS
# ═══════════════════════════════════════════════════════════════════
class LigneEditor(tk.Toplevel):
    NOMS = {'item':'Prestation','section':'Section','subtotal':'Sous-total','comment':'Commentaire'}
    def __init__(self, parent, tl, data, callback, idx=None):
        super().__init__(parent)
        self.callback = callback
        self.idx = idx
        self.tl = tl
        self.data = data or {}
        self.title(f"Modifier : {self.NOMS.get(tl,tl)}")
        self.resizable(False, False)
        self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        self._build()

    def _build(self):
        colors = {'item':C_SUCCESS, 'section':C_PRIMARY, 'subtotal':C_ACCENT, 'comment':C_GRAY}
        hdr = tk.Frame(self, bg=colors.get(self.tl, C_PRIMARY), relief="raised", bd=2)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"  {self.NOMS.get(self.tl,self.tl)}", font=FT_H2,
                 fg=C_LIGHT, bg=colors.get(self.tl, C_PRIMARY), anchor="w", pady=8, padx=12).pack()
        body = RidgePanel(self, bg=BG_CARD, bd=1)
        body.pack(padx=15, pady=10, fill="x")

        def row(label, widget):
            f = tk.Frame(body, bg=BG_CARD)
            f.pack(fill="x", padx=12, pady=5)
            tk.Label(f, text=label, font=FT_NORM, fg=C_GRAY, bg=BG_CARD,
                     width=18, anchor="w").pack(side="left")
            widget.pack(side="left", fill="x", expand=True)

        self.desig_var = tk.StringVar(value=self.data.get('designation',''))
        row("Désignation :", SunkenEntry(body, textvariable=self.desig_var, width=42))

        if self.tl == 'item':
            self.unite_var = tk.StringVar(value=self.data.get('unite','U'))
            self.qte_var = tk.StringVar(value=str(self.data.get('quantite',1)))
            self.pu_var = tk.StringVar(value=str(self.data.get('prix_unitaire',0)))
            self.montant_var = tk.StringVar(value=str(self.data.get('montant',0)))
            row("Unité :", ttk.Combobox(body, textvariable=self.unite_var,
                values=["U","ml","m²","m³","kg","t","h","j","forfait","lot"],
                width=12, font=FT_NORM, state="normal"))
            row("Quantité :", SunkenEntry(body, textvariable=self.qte_var, width=16))
            row("Prix unitaire (FCFA) :", SunkenEntry(body, textvariable=self.pu_var, width=20))
            mf = tk.Frame(body, bg=BG_CARD)
            mf.pack(fill="x", padx=12, pady=5)
            tk.Label(mf, text="Montant calculé :", font=FT_NORM, fg=C_GRAY,
                     bg=BG_CARD, width=18, anchor="w").pack(side="left")
            tk.Label(mf, textvariable=self.montant_var, font=("Segoe UI", 11, "bold"),
                     fg=C_PRIMARY, bg=BG_STR, relief="groove", bd=1, padx=10, pady=4
                     ).pack(side="left")
            self.qte_var.trace_add("write", lambda *a: self._calc())
            self.pu_var.trace_add("write", lambda *a: self._calc())

        btn_frame = tk.Frame(self, bg=BG_APP, relief="groove", bd=1)
        btn_frame.pack(fill="x", padx=15, pady=(0,12))
        ModernButton(btn_frame, "Valider", self._ok, bg=C_SUCCESS, font=FT_NORM
                     ).pack(side="right", padx=8, pady=8)
        ModernButton(btn_frame, "Annuler", self.destroy, bg=C_GRAY, font=FT_NORM
                     ).pack(side="right", padx=4, pady=8)

    def _calc(self):
        try:
            q = float(self.qte_var.get() or 0)
            pu = float(self.pu_var.get() or 0)
            self.montant_var.set(f"{int(q*pu):,}".replace(',',' '))
        except:
            pass

    def _ok(self):
        data = {'type_ligne': self.tl, 'designation': self.desig_var.get()}
        if self.tl == 'item':
            try:
                q = float(self.qte_var.get() or 0)
            except:
                q = 0
            try:
                pu = float(self.pu_var.get() or 0)
            except:
                pu = 0
            data.update({
                'unite': self.unite_var.get(),
                'quantite': q,
                'prix_unitaire': pu,
                'montant': q * pu
            })
        self.callback(data, self.idx)
        self.destroy()

class CatalogPicker(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.articles = []
        self.title("Catalogue des Articles")
        self.geometry("860x580")
        self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        self._build()
        self._load()

    def _build(self):
        hdr = tk.Frame(self, bg=C_PRIMARY, relief="raised", bd=2)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Choisir depuis le catalogue", font=FT_H2,
                 fg=C_LIGHT, bg=C_PRIMARY, anchor="w", pady=10, padx=15).pack()
        filt = GrooveBox(self, bg=BG_CARD, bd=1)
        filt.pack(fill="x", padx=10, pady=8)
        tk.Label(filt, text="Recherche :", font=FT_NORM, fg=C_GRAY, bg=BG_CARD
                 ).pack(side="left", padx=(10,5), pady=8)
        self.search_var = tk.StringVar()
        search_entry = SunkenEntry(filt, textvariable=self.search_var, width=25)
        search_entry.pack(side="left", padx=5)
        search_entry.bind("<Return>", lambda e: self._load())
        self.cat_var = tk.StringVar(value="Toutes")
        cats = ["Toutes"] + db.get_categories_articles()
        ttk.Combobox(filt, values=cats, textvariable=self.cat_var,
                     width=24, font=FT_NORM, state="readonly").pack(side="left", padx=5)
        ModernButton(filt, "Rechercher", self._load, bg=C_PRIMARY, pady=3
                     ).pack(side="left", padx=5)

        tree_frame = RidgePanel(self, bg=BG_CARD, bd=1)
        tree_frame.pack(fill="both", expand=True, padx=10)
        self.tree = create_tree(tree_frame,
            ("cat","desig","unite","pu"),
            ("Catégorie","Désignation","Unité","Prix Unitaire (FCFA)"),
            [150,370,65,150])
        scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)

        bottom = GrooveBox(self, bg=BG_APP, bd=1)
        bottom.pack(fill="x", padx=10, pady=8)
        tk.Label(bottom, text="Ctrl+clic : sélection multiple", font=FT_SMALL,
                 fg=C_GRAY, bg=BG_APP).pack(side="left", padx=10)
        ModernButton(bottom, "Ajouter la sélection", self._pick, bg=C_SUCCESS, font=FT_NORM
                     ).pack(side="right", padx=8, pady=6)
        ModernButton(bottom, "Fermer", self.destroy, bg=C_GRAY, font=FT_NORM
                     ).pack(side="right", padx=4, pady=6)

    def _load(self, *args):
        self.articles = db.get_articles(self.search_var.get(), self.cat_var.get())
        fill_tree(self.tree,
            [(a['categorie'], a['designation'], a['unite'], fmt_fcfa(a['prix_unitaire']))
             for a in self.articles])

    def _pick(self):
        sels = self.tree.selection()
        if not sels:
            messagebox.showinfo("Information", "Veuillez sélectionner au moins un article.")
            return
        selected = [self.articles[self.tree.index(s)] for s in sels]
        self.callback(selected)
        self.destroy()

class ClientPicker(tk.Toplevel):
    def __init__(self, parent, callback):
        super().__init__(parent)
        self.callback = callback
        self.clients = []
        self.title("Choisir un client")
        self.geometry("580x420")
        self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        self._build()
        self._load()

    def _build(self):
        hdr = tk.Frame(self, bg=C_ACCENT, relief="raised", bd=2)
        hdr.pack(fill="x")
        tk.Label(hdr, text="Sélectionner un client", font=FT_H2,
                 fg=C_LIGHT, bg=C_ACCENT, anchor="w", pady=10, padx=15).pack()
        filt = GrooveBox(self, bg=BG_CARD, bd=1)
        filt.pack(fill="x", padx=10, pady=8)
        self.search_var = tk.StringVar()
        search_entry = SunkenEntry(filt, textvariable=self.search_var, width=30)
        search_entry.pack(side="left", padx=(10,6), pady=8)
        search_entry.bind("<Return>", lambda e: self._load())
        ModernButton(filt, "Rechercher", self._load, bg=C_PRIMARY, pady=3).pack(side="left")
        tree_frame = RidgePanel(self, bg=BG_CARD, bd=1)
        tree_frame.pack(fill="both", expand=True, padx=10)
        self.tree = create_tree(tree_frame,
            ("nom","type","ville","tel"),
            ("Nom / Raison sociale","Type","Ville","Téléphone"),
            [215,110,115,125])
        scroll = ttk.Scrollbar(tree_frame, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self._pick())
        bottom = GrooveBox(self, bg=BG_APP, bd=1)
        bottom.pack(fill="x", padx=10, pady=8)
        ModernButton(bottom, "Sélectionner", self._pick, bg=C_SUCCESS, font=FT_NORM
                     ).pack(side="right", padx=8, pady=6)
        ModernButton(bottom, "Fermer", self.destroy, bg=C_GRAY, font=FT_NORM
                     ).pack(side="right", padx=4, pady=6)

    def _load(self, *args):
        self.clients = db.get_clients(self.search_var.get())
        fill_tree(self.tree,
            [(c['nom'], c.get('type_client',''), c['ville'], c['telephone'])
             for c in self.clients])

    def _pick(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Information", "Veuillez sélectionner un client.")
            return
        self.callback(self.clients[self.tree.index(sel[0])])
        self.destroy()

class DevisDetailView(tk.Toplevel):
    def __init__(self, parent, did, on_edit=None):
        super().__init__(parent)
        self.did = did
        self.on_edit = on_edit
        self.title("Détail du Devis")
        self.geometry("1020x720")
        self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        devis, lignes = db.get_devis(did)
        if not devis:
            self.destroy()
            return
        self._build(devis, lignes)

    def _build(self, d, lignes):
        hdr = tk.Frame(self, bg=C_PRIMARY, relief="raised", bd=2)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"Devis  {d['numero']}", font=FT_TITLE,
                 fg=C_LIGHT, bg=C_PRIMARY, anchor="w", pady=10, padx=15).pack(side="left")
        def edit_close():
            self.destroy()
            DevisEditor(self.master, None, did=self.did, on_save=self.on_edit)
        ModernButton(hdr, "Modifier", edit_close, bg=C_PRIMARY, pady=3
                     ).pack(side="right", padx=5, pady=5)
        ModernButton(hdr, "Générer PDF", self._pdf, bg=C_ACCENT, pady=3
                     ).pack(side="right", padx=5, pady=5)
        ModernButton(hdr, "Fermer", self.destroy, bg=C_GRAY, pady=3
                     ).pack(side="right", padx=5, pady=5)

        colors_st = {'Accepté':'#E8F5E9','Envoyé':'#E3F2FD','Facturé':'#F3E5F5',
                     'Refusé':'#FFEBEE','Brouillon':'#FFF9C4'}
        fg_st = {'Accepté':C_SUCCESS,'Envoyé':C_PRIMARY,'Facturé':'#6A1B9A',
                 'Refusé':C_DANGER,'Brouillon':C_ACCENT}
        st = d.get('statut','Brouillon')
        tk.Label(self, text=f"Statut : {st}", font=FT_H3,
                 bg=colors_st.get(st,'#F5F5F5'), fg=fg_st.get(st,C_DARK),
                 relief="ridge", bd=1).pack(anchor="e", padx=15, pady=5)

        scroll = ScrollFrame(self, bg=BG_APP)
        scroll.pack(fill="both", expand=True)
        p = scroll.inner

        def info_card(titre, rows, color=C_PRIMARY):
            section_header(p, titre, bg=color)
            card = RidgePanel(p, bg=BG_CARD, bd=1)
            card.pack(fill="x", padx=10, pady=5)
            for lbl, val in rows:
                f = tk.Frame(card, bg=BG_CARD)
                f.pack(fill="x", padx=12, pady=3)
                tk.Label(f, text=lbl, font=FT_SMALL, fg=C_GRAY, bg=BG_CARD,
                         width=22, anchor="w").pack(side="left")
                tk.Label(f, text=str(val) if val else "—", font=FT_NORM,
                         fg=C_DARK, bg=BG_CARD, anchor="w", wraplength=500
                         ).pack(side="left", fill="x")
            tk.Frame(card, height=4, bg=BG_CARD).pack()

        def fdate(s):
            try:
                return datetime.strptime(s, "%Y-%m-%d").strftime("%d/%m/%Y")
            except:
                return s or "—"

        two = tk.Frame(p, bg=BG_APP)
        two.pack(fill="x", padx=10, pady=(5,0))
        two.columnconfigure(0, weight=1)
        two.columnconfigure(1, weight=1)

        def col_card(parent, col, titre, rows, color=C_PRIMARY):
            f = tk.Frame(parent, bg=BG_APP)
            f.grid(row=0, column=col, sticky="nsew", padx=(0,5) if col==0 else (5,0))
            section_header(f, titre, bg=color)
            card = RidgePanel(f, bg=BG_CARD, bd=1)
            card.pack(fill="both", expand=True)
            for lbl, val in rows:
                rf = tk.Frame(card, bg=BG_CARD)
                rf.pack(fill="x", padx=12, pady=3)
                tk.Label(rf, text=lbl, font=FT_SMALL, fg=C_GRAY, bg=BG_CARD,
                         width=18, anchor="w").pack(side="left")
                tk.Label(rf, text=str(val) if val else "—", font=FT_NORM,
                         fg=C_DARK, bg=BG_CARD, anchor="w").pack(side="left")
            tk.Frame(card, height=4, bg=BG_CARD).pack()

        col_card(two, 0, "Informations Devis", [
            ("N° Devis :", d.get('numero','')),
            ("Date création :", fdate(d.get('date_creation',''))),
            ("Date validité :", fdate(d.get('date_validite',''))),
            ("Statut :", d.get('statut','')),
            ("Chantier :", d.get('chantier','')),
            ("Localisation :", d.get('localisation','')),
            ("Délai exécution :", d.get('delai_execution','')),
            ("TVA :", f"{d.get('tva_taux',0):.0f} %"),
        ])
        col_card(two, 1, "Client / Maître d'ouvrage", [
            ("Nom :", d.get('client_nom','')),
            ("Adresse :", d.get('client_adresse','')),
            ("Ville :", d.get('client_ville','')),
            ("Téléphone :", d.get('client_tel','')),
            ("Email :", d.get('client_email','')),
            ("NIF :", d.get('client_nif','')),
        ], color=C_ACCENT)

        if d.get('description'):
            section_header(p, "Description des travaux")
            dc = RidgePanel(p, bg=BG_CARD, bd=1)
            dc.pack(fill="x", padx=10, pady=5)
            tk.Label(dc, text=d['description'], font=FT_NORM, fg=C_DARK, bg=BG_CARD,
                     anchor="w", justify="left", padx=15, pady=8, wraplength=900
                     ).pack(fill="x")

        section_header(p, "Détail des Prestations")
        table_frame = RidgePanel(p, bg=BG_CARD, bd=1)
        table_frame.pack(fill="x", padx=10, pady=5)
        tv = create_tree(table_frame,
            ("num","desig","unite","qte","pu","mont"),
            ("N°","Désignation","Unité","Quantité","Prix U. (FCFA)","Montant (FCFA)"),
            [38,370,65,72,128,128], height=min(len(lignes)+2,14))
        tv.column("pu", anchor="e")
        tv.column("mont", anchor="e")
        tv.column("num", anchor="center")
        tv.column("unite", anchor="center")
        tv.column("qte", anchor="center")
        scroll = ttk.Scrollbar(table_frame, command=tv.yview)
        tv.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        tv.pack(side="left", fill="x", expand=True)

        sec_num = 0
        item_num = 0
        for l in lignes:
            tl = l.get('type_ligne','item')
            mont = float(l.get('montant',0) or 0)
            if tl == 'section':
                sec_num += 1
                item_num = 0
                tv.insert("", "end", tags=("section",),
                    values=(str(sec_num), l.get('designation','').upper(), "", "", "", ""))
            elif tl == 'subtotal':
                tv.insert("", "end", tags=("subtotal",),
                    values=("Σ", l.get('designation','Sous-total'), "", "", "",
                            f"{int(mont):,}".replace(',',' ')))
            elif tl == 'comment':
                tv.insert("", "end", tags=("comment",),
                    values=("💬", l.get('designation',''), "", "", "", ""))
            else:
                item_num += 1
                num = f"{sec_num}.{item_num}" if sec_num else str(item_num)
                qte = float(l.get('quantite',0) or 0)
                pu = float(l.get('prix_unitaire',0) or 0)
                qs = str(int(qte)) if qte==int(qte) else f"{qte:.2f}"
                tv.insert("", "end", tags=("impair" if item_num%2 else "pair",),
                    values=(num, l.get('designation',''), l.get('unite',''), qs,
                            f"{int(pu):,}".replace(',',' '),
                            f"{int(mont):,}".replace(',',' ')))

        ht = float(d.get('montant_ht',0) or 0)
        tva = float(d.get('montant_tva',0) or 0)
        ttc = float(d.get('montant_ttc',0) or 0)
        tva_t = float(d.get('tva_taux',0) or 0)

        total_frame = tk.Frame(p, bg=BG_APP)
        total_frame.pack(anchor="e", padx=10, pady=10)
        for lbl, val, bold, bg in [
            ("Montant HT :", fmt_fcfa(ht), False, BG_STR),
            (f"TVA ({tva_t:.0f}%) :", fmt_fcfa(tva), False, BG_STR),
            ("TOTAL TTC :", fmt_fcfa(ttc), True, C_PRIMARY),
        ]:
            row = tk.Frame(total_frame, bg=bg, relief="ridge" if bold else "groove", bd=2 if bold else 1)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=lbl, font=FT_NORM if not bold else FT_H3,
                     fg=C_LIGHT if bold else C_GRAY, bg=bg,
                     width=20, anchor="e", padx=8, pady=5).pack(side="left")
            tk.Label(row, text=val, font=FT_NORM if not bold else ("Segoe UI", 11, "bold"),
                     fg=C_LIGHT if bold else C_DARK, bg=bg, anchor="e", padx=12, pady=5
                     ).pack(side="right")

        for titre, val in [("Conditions de règlement", d.get('conditions_reglement','')),
                           ("Notes internes", d.get('notes',''))]:
            if val and val.strip():
                section_header(p, titre, bg=C_GRAY)
                vc = RidgePanel(p, bg=BG_CARD, bd=1)
                vc.pack(fill="x", padx=10, pady=5)
                tk.Label(vc, text=val, font=FT_NORM, fg=C_DARK, bg=BG_CARD,
                         anchor="w", justify="left", padx=15, pady=8, wraplength=900
                         ).pack(fill="x")

    def _pdf(self):
        devis, lignes = db.get_devis(self.did)
        ent = db.get_entreprise()
        out_dir = Path(db.APP_DIR) / "PDF"
        out_dir.mkdir(exist_ok=True)
        out = str(out_dir / f"{devis['numero']}.pdf")
        try:
            generate_devis_pdf(devis, lignes, ent, out)
            if sys.platform == "win32":
                os.startfile(out)
            else:
                os.system(f'xdg-open "{out}" &')
        except Exception as e:
            messagebox.showerror("Erreur PDF", str(e))

class ClientDetailView(tk.Toplevel):
    def __init__(self, parent, cid, on_edit=None):
        super().__init__(parent)
        self.cid = cid
        self.on_edit = on_edit
        self.title("Détail du Client")
        self.geometry("820x620")
        self.configure(bg=BG_APP)
        self.update_idletasks()
        self.grab_set()
        client = db.get_client(cid)
        if not client:
            self.destroy()
            return
        self._build(client)

    def _build(self, c):
        type_colors = {'Particulier':C_PRIMARY, 'Entreprise':C_ACCENT,
                       'Administration':C_SUCCESS, 'ONG':'#6A1B9A'}
        tc = type_colors.get(c.get('type_client',''), C_PRIMARY)
        hdr = tk.Frame(self, bg=tc, relief="raised", bd=2)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"{c['nom']}", font=FT_TITLE,
                 fg=C_LIGHT, bg=tc, anchor="w", pady=10, padx=15).pack(side="left")
        def edit_close():
            self.destroy()
            ClientEditor(self.master, self.cid, on_save=self.on_edit)
        ModernButton(hdr, "Modifier", edit_close, bg=C_PRIMARY, pady=3
                     ).pack(side="right", padx=5, pady=5)
        ModernButton(hdr, "Fermer", self.destroy, bg=C_GRAY, pady=3
                     ).pack(side="right", padx=5, pady=5)
        tk.Label(self, text=f"  {c.get('type_client','Inconnu')}  ", font=FT_H3,
                 fg=C_LIGHT, bg=tc, relief="ridge", bd=1
                 ).pack(anchor="e", padx=15, pady=5)

        scroll = ScrollFrame(self, bg=BG_APP)
        scroll.pack(fill="both", expand=True)
        p = scroll.inner

        section_header(p, "Fiche Identité", bg=tc)
        id_card = RidgePanel(p, bg=BG_CARD, bd=1)
        id_card.pack(fill="x", padx=10, pady=5)
        id_card.columnconfigure(1, weight=1)
        id_card.columnconfigure(3, weight=1)
        infos = [
            ("Nom / Raison sociale :", c.get('nom',''), 0, 0),
            ("Type de client :", c.get('type_client',''), 1, 0),
            ("NIF :", c.get('nif','') or "—", 1, 1),
        ]
        for lbl, val, r, col in infos:
            lc = col*2
            tk.Label(id_card, text=lbl, font=FT_SMALL, fg=C_GRAY, bg=BG_CARD,
                     anchor="w").grid(row=r, column=lc, sticky="w", padx=(12,4), pady=5)
            tk.Label(id_card, text=str(val) if val else "—",
                     font=FT_NORM if lbl!="Nom / Raison sociale :" else ("Segoe UI", 10, "bold"),
                     fg=tc if lbl=="Nom / Raison sociale :" else C_DARK, bg=BG_CARD,
                     anchor="w").grid(row=r, column=lc+1, sticky="w", padx=(0,12), pady=5)
        tk.Frame(id_card, height=4, bg=BG_CARD).grid(row=10, column=0)

        section_header(p, "Adresse / Localisation", bg=C_ACCENT)
        ac = RidgePanel(p, bg=BG_CARD, bd=1)
        ac.pack(fill="x", padx=10, pady=5)
        for lbl, val in [("Adresse :", c.get('adresse','')),
                         ("Quartier :", c.get('quartier','')),
                         ("Ville :", c.get('ville',''))]:
            af = tk.Frame(ac, bg=BG_CARD)
            af.pack(fill="x", padx=12, pady=3)
            tk.Label(af, text=lbl, font=FT_SMALL, fg=C_GRAY, bg=BG_CARD,
                     width=16, anchor="w").pack(side="left")
            tk.Label(af, text=str(val) if val else "—", font=FT_NORM,
                     fg=C_DARK, bg=BG_CARD).pack(side="left")
        tk.Frame(ac, height=4, bg=BG_CARD).pack()

        section_header(p, "Contacts", bg=C_SUCCESS)
        cc = RidgePanel(p, bg=BG_CARD, bd=1)
        cc.pack(fill="x", padx=10, pady=5)
        for lbl, val in [("Téléphone :", c.get('telephone','')),
                         ("Email :", c.get('email',''))]:
            cf = tk.Frame(cc, bg=BG_CARD)
            cf.pack(fill="x", padx=12, pady=3)
            tk.Label(cf, text=lbl, font=FT_SMALL, fg=C_GRAY, bg=BG_CARD,
                     width=16, anchor="w").pack(side="left")
            tk.Label(cf, text=str(val) if val else "—", font=FT_NORM,
                     fg=C_PRIMARY, bg=BG_CARD).pack(side="left")
        tk.Frame(cc, height=4, bg=BG_CARD).pack()

        devis_client = [d for d in db.get_devis_list() if d.get('client_id') == self.cid]
        section_header(p, f"Devis associés  ({len(devis_client)} devis)")
        if devis_client:
            tf = RidgePanel(p, bg=BG_CARD, bd=1)
            tf.pack(fill="x", padx=10, pady=5)
            tv = create_tree(tf,
                ("num","date","chantier","ht","ttc","statut"),
                ("N° Devis","Date","Chantier / Objet","HT","TTC","Statut"),
                [108,88,240,125,135,88], height=min(len(devis_client)+1,8))
            tv.column("ht", anchor="e")
            tv.column("ttc", anchor="e")
            tv.pack(fill="x", padx=4, pady=4)
            fill_tree(tv, [(d['numero'], d['date_creation'],
                            d.get('chantier','')[:35],
                            fmt_fcfa(d['montant_ht']),
                            fmt_fcfa(d['montant_ttc']),
                            d['statut']) for d in devis_client])

            def open_linked(event, tv=tv, dl=devis_client):
                sel = tv.selection()
                if not sel:
                    return
                idx = tv.index(sel[0])
                DevisDetailView(self, dl[idx]['id'])
            tv.bind("<Double-1>", open_linked)

            total_ttc = sum(float(d.get('montant_ttc',0) or 0) for d in devis_client)
            total_acc = sum(float(d.get('montant_ttc',0) or 0)
                           for d in devis_client if d['statut'] in ('Accepté','Facturé'))
            tf2 = tk.Frame(p, bg=BG_APP)
            tf2.pack(anchor="e", padx=10, pady=5)
            for lbl, val, bg in [
                ("Total devis (tous statuts) :", fmt_fcfa(total_ttc), BG_STR),
                ("Total acceptés + facturés :", fmt_fcfa(total_acc), "#E8F5E9"),
            ]:
                rf = tk.Frame(tf2, bg=bg, relief="groove", bd=1)
                rf.pack(fill="x", pady=2)
                tk.Label(rf, text=lbl, font=FT_SMALL, fg=C_GRAY,
                         bg=bg, width=28, anchor="e", padx=8, pady=5).pack(side="left")
                tk.Label(rf, text=val, font=FT_NORM, fg=C_SUCCESS,
                         bg=bg, padx=12).pack(side="right")
        else:
            nc = RidgePanel(p, bg=BG_CARD, bd=1)
            nc.pack(fill="x", padx=10, pady=5)
            tk.Label(nc, text="Aucun devis pour ce client.", font=FT_NORM,
                     fg=C_GRAY_L, bg=BG_CARD, pady=14).pack()
        tk.Frame(p, height=12, bg=BG_APP).pack()

# ═══════════════════════════════════════════════════════════════════
#  INJECTION DES MÉTHODES POUR DOUBLE-CLIC
# ═══════════════════════════════════════════════════════════════════
def _devis_detail_patch(self):
    did = self._selected_id()
    if not did:
        return
    DevisDetailView(self, did, on_edit=lambda: self.refresh())

def _client_detail_patch(self):
    cid = self._selected_id()
    if not cid:
        return
    ClientDetailView(self, cid, on_edit=lambda: self.refresh())

DevisPage._detail = _devis_detail_patch
ClientsPage._detail_client = _client_detail_patch

# ═══════════════════════════════════════════════════════════════════
#  LANCEMENT
# ═══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = App()
    app.mainloop()
