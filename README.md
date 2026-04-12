# Tiroirs du Parlement

Propositions de loi adoptées par l'une des chambres du Parlement, toujours en attente d'inscription à l'ordre du jour de l'autre chambre.

## Prérequis

- [Python](https://www.python.org/) 3.12 ou ultérieur
- [Poetry](https://python-poetry.org/) 2.2 ou ultérieur

## Installation

### Dépendances

```powershell
poetry install --with dev
```

### Données

```powershell
poetry run download_data
```

## Utilisation

```powershell
poetry run generate_output
```

Résultat enregistré dans `dist/output.json`.

## Développement

```powershell
poetry run serve_website
```
