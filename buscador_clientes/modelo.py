from dataclasses import dataclass, field


@dataclass
class Lead:
    nome: str
    nicho: str
    fonte: str
    endereco: str = ""
    cidade: str = ""
    telefone: str = ""
    site: str = ""
    email: str = ""
    instagram: str = ""
    facebook: str = ""
    youtube: str = ""
    tiktok: str = ""
    whatsapp: str = ""
    nota: float | None = None
    avaliacoes: int | None = None
    link_mapa: str = ""
    pontuacao: int = 0
    motivos: list[str] = field(default_factory=list)
    link_whatsapp: str = ""

    def chave(self):
        """Identifica o mesmo negócio vindo de buscas diferentes."""
        digitos = "".join(c for c in self.telefone if c.isdigit())[-8:]
        return (self.nome.strip().lower(), digitos or self.endereco.strip().lower())
