# DevisBTP - Logiciel de devis pour le Génie Civil (BTP) - Togo 🇹🇬

DevisBTP est une application de bureau développée en Python (Tkinter) permettant de créer, gérer et générer des devis professionnels pour les entreprises du BTP (Bâtiment, Travaux Publics) au **Togo** (devise **FCFA**). Elle propose une interface moderne avec effets de relief (raised, sunken, ridge, groove), un catalogue d’articles pré‑rempli (66 prestations courantes), et génère des PDF au format A4 (thème blanc/bleu).

## ✨ Fonctionnalités principales

- **Gestion de l’entreprise** : coordonnées, logo, TVA par défaut, conditions générales, délai d’exécution.
- **Gestion des clients** : particuliers, entreprises, administrations, ONG.
- **Catalogue d’articles** : 66 articles pré‑chargés (terrassement, béton, charpente, VRD, électricité…), modifiables/ajoutables.
- **Création / édition de devis** :
  - Sections, prestations, sous‑totaux, commentaires.
  - Choix du client, chantier, dates, statut (Brouillon, Envoyé, Accepté, Refusé, Facturé).
  - Calcul automatique HT, TVA et TTC.
- **Duplication de devis**.
- **Génération de PDF** : format A4, bleu/blanc, numéro de page, signature.
- **Tableau de bord** : indicateurs (total devis, chiffre d’affaires, acceptés…).
- **Recherche et filtres** par numéro, client, chantier, statut.
- **Double‑clic** pour ouvrir le détail d’un devis ou d’un client.
- **Raccourci clavier** : `Ctrl+N` → nouveau devis.

## 📸 Aperçu de l’interface

<img width="1362" height="731" alt="Capture d’écran du 2026-06-10 19-54-56" src="https://github.com/user-attachments/assets/99fd0432-0ad3-4c31-9ef9-3213ade3747d" />


## 🛠️ Technologies utilisées

- Python 3.12+
- Tkinter (interface graphique)
- SQLite (base de données locale)
- ReportLab (génération PDF)
- Pillow (gestion des images / logo)
- PyInstaller (création d’exécutables)

## 📦 Installation et exécution

### Depuis les sources

```bash
git clone https://github.com/koudousse-ab/Devis_BTP.git
cd Devis_BTP
pip install -r requirements.txt
python run.py   # ou python3 run.p

```
Exécutables pré‑compilés (Windows / Linux)

Les exécutables sont disponibles dans les Actions du dépôt GitHub ou en téléchargement dans la section Releases (à venir).

    Windows : lancez DevisBTP.exe (aucune installation Python nécessaire).

    Linux : utilisez le binaire DevisBTP (rendu exécutable) ou installez le paquet .deb fourni.

📝 Configuration initiale

Lors du premier lancement, une base de données SQLite est créée dans ~/DevisBTP/devis_btp.db (Linux/macOS) ou %USERPROFILE%\DevisBTP\devis_btp.db (Windows).
Une société par défaut est créée (modifiable dans l’onglet Mon Entreprise).
La TVA est initialement à 0 % ; vous pouvez la modifier dans l’onglet entreprise.
🧪 Utilisation rapide

    Renseignez les informations de votre entreprise (onglet Mon Entreprise).

    Ajoutez vos clients (onglet Clients).

    Consultez/modifiez le catalogue d’articles (onglet Articles & Prix).

    Créez un devis (Ctrl+N ou bouton Nouveau Devis) :

        Sélectionnez un client.

        Remplissez le chantier, les dates, la TVA.

        Ajoutez des prestations (depuis le catalogue ou manuellement).

        Sauvegardez, puis générez le PDF.

    Suivez les devis via le tableau de bord ou l’onglet Devis (changement de statut, duplication, suppression).

🔧 Construction des exécutables (pour les développeurs)
Sur Windows
cmd

pip install pyinstaller
pyinstaller --onefile --windowed --name DevisBTP --icon=logo.ico run.py

Sur Linux
bash

pip install pyinstaller
pyinstaller --onefile --name DevisBTP run.py

🤝 Contribuer

Les contributions sont les bienvenues !

    Signalez un bug ou proposez une amélioration via les Issues GitHub.

    Soumettez une Pull Request en respectant le style existant.

📄 Licence

Ce projet est distribué sous licence MIT – voir le fichier LICENSE pour plus de détails.
✉️ Contact

    Auteur : TCHEDRE Aboudoul-Koudousse

    GitHub : @koudousse-ab

    Gmail : koudousetchedre@gmail.com
Développé pour les professionnels du BTP au Togo.
Fait avec Python.

