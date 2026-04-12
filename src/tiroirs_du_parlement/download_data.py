import importlib.metadata
import json
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import asdict
from email.headerregistry import ContentTypeHeader
from email.policy import EmailPolicy
from io import BytesIO
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import requests

from tiroirs_du_parlement.config import DATA_PATH, META_PATH
from tiroirs_du_parlement.types import DownloadMetadata, Downloads

_downloads: Downloads = {
    # "Dossiers_Legislatifs_XII": {
    #     "tableau.html": "https://www.assemblee-nationale.fr/12/documents/tableau-ban.asp",
    # },
    # "Dossiers_Legislatifs_XIII": {
    #     "tableau_0708.html": "https://www.assemblee-nationale.fr/13/documents/tableau-ban_0708.asp",
    #     "tableau_0809.html": "https://www.assemblee-nationale.fr/13/documents/tableau-ban_0809.asp",
    #     "tableau_0910.html": "https://www.assemblee-nationale.fr/13/documents/tableau-ban_0910.asp",
    #     "tableau_1011.html": "https://www.assemblee-nationale.fr/13/documents/tableau-ban_1011.asp",
    #     "tableau_1112.html": "https://www.assemblee-nationale.fr/13/documents/tableau-ban.asp",
    # },
    "Dossiers_Legislatifs_XIV": "https://data.assemblee-nationale.fr/static/openData/repository/14/loi/dossiers_legislatifs/Dossiers_Legislatifs_XIV.json.zip",
    "Dossiers_Legislatifs_XV": "https://data.assemblee-nationale.fr/static/openData/repository/15/loi/dossiers_legislatifs/Dossiers_Legislatifs_XV.json.zip",
    "Dossiers_Legislatifs_XVI": "https://data.assemblee-nationale.fr/static/openData/repository/16/loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip",
    "Dossiers_Legislatifs_XVII": "https://data.assemblee-nationale.fr/static/openData/repository/17/loi/dossiers_legislatifs/Dossiers_Legislatifs.json.zip",
    "OrdreDuJour_AN.html": "https://www.assemblee-nationale.fr/dyn/seance-publique/textes-inscrits-ordre-du-jour",
    "OrdreDuJour_SN.html": "https://www.senat.fr/ordre-du-jour/ordre-du-jour.html",
    "Promulguees.csv": "https://data.senat.fr/data/dosleg/promulguees.csv",
}


# From https://stackoverflow.com/a/77225775
def _parse_content_type(content_type: str) -> tuple[str, dict[str, Any]]:
    header: ContentTypeHeader = EmailPolicy.header_factory("Content-Type", content_type)
    return header.content_type, dict(header.params)


def _process_zip(path: Path, data: bytes, meta: DownloadMetadata) -> DownloadMetadata:
    print(f"Extracting `{path}`…")
    with ZipFile(BytesIO(data)) as archive:
        archive.extractall(path)
        meta.size = sum(zinfo.file_size for zinfo in archive.infolist())
    print(f"Extracted `{path}` ({meta.size / (1000 * 1000)} MB).")
    return meta


def _process_text(path: Path, data: str, meta: DownloadMetadata) -> DownloadMetadata:
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)
    meta.size = path.stat().st_size
    print(f"Wrote `{path}` ({meta.size / 1000} KB).")
    return meta


def _download_file(
    session: requests.Session,
    executor: ThreadPoolExecutor,
    path: Path,
    url: str,
    meta: DownloadMetadata,
) -> Future[DownloadMetadata]:
    print(f"Downloading `{path}`…")

    headers = {"If-None-Match": meta.etag} if meta.etag else {}
    with session.get(url, headers=headers, stream=True) as r:
        r.raise_for_status()
        if "ETag" in r.headers:
            meta.etag = r.headers["ETag"]
        if r.status_code == 304:
            print(f"Skipped `{path}`: already up to date.")
            future = executor.submit(lambda: meta)
        else:
            content_type = _parse_content_type(r.headers["Content-Type"])
            match content_type[0]:
                case "application/zip":
                    data = r.content
                    print(f"Downloaded `{path}`.")
                    future = executor.submit(_process_zip, path, data, meta)
                case "text/html" | "text/csv":
                    data = r.text
                    print(f"Downloaded `{path}`.")
                    future = executor.submit(_process_text, path, data, meta)
                case _:
                    raise ValueError(
                        f"Unsupported content type '{content_type[0]}' for `{path}`."
                    )

    return future


def _download_dir(
    session: requests.Session,
    executor: ThreadPoolExecutor,
    future_to_url: dict[Future[DownloadMetadata], str],
    path: Path,
    downloads: Downloads,
    meta_dict: dict[str, DownloadMetadata],
) -> None:
    path.mkdir(parents=True, exist_ok=True)

    for name, target in downloads.items():
        if isinstance(target, str):
            future = _download_file(
                session=session,
                executor=executor,
                path=path / name,
                url=target,
                meta=meta_dict.get(target, DownloadMetadata(size=0, etag=None)),
            )
            future_to_url[future] = target
        else:
            _download_dir(
                session=session,
                executor=executor,
                future_to_url=future_to_url,
                path=path / name,
                downloads=target,
                meta_dict=meta_dict,
            )


def download_data():
    DATA_PATH.mkdir(parents=True, exist_ok=True)

    # Load download metadata
    meta_dict: dict[str, DownloadMetadata] = {}
    if META_PATH.is_file():
        with open(META_PATH, "r", encoding="utf-8") as f:
            meta_dict = {k: DownloadMetadata(**v) for k, v in json.load(f).items()}
        print(f"Loaded download metadata from `{META_PATH}`.")

    # Download all data
    start_time = time.time()
    with requests.Session() as session, ThreadPoolExecutor() as executor:
        session.headers.update(
            {
                "User-Agent": f"TiroirsDuParlement/{importlib.metadata.version('tiroirs_du_parlement')}"
            }
        )
        future_to_url: dict[Future[DownloadMetadata], str] = {}
        _download_dir(
            session=session,
            executor=executor,
            future_to_url=future_to_url,
            path=DATA_PATH,
            downloads=_downloads,
            meta_dict=meta_dict,
        )
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            meta_dict[url] = future.result()
    total_mb = sum(m.size for m in meta_dict.values()) / (1000 * 1000)
    print(
        f"Downloaded all data ({total_mb} MB) in {(time.time() - start_time):.3f} seconds."
    )

    # Save download metadata
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {k: asdict(v) for k, v in meta_dict.items()},
            f,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    print(f"Saved download metadata to `{META_PATH}`.")


if __name__ == "__main__":
    download_data()
