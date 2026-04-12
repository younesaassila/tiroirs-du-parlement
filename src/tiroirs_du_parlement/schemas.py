from typing import NotRequired, TypedDict

# Reference: https://data.assemblee-nationale.fr/autres/schemas/donnees-legislatives


class TitreDossier(TypedDict):
    titre: str
    titreChemin: NotRequired[None | str]
    senatChemin: NotRequired[None | str]


class ProcedureParlementaire(TypedDict):
    code: str  # In ref: int
    libelle: str


class Acteur(TypedDict):
    acteurRef: str
    mandatRef: str


class Acteurs(TypedDict):
    acteur: Acteur | list[Acteur]  # In ref: list[Acteur]


class IdOrganeEtRef(TypedDict):
    uid: str
    # In ref: type_reference: NotRequired[None | str]


class Organe(TypedDict):
    organeRef: IdOrganeEtRef


class Organes(TypedDict):
    organe: Organe | list[Organe]  # In ref: list[Organe]


class Initiateur(TypedDict):
    acteurs: NotRequired[None | Acteurs]
    organes: NotRequired[None | Organes]


class LibelleActe(TypedDict):
    nomCanonique: str
    libelleCourt: NotRequired[None | str]  # In ref: str


class ActeLegislatif(TypedDict):
    uid: str
    codeActe: str
    libelleActe: LibelleActe  # In ref: NotRequired[None | LibelleActe]
    organeRef: NotRequired[None | str]  # In ref: str
    dateActe: NotRequired[None | str]
    actesLegislatifs: NotRequired["None | ActesLegislatifs"]


class ActesLegislatifs(TypedDict):
    acteLegislatif: (
        ActeLegislatif | list[ActeLegislatif]
    )  # In ref: list[ActeLegislatif]


class Theme(TypedDict):
    libelleTheme: str
    # In ref: codeTheme: NotRequired[None | str]
    # In ref: themes: NotRequired["None | Themes"]


Themes = TypedDict(
    "Themes",
    {
        "theme": Theme | list[Theme],  # In ref: list[Theme]
        "@niveau": NotRequired[None | str],  # In ref: niveau: NotRequired[None | int]
    },
)


class MotsCles(TypedDict):
    motCle: list[str]


class Indexation(TypedDict):
    themes: Themes
    # In ref: motsCles: NotRequired[None | MotsCles]


class DossierParlementaire(TypedDict):
    uid: str
    legislature: str  # In ref: int
    titreDossier: TitreDossier
    procedureParlementaire: (
        ProcedureParlementaire  # In ref: NotRequired[None | ProcedureParlementaire]
    )
    initiateur: NotRequired[None | Initiateur]  # In ref: Initiateur
    actesLegislatifs: NotRequired[None | ActesLegislatifs]  # In ref: ActesLegislatifs
    indexation: NotRequired[None | Indexation]
