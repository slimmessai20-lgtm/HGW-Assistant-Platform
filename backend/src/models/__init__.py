from pydantic import BaseModel


class TelnetRequest(BaseModel):
    """Modèle pour les requêtes Telnet centralisé.

    Champs:
    - host: adresse IP ou hostname
    - port: port Telnet (par défaut 23)
    - user: nom d'utilisateur
    - password: mot de passe
    """
    host: str
    port: int = 23
    user: str
    password: str

__all__ = ["TelnetRequest"]
