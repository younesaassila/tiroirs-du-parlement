import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

import roman
from tiroirs_du_parlement.config import DATA_PATH, OUTPUT_PATH
from tiroirs_du_parlement.schemas import ActeLegislatif, DossierParlementaire
from tiroirs_du_parlement.types import OrdreDuJour, StalledDossier, StalledDossierStep

_acte_code_regex = re.compile("^(?P<house>AN|SN)(?P<reading>[0-9]|[A-Z]+)$", re.I)


def _parse_json_file(path: Path) -> tuple[str, DossierParlementaire]:
    with open(path, "r", encoding="utf-8") as f:
        container = json.load(f)
    if "dossierParlementaire" not in container or not container["dossierParlementaire"]:
        raise ValueError(f"{path}: missing `dossierParlementaire`.")
    dossier: DossierParlementaire = container["dossierParlementaire"]
    if "uid" not in dossier or not dossier["uid"]:
        raise ValueError(f"{path}: missing `uid`.")
    return dossier["uid"], dossier


def _get_dossiers_dict(
    data_path: Path, roman_legislature: str
) -> dict[str, DossierParlementaire]:
    dossiers_dict: dict[str, DossierParlementaire] = {}

    if roman_legislature == "XIV":
        json_file = (
            data_path
            / f"Dossiers_Legislatifs_{roman_legislature}"
            / f"Dossiers_Legislatifs_{roman_legislature}.json"
        )
        print(
            f"Reading legislature {roman_legislature} data… (1 file)",
        )
        with open(json_file, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        dossiers: list[DossierParlementaire] = [
            container["dossierParlementaire"]
            for container in json_data["export"]["dossiersLegislatifs"]["dossier"]
        ]
        dossiers_dict = {dossier["uid"]: dossier for dossier in dossiers}
    else:
        json_path = (
            data_path
            / f"Dossiers_Legislatifs_{roman_legislature}"
            / "json"
            / "dossierParlementaire"
        )
        json_files = json_path.glob("*.json")
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(_parse_json_file, json_file) for json_file in json_files
            ]
            c = 0
            isatty = sys.stdout.isatty()
            if not isatty:
                print(
                    f"Reading legislature {roman_legislature} data… ({len(futures)} files)",
                )
            for future in as_completed(futures):
                uid, dossier = future.result()
                if uid in dossiers_dict:
                    raise ValueError(
                        f"Duplicate dossier législatif '{uid}' in legislature {roman_legislature}."
                    )
                dossiers_dict[uid] = dossier
                c += 1
                if isatty:
                    print(
                        f"{'' if c <= 1 else '\r'}Reading legislature {roman_legislature} data… ({c}/{len(futures)}){'' if c < len(futures) else '\n'}",
                        end="",
                        flush=True,
                    )

    return dossiers_dict


def _get_ordre_du_jour(data_path: Path) -> OrdreDuJour:
    ordre_du_jour: OrdreDuJour = {}
    with open(data_path / "OrdreDuJour_AN.html", "r", encoding="utf-8") as f:
        ordre_du_jour["AN"] = re.findall(
            '"/dyn/\\d+/dossiers/([^/"\\n]+)/?"', f.read(), re.I
        )
    with open(data_path / "OrdreDuJour_SN.html", "r", encoding="utf-8") as f:
        ordre_du_jour["SN"] = re.findall(
            '"https?://www.senat.fr/dossier-legislatif/([^/"\\n]+)/?"', f.read(), re.I
        )
    return ordre_du_jour


def _get_promulguees(data_path: Path) -> list[str]:
    promulguees: list[str] = []
    with open(data_path / "Promulguees.csv", "r", encoding="utf-8") as f:
        promulguees = re.findall(
            '"https?://www.senat.fr/dossier-legislatif/([^/"\\n]+)/?"', f.read(), re.I
        )
    return promulguees


def _is_dossier_in_ordre_du_jour(
    dossier: DossierParlementaire, ordre_du_jour: OrdreDuJour
) -> bool:
    filename_AN = (
        dossier["titreDossier"]["titreChemin"].lower()
        if "titreChemin" in dossier["titreDossier"]
        and dossier["titreDossier"]["titreChemin"]
        else None
    )
    filename_SN = (
        dossier["titreDossier"]["senatChemin"].rstrip("/").split("/")[-1].lower()
        if "senatChemin" in dossier["titreDossier"]
        and dossier["titreDossier"]["senatChemin"]
        else None
    )
    for filename in ordre_du_jour["AN"]:
        filename_lower = filename.lower()
        if dossier["uid"].lower() == filename_lower or (
            filename_AN and filename_AN == filename_lower
        ):
            return True
    if filename_SN and any(
        filename.lower() == filename_SN for filename in ordre_du_jour["SN"]
    ):
        return True

    return False


def _is_dossier_in_promulguees(
    dossier: DossierParlementaire, promulguees: list[str]
) -> bool:
    filename_SN = (
        dossier["titreDossier"]["senatChemin"].rstrip("/").split("/")[-1].lower()
        if "senatChemin" in dossier["titreDossier"]
        and dossier["titreDossier"]["senatChemin"]
        else None
    )
    if filename_SN and any(filename.lower() == filename_SN for filename in promulguees):
        return True

    return False


def _is_dossier_stalled(
    dossier: DossierParlementaire, ordre_du_jour: OrdreDuJour, promulguees: list[str]
) -> bool:
    if "actesLegislatifs" not in dossier or not dossier["actesLegislatifs"]:
        return False
    actes = dossier["actesLegislatifs"]["acteLegislatif"]
    if not isinstance(actes, list) or len(actes) < 2:
        return False

    if not all(
        _acte_code_regex.match(acte["codeActe"]) or acte["codeActe"] == "CMP"
        for acte in actes
    ):
        return False
    if actes[-1]["codeActe"] == "CMP":
        return False

    if "actesLegislatifs" in actes[-1] and actes[-1]["actesLegislatifs"]:
        latest_sub_actes = actes[-1]["actesLegislatifs"]["acteLegislatif"]
        if not isinstance(latest_sub_actes, list):
            latest_sub_actes = [latest_sub_actes]
        code_suffixes = {
            sub_acte["codeActe"].split("-", 1)[1].upper()
            for sub_acte in latest_sub_actes
            if "-" in sub_acte["codeActe"]
        }  # e.g. "DEPOT", "ACIN", "PROCACC", "COM", "DEBATS"
        if "DEBATS" in code_suffixes:
            return False

    if _is_dossier_in_ordre_du_jour(dossier, ordre_du_jour):
        return False

    if _is_dossier_in_promulguees(dossier, promulguees):
        return False

    return True


def _get_acte_filing_date(acte: ActeLegislatif) -> None | int:
    if "dateActe" in acte and acte["dateActe"]:
        return int(datetime.fromisoformat(acte["dateActe"]).timestamp() * 1000)
    if "actesLegislatifs" not in acte or not acte["actesLegislatifs"]:
        return None
    actes = acte["actesLegislatifs"]["acteLegislatif"]
    if not isinstance(actes, list):
        actes = [actes]
    if len(actes) == 0:
        return None
    return _get_acte_filing_date(
        next((a for a in actes if a["codeActe"].upper().endswith("-DEPOT")), actes[0])
    )


def _create_stalled_dossier_step(acte: ActeLegislatif) -> StalledDossierStep:
    legislature_match = re.match("^L(?P<legislature>\\d+)-", acte["uid"], re.I)
    if not legislature_match:
        raise ValueError(
            f"{acte["uid"]}: invalid `uid` '{acte["uid"]}' (missing legislature)."
        )
    legislature = legislature_match.group("legislature")
    code_match = _acte_code_regex.match(acte["codeActe"])
    if code_match is None:
        raise ValueError(f"{acte["uid"]}: invalid `codeActe` '{acte["codeActe"]}'.")
    house = str(code_match.group("house")).upper()
    if house not in ("AN", "SN"):
        raise ValueError(
            f"{acte["uid"]}: invalid house '{house}' in `codeActe` '{acte["codeActe"]}'."
        )
    reading = str(code_match.group("reading")).upper()
    filing_date = _get_acte_filing_date(acte)
    if filing_date is None:
        raise ValueError(f"{acte["uid"]}: missing `dateActe`.")

    return StalledDossierStep(
        uid=acte["uid"],
        legislature=legislature,
        house=house,
        reading=reading,
        filing_date=filing_date,
    )


def _create_stalled_dossier(
    dossier: DossierParlementaire, latest_legislature: str
) -> StalledDossier:
    if "actesLegislatifs" not in dossier or not dossier["actesLegislatifs"]:
        raise ValueError(f"{dossier["uid"]}: missing `actesLegislatifs`.")
    actes = dossier["actesLegislatifs"]["acteLegislatif"]
    if not isinstance(actes, list) or len(actes) < 2:
        raise ValueError(
            f"{dossier["uid"]}: invalid `actesLegislatifs` (must be a list with at least 2 items)."
        )
    if actes[-1]["codeActe"] == "CMP":
        raise ValueError(f"{dossier["uid"]}: last `acteLegislatif` must not be a CMP.")

    steps: list[StalledDossierStep] = []
    for acte in actes:
        if acte["codeActe"] == "CMP":
            continue  # CMPs are ignored
        try:
            steps.append(_create_stalled_dossier_step(acte))
        except ValueError as e:
            raise ValueError(f"{dossier["uid"]}: {e}") from e
    stalled_since = [
        step
        for step in steps
        if step.house == steps[-1].house and step.reading == steps[-1].reading
    ][0].filing_date
    lapsed = steps[-1].house == "AN" and steps[-1].legislature != latest_legislature
    link_AN = (
        f"http://www.assemblee-nationale.fr/dyn/{steps[-1].legislature}/dossiers/{dossier["titreDossier"]["titreChemin"]}"
        if "titreChemin" in dossier["titreDossier"]
        and dossier["titreDossier"]["titreChemin"]
        else None
    )
    link_SN = (
        dossier["titreDossier"]["senatChemin"]
        if "senatChemin" in dossier["titreDossier"]
        and dossier["titreDossier"]["senatChemin"]
        else None
    )

    return StalledDossier(
        uid=dossier["uid"],
        legislature=dossier["legislature"],
        procedure=dossier["procedureParlementaire"]["libelle"],
        title=dossier["titreDossier"]["titre"],
        stalled_by=steps[-1].house,
        stalled_since=stalled_since,
        reading=steps[-1].reading,
        lapsed=lapsed,
        steps=steps,
        link_AN=link_AN,
        link_SN=link_SN,
    )


def generate_output():
    # Read and parse dossiers législatifs
    if not DATA_PATH.is_dir():
        raise FileNotFoundError(
            "You must download the data before generating the output."
        )
    start_time = time.time()
    roman_legislatures = sorted(
        [f.name.split("_")[-1] for f in DATA_PATH.glob("Dossiers_Legislatifs_*")],
        key=lambda legislature: roman.fromRoman(legislature),
    )
    dossiers_dict: dict[str, DossierParlementaire] = {}
    for roman_legislature in roman_legislatures:
        legislature_dossiers_dict = _get_dossiers_dict(DATA_PATH, roman_legislature)
        if len(legislature_dossiers_dict) == 0:
            raise ValueError(
                f"No dossier législatif found for legislature {roman_legislature}."
            )
        dossiers_dict.update(legislature_dossiers_dict)
    print(
        f"Read {len(dossiers_dict)} dossiers législatifs in {(time.time() - start_time):.3f} seconds."
    )

    # Read and parse ordre du jour
    start_time = time.time()
    print("Parsing ordre du jour…")
    ordre_du_jour = _get_ordre_du_jour(DATA_PATH)
    print(f"Parsed ordre du jour in {(time.time() - start_time):.3f} seconds:")
    print(f"- Assemblée nationale: {len(ordre_du_jour['AN'])}")
    print(f"-               Sénat: {len(ordre_du_jour['SN'])}")

    # Read and parse promulguées
    start_time = time.time()
    print("Parsing promulguées…")
    promulguees = _get_promulguees(DATA_PATH)
    print(
        f"Parsed {len(promulguees)} promulguées in {(time.time() - start_time):.3f} seconds."
    )

    # Find stalled dossiers législatifs
    start_time = time.time()
    print("Finding stalled dossiers législatifs…")
    latest_legislature = str(roman.fromRoman(roman_legislatures[-1]))
    stalled_dossiers: list[StalledDossier] = []
    for dossier in dossiers_dict.values():
        if _is_dossier_stalled(dossier, ordre_du_jour, promulguees):
            stalled_dossiers.append(
                _create_stalled_dossier(dossier, latest_legislature)
            )
    print(
        f"Found {len(stalled_dossiers)} stalled dossiers législatifs in {(time.time() - start_time):.3f} seconds:"
    )
    print(
        f"- Assemblée nationale: {len([sd for sd in stalled_dossiers if sd.stalled_by == "AN"])}"
    )
    print(
        f"-               Sénat: {len([sd for sd in stalled_dossiers if sd.stalled_by == "SN"])}"
    )

    # Generate output JSON file
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "version": "1",
                "generated_at": int(time.time() * 1000),
                "stalled_dossiers": [asdict(sd) for sd in stalled_dossiers],
            },
            f,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    print(f"Generated `{OUTPUT_PATH}`.")


if __name__ == "__main__":
    generate_output()
