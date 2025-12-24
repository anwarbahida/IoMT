from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Text, create_engine
from sqlalchemy.orm import sessionmaker
import datetime, os, sys

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    role = Column(String, nullable=True)

class Attribute(Base):
    __tablename__ = "attributes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    name = Column(String)
    value = Column(String)

class ABEKey(Base):
    __tablename__ = "abe_keys"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    key_type = Column(String)
    private_key_blob = Column(Text)
    policy_blob = Column(Text)

class Record(Base):
    __tablename__ = "records"
    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String)
    storage_path = Column(String)
    encryption_type = Column(String)
    policy_text = Column(Text)
    attributes_json = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def get_session(db_path=None):
    # 🔍 Déterminer si le script est exécuté en mode exécutable (.exe) ou en mode normal
    if getattr(sys, 'frozen', False):
        # Mode .exe → placer la base dans le même dossier que l’exécutable
        base_dir = os.path.dirname(sys.executable)
    else:
        # Mode développement → dossier du fichier Python
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # 📁 Chemin par défaut de la base de données
    if db_path is None:
        db_path = os.path.join(base_dir, 'data.db')

    # 🔌 Connexion SQLite
    engine = create_engine('sqlite:///' + db_path, connect_args={'check_same_thread': False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)

    return SessionLocal()
