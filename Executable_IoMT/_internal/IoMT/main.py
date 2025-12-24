import sys
import customtkinter as ctk
from tkinter import messagebox, filedialog
import base64, json, os, datetime
from models import get_session
from abe.sim_abe import setup_abe, encrypt_cp, encrypt_kp, keygen_cp, keygen_kp, decrypt_cp, decrypt_kp

db = get_session()
abe_state = setup_abe()
STORAGE_DIR = os.path.join(os.path.dirname(__file__), 'storage')
os.makedirs(STORAGE_DIR, exist_ok=True)

# Configuration du thème personnalisé
ctk.set_appearance_mode('Dark')
ctk.set_default_color_theme('blue')

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title('IoMT ABE')


        def resource_path(relative_path):
            """ Retourne le chemin absolu vers une ressource (dev + exe) """
            if getattr(sys, 'frozen', False):
                base_path = sys._MEIPASS  # dossier temporaire PyInstaller
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            return os.path.join(base_path, relative_path)

        self.iconbitmap(resource_path("icone.ico"))

        # Dimensions de la fenêtre
        width = 1200
        height = 650

        # Récupérer la taille de l'écran
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        # Calculer la position x, y pour centrer
        x = int((screen_width - width) / 2)
        y = int((screen_height - height) / 2)

        # Appliquer la géométrie centrée
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.minsize(1000, 600)

        # Configuration des couleurs personnalisées
        self.colors = {
            'primary': '#2B5F8A',
            'secondary': '#3D8BBA',
            'accent': '#FF6B35',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'error': '#F44336',
            'dark_bg': '#1E1E1E',
            'light_bg': '#2D2D2D',
            'card_bg': '#37474F',
            'text_light': '#FFFFFF',
            'text_muted': '#B0BEC5'
        }

        # Conteneur principal
        self.container = ctk.CTkFrame(self, fg_color=self.colors['dark_bg'])
        self.container.pack(fill='both', expand=True, padx=10, pady=10)

        # Sidebar avec design moderne
        self.sidebar = ctk.CTkFrame(self.container, width=220, corner_radius=15, 
                                   fg_color=self.colors['light_bg'])
        self.sidebar.pack(side='left', fill='y', padx=(0, 10))

        # En-tête sidebar
        sidebar_header = ctk.CTkFrame(self.sidebar, height=100, corner_radius=15,
                                     fg_color=self.colors['primary'])
        sidebar_header.pack(fill='x', pady=(0, 20))
        
        ctk.CTkLabel(sidebar_header, text="🔒 MEDICAL ABE", 
                    font=('Arial', 20, 'bold'), 
                    text_color=self.colors['text_light']).pack(expand=True, pady=(15, 0))
        ctk.CTkLabel(sidebar_header, text="Secure Data Platform", 
                    font=('Arial', 12), 
                    text_color=self.colors['text_muted']).pack(expand=True, pady=(0, 15))

        # Boutons de navigation avec icônes
        nav_buttons = [
            ("👥 Gestion Utilisateurs", self.show_user_page),
            ("📡 Simulateur IoMT", self.show_iomt_page),
            ("⚡ Actions Utilisateurs", self.show_vider_user_page),
            ("⚡ Actions Records", self.show_vider_record_page)
        ]

        for text, command in nav_buttons:
            btn = ctk.CTkButton(self.sidebar, text=text, command=command,
                               font=('Arial', 14), height=45,
                               fg_color='transparent',
                               hover_color=self.colors['primary'],
                               border_color=self.colors['secondary'],
                               border_width=2,
                               corner_radius=12,
                               anchor='w')
            btn.pack(pady=8, padx=15, fill='x')

        # Status bar en bas de la sidebar
        status_frame = ctk.CTkFrame(self.sidebar, height=50, corner_radius=12,
                                   fg_color=self.colors['card_bg'])
        status_frame.pack(side='bottom', fill='x', padx=10, pady=10)
        
        from models import User, Record
        user_count = db.query(User).count()
        record_count = db.query(Record).count()
        
        self.status_label = ctk.CTkLabel(status_frame, 
                    text=f"👥 {user_count} users\n📁 {record_count} records",
                    font=('Arial', 11),
                    text_color=self.colors['text_muted'],
                    justify='center')
        self.status_label.pack(expand=True, pady=5)
        # Zone de contenu principale
        self.content_frame = ctk.CTkFrame(self.container, corner_radius=15,
                                         fg_color=self.colors['light_bg'])
        self.content_frame.pack(side='right', fill='both', expand=True)

        # Initialisation des pages
        self.user_page = None
        self.iomt_page = None
        self.vider_user_page = None
        self.selected_file = None

        # Afficher par défaut la page utilisateurs
        self.show_user_page()
    def refresh_status_counts(self):
        from models import User, Record
        user_count = db.query(User).count()
        record_count = db.query(Record).count()

        self.status_label.configure(
            text=f"👥 {user_count} users\n📁 {record_count} records"
        )

    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def show_user_page(self):
        self.clear_content()
        self.user_page = UserPage(self.content_frame, self)
        self.user_page.pack(fill='both', expand=True, padx=20, pady=20)

    def show_iomt_page(self):
        self.clear_content()
        self.iomt_page = IoMTPage(self.content_frame, self)
        self.iomt_page.pack(fill='both', expand=True, padx=20, pady=20)

    def show_vider_user_page(self):
        self.clear_content()
        self.vider_user_page = GestionUsers(self.content_frame, self)
        self.vider_user_page.pack(fill='both', expand=True, padx=20, pady=20)
    def show_vider_record_page(self):
        self.clear_content()
        self.vider_record_page = GestionRecords(self.content_frame, self)
        self.vider_record_page.pack(fill='both', expand=True, padx=20, pady=20)


# -------------------- PAGE UTILISATEURS AVEC SCROLL CORRIGÉ --------------------
class UserPage(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color=parent.cget('fg_color'))
        self.main_app = main_app
        self.setup_ui()
        self.main_app.refresh_status_counts()
    def setup_ui(self):
        # Créer un frame scrollable avec CTkScrollableFrame
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color=self.cget('fg_color'))
        self.scrollable_frame.pack(fill="both", expand=True)

        # Maintenant tout le contenu va dans scrollable_frame
        self.setup_content()

    def setup_content(self):
        # Header de la page
        header_frame = ctk.CTkFrame(self.scrollable_frame, fg_color=self.main_app.colors['primary'], 
                                   height=80, corner_radius=12)
        header_frame.pack(fill='x', pady=(0, 20), padx=20)
        ctk.CTkLabel(header_frame, text="👥 Gestion des Utilisateurs", 
                    font=('Arial', 24, 'bold'),
                    text_color=self.main_app.colors['text_light']).pack(expand=True)

        # Conteneur principal avec deux colonnes
        main_container = ctk.CTkFrame(self.scrollable_frame, fg_color='transparent')
        main_container.pack(fill='both', expand=True, padx=20)

        # Colonne gauche - Formulaire
        left_column = ctk.CTkFrame(main_container, corner_radius=15, 
                                  fg_color=self.main_app.colors['card_bg'])
        left_column.pack(side='left', fill='both', expand=True, padx=(0, 10))

        # Section création utilisateur
        create_section = ctk.CTkFrame(left_column, corner_radius=12, fg_color='transparent')
        create_section.pack(fill='x', pady=15, padx=15)
        
        ctk.CTkLabel(create_section, text="➕ Nouvel Utilisateur", 
                    font=('Arial', 18, 'bold'),
                    text_color=self.main_app.colors['text_light']).pack(pady=(0, 15))
        
        self.username = ctk.CTkEntry(create_section, placeholder_text='Nom d\'utilisateur', 
                                   height=45, font=('Arial', 14))
        self.username.pack(fill='x', pady=8, padx=10)
        
        self.role = ctk.CTkEntry(create_section, placeholder_text='Rôle (ex: medecin, infirmier)', 
                               height=45, font=('Arial', 14))
        self.role.pack(fill='x', pady=8, padx=10)
        
        ctk.CTkButton(create_section, text="🎯 Créer Utilisateur", 
                     command=self.create_user, height=45,
                     font=('Arial', 14, 'bold'),
                     fg_color=self.main_app.colors['success'],
                     hover_color='#45a049').pack(fill='x', pady=15, padx=10)

        # Section attributs
        attr_section = ctk.CTkFrame(left_column, corner_radius=12, fg_color='transparent')
        attr_section.pack(fill='x', pady=15, padx=15)
        
        ctk.CTkLabel(attr_section, text="🎯 Ajouter un Attribut", 
                    font=('Arial', 18, 'bold'),
                    text_color=self.main_app.colors['text_light']).pack(pady=(0, 15))
        
        self.attr_userid = ctk.CTkEntry(attr_section, placeholder_text='ID Utilisateur', 
                                      height=45, font=('Arial', 14))
        self.attr_userid.pack(fill='x', pady=8, padx=10)
        
        self.attr_name = ctk.CTkEntry(attr_section, placeholder_text='Nom de l\'attribut', 
                                    height=45, font=('Arial', 14))
        self.attr_name.pack(fill='x', pady=8, padx=10)
        
        self.attr_value = ctk.CTkEntry(attr_section, placeholder_text='Valeur de l\'attribut', 
                                     height=45, font=('Arial', 14))
        self.attr_value.pack(fill='x', pady=8, padx=10)
        
        ctk.CTkButton(attr_section, text="⚡ Ajouter Attribut", 
                     command=self.add_attribute, height=45,
                     font=('Arial', 14, 'bold'),
                     fg_color=self.main_app.colors['secondary'],
                     hover_color='#357abd').pack(fill='x', pady=15, padx=10)

        # Section génération clé ABE
        key_section = ctk.CTkFrame(left_column, corner_radius=12, fg_color='transparent')
        key_section.pack(fill='x', pady=15, padx=15)
        
        ctk.CTkLabel(key_section, text="🔑 Générer Clé ABE", 
                    font=('Arial', 18, 'bold'),
                    text_color=self.main_app.colors['text_light']).pack(pady=(0, 15))
        
        self.key_userid = ctk.CTkEntry(key_section, placeholder_text='ID Utilisateur', 
                                     height=45, font=('Arial', 14))
        self.key_userid.pack(fill='x', pady=8, padx=10)
        
        self.key_type = ctk.CTkComboBox(key_section, values=['CP', 'KP'], 
                                      height=45, font=('Arial', 14))
        self.key_type.set('CP')
        self.key_type.pack(fill='x', pady=8, padx=10)
        
        self.key_policy = ctk.CTkEntry(key_section, placeholder_text='Policy ou attributs JSON', 
                                     height=45, font=('Arial', 14))
        self.key_policy.pack(fill='x', pady=8, padx=10)
        
        ctk.CTkButton(key_section, text="🔐 Générer Clé", 
                     command=self.generate_key, height=45,
                     font=('Arial', 14, 'bold'),
                     fg_color=self.main_app.colors['accent'],
                     hover_color='#e55a2e').pack(fill='x', pady=15, padx=10)

        # Colonne droite - Liste des utilisateurs
        right_column = ctk.CTkFrame(main_container, corner_radius=15,
                                   fg_color=self.main_app.colors['card_bg'])
        right_column.pack(side='right', fill='both', expand=True, padx=(10, 0))

        ctk.CTkLabel(right_column, text="📋 Liste des Utilisateurs", 
                    font=('Arial', 18, 'bold'),
                    text_color=self.main_app.colors['text_light']).pack(pady=15)

        # Frame pour la liste avec scrollbar
        list_frame = ctk.CTkFrame(right_column, fg_color='transparent')
        list_frame.pack(fill='both', expand=True, padx=15, pady=10)

        self.users_box = ctk.CTkTextbox(list_frame, wrap='word', font=('Arial', 12),
                                      fg_color=self.main_app.colors['dark_bg'],
                                      text_color=self.main_app.colors['text_light'])
        self.users_box.pack(side='left', fill='both', expand=True)

        scrollbar_inner = ctk.CTkScrollbar(list_frame, command=self.users_box.yview,
                                         fg_color=self.main_app.colors['dark_bg'])
        scrollbar_inner.pack(side='right', fill='y')
        self.users_box.configure(yscrollcommand=scrollbar_inner.set)

        ctk.CTkButton(right_column, text="🔄 Rafraîchir la Liste", 
                     command=self.refresh_users, height=45,
                     font=('Arial', 14, 'bold')).pack(fill='x', pady=15, padx=15)

        self.refresh_users()

    def create_user(self):
        uname = self.username.get().strip()
        role = self.role.get().strip()
        if not uname:
            messagebox.showerror('Erreur', 'Le nom d\'utilisateur est requis')
            return
        from models import User as U
        u = U(username=uname, role=role)
        db.add(u)
        db.commit()
        messagebox.showinfo('Succès', f'✅ Utilisateur créé - ID: {u.id}')
        self.refresh_users()
        self.username.delete(0, 'end')
        self.role.delete(0, 'end')
        self.main_app.refresh_status_counts()

    def add_attribute(self):
        try:
            uid = int(self.attr_userid.get().strip())
        except:
            messagebox.showerror('Erreur', '❌ ID utilisateur invalide')
            return
        
        name = self.attr_name.get().strip()
        val = self.attr_value.get().strip()
        
        if not name or not val:
            messagebox.showerror('Erreur', '❌ Le nom et la valeur sont requis')
            return
        
        from models import Attribute as A
        a = A(user_id=uid, name=name, value=val)
        db.add(a)
        db.commit()
        messagebox.showinfo('Succès', '✅ Attribut ajouté avec succès')
        self.refresh_users()
        self.attr_userid.delete(0, 'end')
        self.attr_name.delete(0, 'end')
        self.attr_value.delete(0, 'end')

    def generate_key(self):
        try:
            uid = int(self.key_userid.get().strip())
        except:
            messagebox.showerror('Erreur', '❌ ID utilisateur invalide')
            return
        ktype = self.key_type.get()
        payload = self.key_policy.get().strip()
        from models import ABEKey as K
        if ktype == 'CP':
            try:
                attrs = json.loads(payload)
            except Exception:
                messagebox.showerror('Erreur', 'Pour les clés CP, fournissez une liste JSON comme ["role:medecin"]')
                return
            sk = keygen_cp(abe_state, attrs)
            blob_hex = sk.hex()
            key = K(user_id=uid, key_type='CP', private_key_blob=blob_hex, policy_blob='')
        else:
            policy = payload
            sk = keygen_kp(abe_state, policy)
            blob_hex = sk.hex()
            key = K(user_id=uid, key_type='KP', private_key_blob=blob_hex, policy_blob=policy)
        db.add(key)
        db.commit()
        messagebox.showinfo('Succès', f'✅ Clé créée - ID: {key.id}')
        self.refresh_users()
        self.key_userid.delete(0, 'end')
        self.key_policy.delete(0, 'end')

    def refresh_users(self):
        from models import User as U, Attribute as A, ABEKey as K
        self.users_box.delete('1.0', 'end')
        users = db.query(U).all()

        for u in users:
            # ===== En-tête utilisateur =====
            self.users_box.insert(
                'end',
                f"🆔 ID: {u.id} | 👤 {u.username} | 🎯 Rôle: {u.role}\n"
            )

            # ===== Attributs (style preview) =====
            attrs = db.query(A).filter(A.user_id == u.id).all()
            if attrs:
                attrs_text = ", ".join([f"{a.name}={a.value}" for a in attrs])
                preview_attrs = attrs_text[:80] + "..." if len(attrs_text) > 80 else attrs_text
                self.users_box.insert(
                    'end',
                    f"📋 Attributs: {preview_attrs}\n"
                )
            '''else:
                self.users_box.insert(
                    'end',
                    "📋 Attributs: Aucun\n"
                )'''

           # ===== Clés ABE / Policy (style record) =====
            keys = db.query(K).filter(K.user_id == u.id).all()
            if keys:
                for k in keys:
                    # Si c'est une clé KP, on prend policy_blob
                    if k.key_type == 'KP' and k.policy_blob:
                        policy_text = k.policy_blob
                    else:
                        # Sinon, on prend les attributs de l'utilisateur
                        attrs = db.query(A).filter(A.user_id == u.id).all()
                        if attrs:
                            policy_text = ", ".join([f"{a.name}={a.value}" for a in attrs])
                        else:
                            policy_text = "—"
                    
                    policy_preview = policy_text[:80] + "..." if len(policy_text) > 80 else policy_text

                    self.users_box.insert(
                        'end',
                        f"🔑 KeyID: {k.id} | 🔐 Type: {k.key_type}\n"
                        f"📜 Policy/Attribs: {policy_preview}\n"
                    )
            '''else:
                self.users_box.insert(
                    'end',
                    "🔑 Clés ABE: Aucune\n"
                )'''

            # ===== Séparateur =====
            self.users_box.insert('end', "─" * 60 + "\n\n")

# -------------------- PAGE IOMT AVEC DESIGN AVANCE ET SCROLL --------------------
class IoMTPage(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color=parent.cget('fg_color'))
        self.main_app = main_app
        self.setup_ui()
        self.main_app.refresh_status_counts()

    def setup_ui(self):
        # Créer un frame scrollable avec CTkScrollableFrame
        self.scrollable_frame = ctk.CTkScrollableFrame(self, fg_color=self.cget('fg_color'))
        self.scrollable_frame.pack(fill="both", expand=True)

        # Maintenant tout le contenu va dans scrollable_frame
        self.setup_content()

    def setup_content(self):
        # Header
        header_frame = ctk.CTkFrame(self.scrollable_frame, fg_color=self.main_app.colors['secondary'], 
                                   height=80, corner_radius=12)
        header_frame.pack(fill='x', pady=(0, 20), padx=20)
        ctk.CTkLabel(header_frame, text="📡 Simulateur IoMT - Envoi de Données Médicales", 
                    font=('Arial', 24, 'bold'),
                    text_color=self.main_app.colors['text_light']).pack(expand=True)

        # Conteneur principal
        main_container = ctk.CTkFrame(self.scrollable_frame, fg_color='transparent')
        main_container.pack(fill='both', expand=True, padx=20)

        # Section configuration
        config_section = ctk.CTkFrame(main_container, corner_radius=15,
                                     fg_color=self.main_app.colors['card_bg'])
        config_section.pack(fill='x', pady=10, padx=10)

        ctk.CTkLabel(config_section, text="⚙️ Configuration de l'Envoi", 
                    font=('Arial', 18, 'bold'),
                    text_color=self.main_app.colors['text_light']).pack(pady=15)

        # Grille pour les champs de configuration
        grid_frame = ctk.CTkFrame(config_section, fg_color='transparent')
        grid_frame.pack(fill='x', padx=20, pady=10)

        ctk.CTkLabel(grid_frame, text="📟 Capteur ID:", font=('Arial', 14)).grid(row=0, column=0, sticky='w', pady=12)
        self.sensor_id = ctk.CTkEntry(grid_frame, placeholder_text='sensor-001', height=45, font=('Arial', 14))
        self.sensor_id.grid(row=0, column=1, sticky='ew', pady=12, padx=(15, 20))

        ctk.CTkLabel(grid_frame, text="🔐 Mode de Chiffrement:", font=('Arial', 14)).grid(row=1, column=0, sticky='w', pady=12)
        self.encryption_mode = ctk.CTkComboBox(grid_frame, values=['CP', 'KP'], height=45, font=('Arial', 14))
        self.encryption_mode.set('CP')
        self.encryption_mode.grid(row=1, column=1, sticky='ew', pady=12, padx=(15, 20) )

        ctk.CTkLabel(grid_frame, text="📝 Policy/Attributs:", font=('Arial', 14)).grid(row=2, column=0, sticky='w', pady=12)
        self.policy_or_attrs = ctk.CTkEntry(grid_frame, 
                                          placeholder_text='Policy ou JSON attributes', 
                                          height=45, font=('Arial', 14))
        self.policy_or_attrs.grid(row=2, column=1, sticky='ew', pady=12, padx=(15, 20))

        grid_frame.columnconfigure(1, weight=1)

        # Boutons d'action
        button_frame = ctk.CTkFrame(config_section, fg_color='transparent')
        button_frame.pack(fill='x', padx=20, pady=20)

        ctk.CTkButton(button_frame, text="📁 Choisir Fichier à Chiffrer", 
                     command=self.choose_file, height=50,
                     font=('Arial', 14, 'bold'),
                     fg_color=self.main_app.colors['primary']).pack(side='left', padx=(0, 10), fill='x', expand=True)

        ctk.CTkButton(button_frame, text="🚀 Envoyer la Lecture", 
                     command=self.send_reading, height=50,
                     font=('Arial', 14, 'bold'),
                     fg_color=self.main_app.colors['success']).pack(side='left', fill='x', expand=True)

        # Section historique
        history_section = ctk.CTkFrame(main_container, corner_radius=15,
                                      fg_color=self.main_app.colors['card_bg'])
        history_section.pack(fill='both', expand=True, pady=10, padx=10)

        ctk.CTkLabel(history_section, text="📊 Historique des Enregistrements", 
                    font=('Arial', 18, 'bold'),
                    text_color=self.main_app.colors['text_light']).pack(pady=15)

        # Frame pour la liste des records avec scrollbar
        records_frame = ctk.CTkFrame(history_section, fg_color='transparent')
        records_frame.pack(fill='both', expand=True, padx=20, pady=10)

        self.records_box = ctk.CTkTextbox(records_frame, wrap='word', font=('Arial', 12),
                                        fg_color=self.main_app.colors['dark_bg'],
                                        text_color=self.main_app.colors['text_light'])
        self.records_box.pack(side='left', fill='both', expand=True)

        records_scrollbar = ctk.CTkScrollbar(records_frame, command=self.records_box.yview,
                                           fg_color=self.main_app.colors['dark_bg'])
        records_scrollbar.pack(side='right', fill='y')
        self.records_box.configure(yscrollcommand=records_scrollbar.set)

        # Section déchiffrement
        decrypt_section = ctk.CTkFrame(main_container, corner_radius=15,
                                      fg_color=self.main_app.colors['card_bg'])
        decrypt_section.pack(fill='x', pady=10, padx=10)

        ctk.CTkLabel(decrypt_section, text="🔓 Déchiffrement des Données", 
                    font=('Arial', 18, 'bold'),
                    text_color=self.main_app.colors['text_light']).pack(pady=15)

        decrypt_grid = ctk.CTkFrame(decrypt_section, fg_color='transparent')
        decrypt_grid.pack(fill='x', padx=20, pady=10)

        ctk.CTkLabel(decrypt_grid, text="📄 ID Record:", font=('Arial', 14)).grid(row=0, column=0, sticky='w', pady=10)
        self.dec_record = ctk.CTkEntry(decrypt_grid, placeholder_text='record_id', height=45, font=('Arial', 14))
        self.dec_record.grid(row=0, column=1, sticky='ew', pady=10, padx=(15, 20))

        ctk.CTkLabel(decrypt_grid, text="🔑 ID Clé:", font=('Arial', 14)).grid(row=1, column=0, sticky='w', pady=10)
        self.dec_key = ctk.CTkEntry(decrypt_grid, placeholder_text='key_id', height=45, font=('Arial', 14))
        self.dec_key.grid(row=1, column=1, sticky='ew', pady=10, padx=(15, 20))

        decrypt_grid.columnconfigure(1, weight=1)

        ctk.CTkButton(decrypt_section, text="🔓 Déchiffrer", 
                     command=self.attempt_decrypt, height=50,
                     font=('Arial', 14, 'bold'),
                     fg_color=self.main_app.colors['accent']).pack(fill='x', pady=15, padx=20)

        ctk.CTkButton(history_section, text="🔄 Rafraîchir l'Historique", 
                     command=self.refresh_records, height=45,
                     font=('Arial', 14, 'bold')).pack(fill='x', pady=15, padx=20)

        self.refresh_records()

    def choose_file(self):
        path = filedialog.askopenfilename(
            title='Choisir un fichier à chiffrer',
            filetypes=[('Tous les fichiers', '*.*'), ('Fichiers texte', '*.txt'), ('Images', '*.png *.jpg')]
        )
        if path:
            self.main_app.selected_file = path
            messagebox.showinfo('Fichier Sélectionné', f'✅ Fichier choisi: {os.path.basename(path)}')

    def send_reading(self):
        if not self.main_app.selected_file:
            messagebox.showerror('Erreur', '❌ Veuillez choisir un fichier d\'abord')
            return
        
        sensor = self.sensor_id.get().strip() or 'sensor-001'
        mode = self.encryption_mode.get()
        payload = self.policy_or_attrs.get().strip()
        
        try:
            with open(self.main_app.selected_file, 'rb') as f:
                content = f.read()
            
            if mode == 'CP':
                ct_blob, meta = encrypt_cp(abe_state, payload, content)
            else:
                try:
                    attrs = json.loads(payload)
                except Exception:
                    messagebox.showerror('Erreur', 'Pour le chiffrement KP, fournissez une liste JSON d\'attributs')
                    return
                ct_blob, meta = encrypt_kp(abe_state, attrs, content)
            
            filename = f'{int(datetime.datetime.utcnow().timestamp())}_{os.path.basename(self.main_app.selected_file)}.bin'
            path = os.path.join(STORAGE_DIR, filename)
            
            with open(path, 'wb') as f:
                f.write(ct_blob)
            
            from models import Record as R
            rec = R(sensor_id=sensor, storage_path=path, encryption_type=mode,
                    policy_text=meta.get('policy', ''), attributes_json=json.dumps(meta.get('attributes', [])),
                    created_at=datetime.datetime.utcnow())
            db.add(rec)
            db.commit()
            
            messagebox.showinfo('Succès', f'✅ Enregistrement stocké - ID: {rec.id}')
            self.refresh_records()
            self.main_app.refresh_status_counts()
            
        except Exception as e:
            messagebox.showerror('Erreur', f'❌ Erreur lors de l\'envoi: {str(e)}')

    def refresh_records(self):
        from models import Record as R
        self.records_box.delete('1.0', 'end')
        recs = db.query(R).order_by(R.created_at.desc()).all()
        
        for r in recs:
            policy_text = r.policy_text or r.attributes_json
            preview = policy_text[:80] + "..." if len(policy_text) > 80 else policy_text
            
            self.records_box.insert('end', 
                                  f"🆔 ID: {r.id} | 📡 Capteur: {r.sensor_id} | "
                                  f"🔐 Type: {r.encryption_type}\n"
                                  f"📋 Policy/Attributs: {preview}\n"
                                  f"🕐 Créé le: {r.created_at.strftime('%Y-%m-%d %H:%M')}\n"
                                  f"{'─'*60}\n\n")

    def attempt_decrypt(self):
        try:
            rid = int(self.dec_record.get().strip())
            kid = int(self.dec_key.get().strip())
        except:
            messagebox.showerror('Erreur', '❌ IDs invalides')
            return
        from models import Record as R, ABEKey as K
        rec = db.query(R).get(rid)
        key = db.query(K).get(kid)
        if not rec or not key:
            messagebox.showerror('Erreur', '❌ Record ou clé non trouvé')
            return
        with open(rec.storage_path, 'rb') as f:
            ct = f.read()
        sk_blob = bytes.fromhex(key.private_key_blob)
        if rec.encryption_type == 'CP':
            pt = decrypt_cp(abe_state, sk_blob, ct)
        else:
            pt = decrypt_kp(abe_state, sk_blob, ct)
        if pt is None:
            messagebox.showerror('Accès Refusé', '❌ Politique non satisfaite ou échec du déchiffrement')
            return
        outpath = os.path.join(os.path.dirname(rec.storage_path), f'plain_{rid}.bin')
        with open(outpath, 'wb') as f:
            f.write(pt)
        messagebox.showinfo('Succès', f'✅ Texte clair sauvegardé dans: {outpath}')

# -------------------- PAGE GESTION UTILISATEURS AVEC DESIGN AVANCE --------------------
class GestionUsers(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color=parent.cget('fg_color'))
        self.main_app = main_app
        self.setup_ui()
        self.main_app.refresh_status_counts()
    def setup_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color=self.main_app.colors['accent'], 
                                   height=80, corner_radius=12)
        header_frame.pack(fill='x', pady=(0, 20))
        ctk.CTkLabel(header_frame, text="⚡ Actions sur les Utilisateurs", 
                    font=('Arial', 24, 'bold'),
                    text_color=self.main_app.colors['text_light']).pack(expand=True)

        # Conteneur principal
        main_container = ctk.CTkFrame(self, fg_color='transparent')
        main_container.pack(fill='both', expand=True)

        # Frame scrollable pour la liste des utilisateurs
        self.scroll_frame = ctk.CTkScrollableFrame(main_container, 
                                                  fg_color=self.main_app.colors['card_bg'],
                                                  corner_radius=15)
        self.scroll_frame.pack(fill='both', expand=True, pady=10, padx=10)

        # Titre pour la section
        ctk.CTkLabel(self.scroll_frame, text="📋 Liste des Utilisateurs",
                    font=('Arial', 18, 'bold'),
                    text_color=self.main_app.colors['text_light']).pack(pady=10)

        # Bouton pour rafraîchir
        ctk.CTkButton(main_container, text="🔄 Rafraîchir la liste", 
                     command=self.refresh_users, height=45,
                     font=('Arial', 14, 'bold')).pack(pady=10)

        # Frame pour modification utilisateur (cachée au début)
        self.edit_frame = ctk.CTkFrame(main_container, corner_radius=15,
                                      fg_color=self.main_app.colors['card_bg'])
        self.edit_frame.pack(fill='both', expand=True, pady=10, padx=10)
        self.edit_frame.pack_forget()  # cachée

        self.refresh_users()

    def refresh_users(self):
        # Effacer le contenu précédent
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        from models import User as U
        users = db.query(U).all()

        if not users:
            ctk.CTkLabel(self.scroll_frame, text="Aucun utilisateur trouvé",
                        font=('Arial', 14),
                        text_color=self.main_app.colors['text_muted']).pack(pady=20)
            return

        for u in users:
            user_card = ctk.CTkFrame(self.scroll_frame, corner_radius=10,
                                   fg_color=self.main_app.colors['dark_bg'])
            user_card.pack(fill='x', pady=8, padx=10)

            # Informations utilisateur
            info_frame = ctk.CTkFrame(user_card, fg_color='transparent')
            info_frame.pack(fill='x', padx=15, pady=10)

            ctk.CTkLabel(info_frame, 
                        text=f"👤 {u.username}",
                        font=('Arial', 16, 'bold'),
                        text_color=self.main_app.colors['text_light']).pack(anchor='w')
            
            ctk.CTkLabel(info_frame,
                        text=f"🆔 ID: {u.id} | 🎯 Rôle: {u.role or 'Non défini'}",
                        font=('Arial', 12),
                        text_color=self.main_app.colors['text_muted']).pack(anchor='w')

            # Boutons d'action
            btn_frame = ctk.CTkFrame(user_card, fg_color='transparent')
            btn_frame.pack(fill='x', padx=15, pady=(5, 10))

            ctk.CTkButton(btn_frame, text="✏️ Modifier", width=120,
                         command=lambda u=u: self.edit_user(u),
                         fg_color=self.main_app.colors['secondary']).pack(side='left', padx=(0, 10))

            ctk.CTkButton(btn_frame, text="🗑️ Supprimer", width=120,
                         command=lambda u=u: self.delete_user(u),
                         fg_color=self.main_app.colors['error']).pack(side='left')

    def edit_user(self, user):
        # Masquer le tableau
        self.scroll_frame.pack_forget()

        # Vider et afficher le frame de modification
        for widget in self.edit_frame.winfo_children():
            widget.destroy()
        self.edit_frame.pack(fill='both', expand=True, pady=10, padx=10)

        ctk.CTkLabel(self.edit_frame, 
                    text=f"✏️ Modifier Utilisateur - ID: {user.id}",
                    font=("Arial", 20, "bold"),
                    text_color=self.main_app.colors['text_light']).pack(pady=20)

        # Formulaire de modification
        form_frame = ctk.CTkFrame(self.edit_frame, fg_color='transparent')
        form_frame.pack(fill='x', padx=50, pady=20)

        # Username
        ctk.CTkLabel(form_frame, text="👤 Username:", font=('Arial', 14)).pack(anchor='w', pady=(10, 5))
        username_entry = ctk.CTkEntry(form_frame, height=45, font=('Arial', 14))
        username_entry.pack(fill='x', pady=5)
        username_entry.insert(0, user.username)

        # Role
        ctk.CTkLabel(form_frame, text="🎯 Rôle:", font=('Arial', 14)).pack(anchor='w', pady=(10, 5))
        role_entry = ctk.CTkEntry(form_frame, height=45, font=('Arial', 14))
        role_entry.pack(fill='x', pady=5)
        role_entry.insert(0, user.role or "")

        # Boutons sauvegarder / annuler
        btn_frame = ctk.CTkFrame(self.edit_frame, fg_color='transparent')
        btn_frame.pack(pady=30)

        def save_changes():
            new_username = username_entry.get().strip()
            new_role = role_entry.get().strip()

            if not new_username:
                messagebox.showerror("Erreur", "❌ Username ne peut pas être vide")
                return

            user.username = new_username
            user.role = new_role
            db.commit()
            messagebox.showinfo("Succès", f"✅ Utilisateur {user.id} modifié")
            self.cancel_changes()

        def cancel_changes():
            self.edit_frame.pack_forget()
            self.scroll_frame.pack(fill='both', expand=True, pady=10, padx=10)
            self.refresh_users()

        ctk.CTkButton(btn_frame, text="💾 Sauvegarder", 
                     command=save_changes, height=45,
                     font=('Arial', 14, 'bold'),
                     fg_color=self.main_app.colors['success']).pack(side='left', padx=10)

        ctk.CTkButton(btn_frame, text="❌ Annuler", 
                     command=cancel_changes, height=45,
                     font=('Arial', 14, 'bold'),
                     fg_color=self.main_app.colors['error']).pack(side='left', padx=10)

    def delete_user(self, user):
        if messagebox.askyesno("Confirmation", 
                             f"Êtes-vous sûr de vouloir supprimer l'utilisateur {user.username} ?\nCette action est irréversible."):
            db.delete(user)
            db.commit()
            messagebox.showinfo("Succès", f"✅ Utilisateur {user.username} supprimé")
            self.refresh_users()
            self.main_app.refresh_status_counts()

class GestionRecords(ctk.CTkFrame):
    def __init__(self, parent, main_app):
        super().__init__(parent, fg_color=parent.cget('fg_color'))
        self.main_app = main_app
        self.setup_ui()
        self.main_app.refresh_status_counts()
    def setup_ui(self):
        header = ctk.CTkFrame(self, fg_color=self.main_app.colors['accent'],
                              height=80, corner_radius=12)
        header.pack(fill='x', pady=(0, 20))

        ctk.CTkLabel(
            header,
            text="📦 Actions sur les Records",
            font=('Arial', 24, 'bold'),
            text_color=self.main_app.colors['text_light']
        ).pack(expand=True)

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=self.main_app.colors['card_bg'],
            corner_radius=15
        )
        self.scroll.pack(fill='both', expand=True, padx=10, pady=10)

        ctk.CTkButton(
            self,
            text="🔄 Rafraîchir",
            command=self.refresh_records,
            height=45
        ).pack(pady=10)

        self.refresh_records()
    def refresh_records(self):
        for w in self.scroll.winfo_children():
            w.destroy()

        from models import Record
        records = db.query(Record).order_by(Record.created_at.desc()).all()

        if not records:
            ctk.CTkLabel(
                self.scroll,
                text="Aucun record trouvé",
                font=('Arial', 14)
            ).pack(pady=20)
            return

        for r in records:
            self._render_record(r)
    def _render_record(self, record):
        card = ctk.CTkFrame(
            self.scroll,
            fg_color=self.main_app.colors['dark_bg'],
            corner_radius=10
        )
        card.pack(fill='x', padx=10, pady=8)

        info = ctk.CTkFrame(card, fg_color='transparent')
        info.pack(fill='x', padx=15, pady=10)

        ctk.CTkLabel(
            info,
            text=f"🆔 Record #{record.id} | 📡 {record.sensor_id}",
            font=('Arial', 16, 'bold')
        ).pack(anchor='w')

        ctk.CTkLabel(
            info,
            text=f"🔐 Type: {record.encryption_type} | 🕒 {record.created_at}",
            font=('Arial', 12)
        ).pack(anchor='w')

        ctk.CTkLabel(
            info,
            text=f"📋 Policy / Attributs : {record.policy_text or record.attributes_json}",
            font=('Arial', 12),
            wraplength=700
        ).pack(anchor='w', pady=(5, 0))
        btns = ctk.CTkFrame(card, fg_color='transparent')
        btns.pack(fill='x', padx=15, pady=(5, 10))

        ctk.CTkButton(
            btns, text="👁️ Détails",
            command=lambda r=record: self.show_details(r)
        ).pack(side='left', padx=5)

        ctk.CTkButton(
            btns, text="🗑️ Supprimer",
            command=lambda r=record: self.delete_record(r),
            fg_color=self.main_app.colors['error']
        ).pack(side='left', padx=5)
    def show_details(self, record):
        details = (
            f"Record ID: {record.id}\n"
            f"Sensor ID: {record.sensor_id}\n"
            f"Encryption Type: {record.encryption_type}\n"
            f"Policy Text: {record.policy_text}\n"
            f"Attributes JSON: {record.attributes_json}\n"
            f"Storage Path: {record.storage_path}\n"
            f"Created At: {record.created_at}\n"
        )
        messagebox.showinfo("Détails du Record", details)
    def delete_record(self, record):
        if messagebox.askyesno(
            "Confirmation",
            "Supprimer ce record chiffré ?\nCette action est irréversible."
        ):
            if os.path.exists(record.storage_path):
                os.remove(record.storage_path)

            db.delete(record)
            db.commit()
            self.refresh_records()
            self.main_app.refresh_status_counts()
if __name__ == '__main__':
    app = App()
    app.mainloop()