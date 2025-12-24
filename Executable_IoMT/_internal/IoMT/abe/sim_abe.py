
import json            # Pour sérialiser/désérialiser les métadonnées (JSON)
import base64          # Pour encoder les clés en Base64
import os
from cryptography.fernet import Fernet  # Chiffrement symétrique (AES + HMAC)
from typing import Tuple, Dict, Any


# ==========================================================
# SETUP : Initialisation du système ABE (Autorité de confiance)
# ==========================================================

def setup_abe():
    """
    Initialise le système ABE.
    Génère une clé maîtresse (wrapper_key) utilisée pour protéger
    les clés de données (data_key).
    """
    wrapper_key = Fernet.generate_key()
    return {'wrapper_key': wrapper_key}


# ==========================================================
# Fonctions internes : encapsulation / désencapsulation
# ==========================================================

def _wrap_message(wrapper_key: bytes, message: bytes) -> bytes:
    """
    Chiffre (encapsule) une clé de données avec la clé maîtresse.
    """
    f = Fernet(wrapper_key)
    return f.encrypt(message)


def _unwrap_message(wrapper_key: bytes, token: bytes) -> bytes:
    """
    Déchiffre (désencapsule) une clé de données.
    """
    f = Fernet(wrapper_key)
    return f.decrypt(token)


# ==========================================================
# =============== CP-ABE (Ciphertext-Policy) ================
# ==========================================================

def encrypt_cp(state: Dict[str, Any], policy_str: str, plaintext: bytes) -> Tuple[bytes, Dict]:
    """
    Chiffrement CP-ABE :
    - La politique d’accès est stockée dans le ciphertext.
    """

    # 1️ Génération d’une clé symétrique pour chiffrer les données
    data_key = Fernet.generate_key()
    f = Fernet(data_key)

    # 2️ Chiffrement du message
    ct = f.encrypt(plaintext)

    # 3️ Chiffrement de la clé de données avec la clé maîtresse
    wrapped_key = _wrap_message(state['wrapper_key'], data_key)

    # 4️ Métadonnées contenant la politique d’accès
    meta = {
        'policy': policy_str,
        'wrapped_key_b64': base64.b64encode(wrapped_key).decode()
    }

    # 5️ Construction du payload final
    payload = json.dumps(meta).encode() + b':::' + ct
    return payload, meta


def keygen_cp(state: Dict[str, Any], attributes: list) -> bytes:
    """
    Génération de la clé secrète CP-ABE :
    La clé contient les ATTRIBUTS de l’utilisateur.
    """
    clean_attrs = [a.replace(" ", "") for a in attributes]
    key_obj = {'attributes': clean_attrs}
    return json.dumps(key_obj).encode()


def decrypt_cp(state: Dict[str, Any], sk_blob: bytes, ct_blob: bytes) -> bytes:
    """
    Déchiffrement CP-ABE :
    L’utilisateur peut déchiffrer si ses attributs
    satisfont la politique du ciphertext.
    """
    try:
        # Charger les attributs de l’utilisateur
        keyobj = json.loads(sk_blob.decode())
        attrs = keyobj.get('attributes', [])

        # Séparer métadonnées et données chiffrées
        meta_raw, ct = ct_blob.split(b':::', 1)
        meta = json.loads(meta_raw.decode())

        policy = meta.get('policy', '')
        wrapped_key = base64.b64decode(meta.get('wrapped_key_b64'))

        # Vérifier la politique
        if not _policy_satisfied(policy, attrs):
            return None

        # Déchiffrement de la clé de données
        data_key = _unwrap_message(state['wrapper_key'], wrapped_key)

        # Déchiffrement du message
        f = Fernet(data_key)
        return f.decrypt(ct)

    except Exception:
        return None


#==========================================================
#=============== KP-ABE (Key-Policy) ======================
#==========================================================

def encrypt_kp(state: Dict[str, Any], attributes: list, plaintext: bytes) -> Tuple[bytes, Dict]:
    """
    Chiffrement KP-ABE :
    - Le ciphertext contient des ATTRIBUTS
    """
    data_key = Fernet.generate_key()
    f = Fernet(data_key)
    ct = f.encrypt(plaintext)

    wrapped_key = _wrap_message(state['wrapper_key'], data_key)

    meta = {
        'attributes': attributes,
        'wrapped_key_b64': base64.b64encode(wrapped_key).decode()
    }

    payload = json.dumps(meta).encode() + b':::' + ct
    return payload, meta


def keygen_kp(state: Dict[str, Any], policy_str: str) -> bytes:
    """
    Génération de la clé secrète KP-ABE :
    La clé contient la POLITIQUE d’accès.
    """
    keyobj = {'policy': policy_str}
    return json.dumps(keyobj).encode()


def decrypt_kp(state: Dict[str, Any], sk_blob: bytes, ct_blob: bytes) -> bytes:
    """
    Déchiffrement KP-ABE :
    L’accès dépend de la politique de la clé.
    """
    try:
        keyobj = json.loads(sk_blob.decode())
        policy = keyobj.get('policy', '')

        meta_raw, ct = ct_blob.split(b':::', 1)
        meta = json.loads(meta_raw.decode())
        attrs = meta.get('attributes', [])

        if not _policy_satisfied(policy, attrs):
            return None

        wrapped_key = base64.b64decode(meta.get('wrapped_key_b64'))
        data_key = _unwrap_message(state['wrapper_key'], wrapped_key)

        f = Fernet(data_key)
        return f.decrypt(ct)

    except Exception:
        return None


# ==========================================================
# ÉVALUATION DE LA POLITIQUE D’ACCÈS
# ==========================================================

def _policy_satisfied(policy_str: str, attrs_list: list) -> bool:
    """
    Vérifie si une liste d’attributs satisfait une politique logique.
    Politique valide = expression booléenne (and / or / parenthèses).
    """

    # Refuser policy vide
    if not policy_str or policy_str.strip() == '':
        return False

    expr = policy_str.lower().strip()

    # Refuser JSON / listes / objets
    if expr.startswith('[') or expr.startswith('{'):
        return False

    aset = set(a.lower() for a in attrs_list)

    import re

    # Extraire uniquement les attributs (ex: role:medecin)
    tokens = re.findall(r'[\w:]+', expr)
    tokens = [t for t in tokens if ':' in t]

    replaced = expr
    for t in set(tokens):
        replaced = re.sub(
            r'\b' + re.escape(t) + r'\b',
            str(t in aset),
            replaced
        )

    # Normalisation Python
    safe = (
        replaced
        .replace('true', 'True')
        .replace('false', 'False')
    )

    # Sécurité finale : pas de listes
    if '[' in safe or ']' in safe or '{' in safe or '}' in safe:
        return False

    try:
        result = eval(safe)
        # Accepter UNIQUEMENT un booléen True
        return isinstance(result, bool) and result
    except Exception:
        return False
