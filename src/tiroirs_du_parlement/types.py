from dataclasses import dataclass
from typing import Literal, Optional

type Downloads = dict[str, str | Downloads]
type House = Literal["AN"] | Literal["SN"]
type OrdreDuJour = dict[House, list[str]]
type Reading = str  # e.g. "1", "2", "3", "NLEC", "LDEF"
type Timestamp = int  # Milliseconds since epoch


@dataclass(kw_only=True)
class DownloadMetadata:
    size: int
    etag: Optional[str]


@dataclass(frozen=True, kw_only=True)
class StalledDossierStep:
    uid: str
    legislature: str
    house: House
    reading: Reading  # If equals "NLEC", CMP took place
    filing_date: Timestamp


@dataclass(frozen=True, kw_only=True)
class StalledDossier:
    uid: str
    legislature: str
    procedure: str
    title: str
    stalled_by: House
    stalled_since: Timestamp
    reading: Reading
    lapsed: bool
    steps: list[StalledDossierStep]
    link_AN: Optional[str]
    link_SN: Optional[str]
