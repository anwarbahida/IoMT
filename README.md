IoMT-ABE-Simulation (CustomTkinter Desktop)
===========================================

Description
-----------
Version desktop du projet IoMT-ABE-Simulation, utilisant CustomTkinter pour l'interface graphique.
C'est une simulation pédagogique : les algorithmes CP-ABE/KP-ABE sont simulés dans `abe/sim_abe.py`
via un chiffrement hybride (Fernet) et une évaluation simple des politiques.

Contenu
-------
- main.py : l'application CustomTkinter (GUI).
- abe/sim_abe.py : simulateur ABE (CP & KP) réutilisé.
- models.py : modèles SQLAlchemy avec SQLite local (data.db).
- requirements.txt : dépendances Python.

Installation rapide
-------------------
1. Crée et active un environnement virtuel :
   python -m venv venv
   venv\Scripts\activate  (Windows)

2. Installe les dépendances :
   pip install -r requirements.txt

3. Lance l'application :
   python main.py
