"""
db.py - Couche base de données SQLite pour DevisBTP
TVA par défaut : 0%
"""
import sqlite3
import os
import shutil
from pathlib import Path
from datetime import datetime, date

# Dossiers de l'application
APP_DIR = Path.home() / "DevisBTP"
DB_PATH  = APP_DIR / "devis_btp.db"
MEDIA_DIR = APP_DIR / "media"

def get_app_dir():
    APP_DIR.mkdir(exist_ok=True)
    MEDIA_DIR.mkdir(exist_ok=True)
    return APP_DIR

def get_conn():
    get_app_dir()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ─────────────────────────────────────────
#  INITIALISATION
# ─────────────────────────────────────────
def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS entreprise (
        id              INTEGER PRIMARY KEY,
        nom             TEXT    DEFAULT '',
        sigle           TEXT    DEFAULT '',
        forme_juridique TEXT    DEFAULT '',
        adresse         TEXT    DEFAULT '',
        quartier        TEXT    DEFAULT '',
        ville           TEXT    DEFAULT 'Lomé',
        pays            TEXT    DEFAULT 'Togo',
        telephone1      TEXT    DEFAULT '',
        telephone2      TEXT    DEFAULT '',
        email           TEXT    DEFAULT '',
        site_web        TEXT    DEFAULT '',
        rccm            TEXT    DEFAULT '',
        nif             TEXT    DEFAULT '',
        logo_path       TEXT    DEFAULT '',
        tva_taux        REAL    DEFAULT 0.0,
        rib             TEXT    DEFAULT '',
        banque          TEXT    DEFAULT '',
        slogan          TEXT    DEFAULT '',
        conditions_def  TEXT    DEFAULT 'Paiement à 30 jours à compter de la date de facturation.',
        delai_def       TEXT    DEFAULT ''
    );

    CREATE TABLE IF NOT EXISTS clients (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        nom         TEXT    NOT NULL,
        adresse     TEXT    DEFAULT '',
        quartier    TEXT    DEFAULT '',
        ville       TEXT    DEFAULT 'Lomé',
        telephone   TEXT    DEFAULT '',
        email       TEXT    DEFAULT '',
        type_client TEXT    DEFAULT 'Particulier',
        nif         TEXT    DEFAULT '',
        created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS devis (
        id                   INTEGER PRIMARY KEY AUTOINCREMENT,
        numero               TEXT    UNIQUE NOT NULL,
        date_creation        TEXT    NOT NULL,
        date_validite        TEXT    DEFAULT '',
        client_id            INTEGER,
        chantier             TEXT    DEFAULT '',
        localisation         TEXT    DEFAULT '',
        description          TEXT    DEFAULT '',
        statut               TEXT    DEFAULT 'Brouillon',
        montant_ht           REAL    DEFAULT 0,
        tva_taux             REAL    DEFAULT 0.0,
        montant_tva          REAL    DEFAULT 0,
        montant_ttc          REAL    DEFAULT 0,
        conditions_reglement TEXT    DEFAULT '',
        delai_execution      TEXT    DEFAULT '',
        notes                TEXT    DEFAULT '',
        created_at           TEXT    DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES clients(id)
    );

    CREATE TABLE IF NOT EXISTS devis_lignes (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        devis_id      INTEGER NOT NULL,
        ordre         INTEGER DEFAULT 0,
        type_ligne    TEXT    DEFAULT 'item',
        designation   TEXT    DEFAULT '',
        unite         TEXT    DEFAULT '',
        quantite      REAL    DEFAULT 1,
        prix_unitaire REAL    DEFAULT 0,
        montant       REAL    DEFAULT 0,
        FOREIGN KEY (devis_id) REFERENCES devis(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS articles (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        categorie     TEXT    DEFAULT 'Général',
        designation   TEXT    NOT NULL,
        unite         TEXT    DEFAULT 'U',
        prix_unitaire REAL    DEFAULT 0,
        description   TEXT    DEFAULT ''
    );
    """)

    # Entreprise par défaut (TVA = 0)
    c.execute("SELECT COUNT(*) FROM entreprise")
    if c.fetchone()[0] == 0:
        c.execute("""INSERT INTO entreprise (nom, ville, pays, tva_taux)
                     VALUES ('Mon Entreprise BTP', 'Lomé', 'Togo', 0.0)""")

    # Articles pré-définis (inchangés)
    c.execute("SELECT COUNT(*) FROM articles")
    if c.fetchone()[0] == 0:
        articles = [
            # Terrassement
            ('Terrassement', 'Décapage et débroussaillage',          'm²',    500),
            ('Terrassement', 'Terrassement général en déblai',        'm³',   3500),
            ('Terrassement', 'Remblai compacté (matériaux sélect.)', 'm³',   4500),
            ('Terrassement', 'Fouille en rigole pour fondation',      'm³',   5000),
            ('Terrassement', 'Fouilles en puits',                     'm³',   7500),
            ('Terrassement', 'Nivellement et compactage',             'm²',   1000),
            # Béton / Maçonnerie
            ('Béton / Maçonnerie', 'Béton de propreté dosé 150 kg/m³',          'm³',  85000),
            ('Béton / Maçonnerie', 'Béton armé dosé 350 kg/m³ (semelles)',       'm³', 195000),
            ('Béton / Maçonnerie', 'Béton armé dosé 350 kg/m³ (dalles/poutres)','m³', 215000),
            ('Béton / Maçonnerie', 'Béton armé dosé 350 kg/m³ (poteaux)',        'm³', 230000),
            ('Béton / Maçonnerie', 'Longrine / Poutre de ceinture',              'm³', 220000),
            ('Béton / Maçonnerie', 'Parpaings creux 15 cm (mur de clôture)',     'm²',  12000),
            ('Béton / Maçonnerie', 'Parpaings creux 15 cm (cloison intérieure)', 'm²',  14000),
            ('Béton / Maçonnerie', 'Parpaings creux 20 cm (mur extérieur)',      'm²',  17000),
            ('Béton / Maçonnerie', 'Briques pleines',                            'm²',  10000),
            ('Béton / Maçonnerie', 'Enduit ciment intérieur (1,5 cm)',            'm²',   4500),
            ('Béton / Maçonnerie', 'Enduit ciment extérieur (2 cm)',              'm²',   5500),
            ('Béton / Maçonnerie', 'Chape ciment (4 cm)',                         'm²',   6000),
            # Charpente / Couverture
            ('Charpente / Couverture', 'Charpente bois traité',            'm²',  18000),
            ('Charpente / Couverture', 'Tôle bac acier galvanisée 6/10',  'm²',   9500),
            ('Charpente / Couverture', 'Tôle ondulée galvanisée',          'm²',   6500),
            ('Charpente / Couverture', 'Faîtière',                         'ml',   2500),
            ('Charpente / Couverture', 'Bavette aluminium',                 'ml',   3500),
            # Menuiserie
            ('Menuiserie', 'Porte pleine bois massif (90×210)',       'U',  85000),
            ('Menuiserie', 'Porte métallique simple vantail',         'U',  65000),
            ('Menuiserie', 'Porte métallique double vantail',         'U', 120000),
            ('Menuiserie', 'Fenêtre aluminium coulissante 100×120',   'U',  90000),
            ('Menuiserie', 'Fenêtre aluminium battante 60×80',        'U',  65000),
            ('Menuiserie', 'Grille de fenêtre en fer forgé',          'U',  45000),
            ('Menuiserie', 'Portail métallique 2 vantaux 3m',        'U', 350000),
            # Plomberie / Sanitaire
            ('Plomberie / Sanitaire', 'Réseau alimentation eau PVC Ø32',    'ml',   8500),
            ('Plomberie / Sanitaire', 'Réseau évacuation PVC Ø100',         'ml',   7500),
            ('Plomberie / Sanitaire', 'WC à l\'anglaise complet',           'U',   95000),
            ('Plomberie / Sanitaire', 'Lavabo encastré complet',            'U',   75000),
            ('Plomberie / Sanitaire', 'Douche avec receveur',               'U',  125000),
            ('Plomberie / Sanitaire', 'Ballon d\'eau chaude 100L',          'U',  185000),
            ('Plomberie / Sanitaire', 'Fosse septique 3 m³',               'U',  850000),
            ('Plomberie / Sanitaire', 'Puisard d\'infiltration',            'U',  350000),
            # Électricité
            ('Électricité', 'Tableau électrique principal 12 disj.',  'U',  180000),
            ('Électricité', 'Point lumineux complet (plafonnier)',     'U',   25000),
            ('Électricité', 'Prise de courant 16A',                   'U',   15000),
            ('Électricité', 'Câble VGV 3×2.5 mm²',                   'ml',    1500),
            ('Électricité', 'Tube IRO Ø20',                           'ml',    1200),
            ('Électricité', 'Mise à la terre complète',               'U',   95000),
            # Peinture / Revêtements
            ('Peinture / Revêtements', 'Peinture intérieure 2 couches (mat)',    'm²',  3500),
            ('Peinture / Revêtements', 'Peinture extérieure 2 couches (façade)', 'm²',  4800),
            ('Peinture / Revêtements', 'Carrelage sol 60×60 (hors carreaux)',    'm²', 12000),
            ('Peinture / Revêtements', 'Carrelage mural 30×60',                  'm²', 14000),
            ('Peinture / Revêtements', 'Parquet stratifié',                       'm²', 18000),
            # VRD / Routes
            ('VRD / Routes', 'Abattage d\'arbres et débroussaillage',    'U',   15000),
            ('VRD / Routes', 'Terrassement voirie en déblai',            'm³',   4000),
            ('VRD / Routes', 'Couche de forme GNT 0/31.5 (e=20cm)',     'm²',   6500),
            ('VRD / Routes', 'Grave concassée 0/20 (base e=15cm)',      'm²',   8500),
            ('VRD / Routes', 'Béton bitumineux (roulement e=5cm)',       'm²',  16000),
            ('VRD / Routes', 'Enduit superficiel bicouche',              'm²',   4500),
            ('VRD / Routes', 'Bordure T2 (30×100)',                      'ml',   8500),
            ('VRD / Routes', 'Cunette bétonnée (30×30)',                 'ml',  22000),
            ('VRD / Routes', 'Caniveau rectangulaire 40×40',             'ml',  45000),
            ('VRD / Routes', 'Dalot préfabriqué 1.00×1.00',             'ml', 125000),
            ('VRD / Routes', 'Regard de visite béton 80×80',            'U',   85000),
            ('VRD / Routes', 'Marquage routier thermoplastique',         'm²',   8500),
            # Génie Civil / Ouvrages d'art
            ('Génie Civil', 'Palplanches métalliques (location)',        'm²',   8500),
            ('Génie Civil', 'Pieux forés Ø40 cm',                       'ml',  85000),
            ('Génie Civil', 'Enrochement (protection berges)',           'm³',  45000),
            ('Génie Civil', 'Gabion (mur de soutènement)',               'm³',  55000),
            ('Génie Civil', 'Mur de soutènement BA',                    'm³', 250000),
        ]
        c.executemany(
            "INSERT INTO articles (categorie, designation, unite, prix_unitaire) VALUES (?,?,?,?)",
            articles
        )

    conn.commit()
    conn.close()

# ─────────────────────────────────────────
#  ENTREPRISE
# ─────────────────────────────────────────
def get_entreprise():
    conn = get_conn()
    row = conn.execute("SELECT * FROM entreprise WHERE id=1").fetchone()
    conn.close()
    return dict(row) if row else {}

def save_entreprise(data):
    conn = get_conn()
    fields = [k for k in data if k != 'id']
    sets   = ", ".join(f"{f}=?" for f in fields)
    vals   = [data[f] for f in fields]
    conn.execute(f"UPDATE entreprise SET {sets} WHERE id=1", vals)
    conn.commit()
    conn.close()

def save_logo(src_path):
    """Copie le logo dans le dossier media, retourne le nouveau chemin."""
    ext = Path(src_path).suffix
    dst = MEDIA_DIR / f"logo{ext}"
    shutil.copy2(src_path, dst)
    return str(dst)

# ─────────────────────────────────────────
#  CLIENTS
# ─────────────────────────────────────────
def get_clients(search=""):
    conn = get_conn()
    if search:
        rows = conn.execute(
            "SELECT * FROM clients WHERE nom LIKE ? OR telephone LIKE ? OR ville LIKE ? ORDER BY nom",
            (f"%{search}%", f"%{search}%", f"%{search}%")
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM clients ORDER BY nom").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_client(cid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM clients WHERE id=?", (cid,)).fetchone()
    conn.close()
    return dict(row) if row else {}

def save_client(data):
    conn = get_conn()
    if data.get('id'):
        fields = [k for k in data if k not in ('id', 'created_at')]
        sets = ", ".join(f"{f}=?" for f in fields)
        vals = [data[f] for f in fields] + [data['id']]
        conn.execute(f"UPDATE clients SET {sets} WHERE id=?", vals)
    else:
        fields = [k for k in data if k not in ('id', 'created_at')]
        cols = ", ".join(fields)
        phs  = ", ".join("?" * len(fields))
        vals = [data[f] for f in fields]
        conn.execute(f"INSERT INTO clients ({cols}) VALUES ({phs})", vals)
    conn.commit()
    conn.close()

def delete_client(cid):
    conn = get_conn()
    conn.execute("DELETE FROM clients WHERE id=?", (cid,))
    conn.commit()
    conn.close()

def count_devis_client(cid):
    conn = get_conn()
    n = conn.execute("SELECT COUNT(*) FROM devis WHERE client_id=?", (cid,)).fetchone()[0]
    conn.close()
    return n

# ─────────────────────────────────────────
#  DEVIS
# ─────────────────────────────────────────
def next_devis_numero():
    conn = get_conn()
    year = datetime.now().year
    row  = conn.execute(
        "SELECT numero FROM devis WHERE numero LIKE ? ORDER BY numero DESC LIMIT 1",
        (f"DEV-{year}-%",)
    ).fetchone()
    conn.close()
    if row:
        last_n = int(row[0].split("-")[-1])
        return f"DEV-{year}-{last_n+1:04d}"
    return f"DEV-{year}-0001"

def get_devis_list(search="", statut=""):
    conn = get_conn()
    q = """
        SELECT d.*, c.nom as client_nom
        FROM devis d
        LEFT JOIN clients c ON c.id = d.client_id
        WHERE 1=1
    """
    params = []
    if search:
        q += " AND (d.numero LIKE ? OR d.chantier LIKE ? OR c.nom LIKE ?)"
        params += [f"%{search}%"] * 3
    if statut and statut != "Tous":
        q += " AND d.statut = ?"
        params.append(statut)
    q += " ORDER BY d.date_creation DESC"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_devis(did):
    conn = get_conn()
    d = conn.execute("""
        SELECT d.*, c.nom as client_nom, c.adresse as client_adresse,
               c.ville as client_ville, c.telephone as client_tel,
               c.email as client_email, c.nif as client_nif
        FROM devis d
        LEFT JOIN clients c ON c.id = d.client_id
        WHERE d.id=?
    """, (did,)).fetchone()
    lignes = conn.execute(
        "SELECT * FROM devis_lignes WHERE devis_id=? ORDER BY ordre",
        (did,)
    ).fetchall()
    conn.close()
    if not d:
        return None, []
    return dict(d), [dict(l) for l in lignes]

def save_devis(data, lignes):
    conn = get_conn()
    c = conn.cursor()
    did = data.get('id')
    if did:
        fields = [k for k in data if k not in ('id', 'created_at', 'client_nom',
                  'client_adresse','client_ville','client_tel','client_email','client_nif')]
        sets = ", ".join(f"{f}=?" for f in fields)
        vals = [data[f] for f in fields] + [did]
        c.execute(f"UPDATE devis SET {sets} WHERE id=?", vals)
        c.execute("DELETE FROM devis_lignes WHERE devis_id=?", (did,))
    else:
        fields = [k for k in data if k not in ('id', 'created_at', 'client_nom',
                  'client_adresse','client_ville','client_tel','client_email','client_nif')]
        cols = ", ".join(fields)
        phs  = ", ".join("?" * len(fields))
        vals = [data[f] for f in fields]
        c.execute(f"INSERT INTO devis ({cols}) VALUES ({phs})", vals)
        did = c.lastrowid
    # lignes
    for i, l in enumerate(lignes):
        c.execute("""
            INSERT INTO devis_lignes (devis_id, ordre, type_ligne, designation,
                                     unite, quantite, prix_unitaire, montant)
            VALUES (?,?,?,?,?,?,?,?)
        """, (did, i, l.get('type_ligne','item'), l.get('designation',''),
              l.get('unite',''), float(l.get('quantite',0) or 0),
              float(l.get('prix_unitaire',0) or 0), float(l.get('montant',0) or 0)))
    conn.commit()
    conn.close()
    return did

def delete_devis(did):
    conn = get_conn()
    conn.execute("DELETE FROM devis WHERE id=?", (did,))
    conn.commit()
    conn.close()

def duplicate_devis(did):
    d, lignes = get_devis(did)
    if not d:
        return None
    d.pop('id', None)
    d.pop('created_at', None)
    d['numero'] = next_devis_numero()
    d['date_creation'] = datetime.now().strftime("%Y-%m-%d")
    d['statut'] = 'Brouillon'
    return save_devis(d, lignes)

# ─────────────────────────────────────────
#  ARTICLES
# ─────────────────────────────────────────
def get_articles(search="", cat=""):
    conn = get_conn()
    q = "SELECT * FROM articles WHERE 1=1"
    params = []
    if search:
        q += " AND (designation LIKE ? OR categorie LIKE ?)"
        params += [f"%{search}%"]*2
    if cat and cat != "Toutes":
        q += " AND categorie = ?"
        params.append(cat)
    q += " ORDER BY categorie, designation"
    rows = conn.execute(q, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_categories_articles():
    conn = get_conn()
    rows = conn.execute("SELECT DISTINCT categorie FROM articles ORDER BY categorie").fetchall()
    conn.close()
    return [r[0] for r in rows]

def save_article(data):
    conn = get_conn()
    if data.get('id'):
        conn.execute("""UPDATE articles SET categorie=?, designation=?, unite=?,
                        prix_unitaire=?, description=? WHERE id=?""",
                     (data['categorie'], data['designation'], data['unite'],
                      data['prix_unitaire'], data.get('description',''), data['id']))
    else:
        conn.execute("""INSERT INTO articles (categorie, designation, unite, prix_unitaire, description)
                        VALUES (?,?,?,?,?)""",
                     (data['categorie'], data['designation'], data['unite'],
                      data['prix_unitaire'], data.get('description','')))
    conn.commit()
    conn.close()

def delete_article(aid):
    conn = get_conn()
    conn.execute("DELETE FROM articles WHERE id=?", (aid,))
    conn.commit()
    conn.close()

# ─────────────────────────────────────────
#  STATISTIQUES
# ─────────────────────────────────────────
def get_stats():
    conn = get_conn()
    year  = datetime.now().year
    month = datetime.now().month
    def q(sql, *p): return conn.execute(sql, p).fetchone()[0] or 0
    stats = {
        'total_devis'     : q("SELECT COUNT(*) FROM devis"),
        'devis_mois'      : q("SELECT COUNT(*) FROM devis WHERE strftime('%Y-%m', date_creation)=?",
                              f"{year}-{month:02d}"),
        'ca_annee'        : q("SELECT COALESCE(SUM(montant_ttc),0) FROM devis WHERE statut IN ('Accepté','Facturé') AND strftime('%Y',date_creation)=?",
                              str(year)),
        'devis_acceptes'  : q("SELECT COUNT(*) FROM devis WHERE statut='Accepté'"),
        'devis_en_attente': q("SELECT COUNT(*) FROM devis WHERE statut IN ('Envoyé','Brouillon')"),
        'devis_refuses'   : q("SELECT COUNT(*) FROM devis WHERE statut='Refusé'"),
        'nb_clients'      : q("SELECT COUNT(*) FROM clients"),
    }
    recents = conn.execute("""
        SELECT d.numero, d.date_creation, c.nom as client_nom,
               d.chantier, d.montant_ttc, d.statut
        FROM devis d LEFT JOIN clients c ON c.id=d.client_id
        ORDER BY d.created_at DESC LIMIT 8
    """).fetchall()
    stats['recents'] = [dict(r) for r in recents]
    conn.close()
    return stats
