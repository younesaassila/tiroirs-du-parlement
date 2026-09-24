# Tiroirs du Parlement

Propositions de loi adoptées par l'une des chambres du Parlement, toujours en attente d'inscription à l'ordre du jour de l'autre chambre.

<https://tiroirsduparlement.aassila.com/>

## Méthodologie

Les données des dossiers législatifs depuis la XIVe législature sont téléchargées depuis [le portail open data de l'Assemblée nationale](https://data.assemblee-nationale.fr/).

Sont retenus les dossiers législatifs :

- comportant au moins deux étapes de lecture ;
- dont les étapes de lecture se limitent à l'Assemblée nationale, le Sénat et la commission mixte paritaire ;
- dont la dernière étape de lecture n'est pas la commission mixte paritaire ;
- dont la dernière étape de lecture n'a pas fait l'objet d'une séance publique ;
- ne figurant pas à l'ordre du jour de l'Assemblée nationale ou du Sénat ;
- dont le texte n'a pas été promulgué (par précaution).

Sont marqués comme caducs les dossiers législatifs dont la dernière étape de lecture a eu lieu à l'Assemblée nationale au cours d'une législature antérieure à la législature en cours. [En savoir plus](https://www.senat.fr/connaitre-le-senat/role-et-fonctionnement/lapplication-des-regles-de-la-caducite-des-propositions-et-projets-de-loi-au-senat.html)

> Remarque : La retransmission par le Président du Sénat d'une proposition de loi d'origine sénatoriale à l'Assemblée nationale nouvellement élue constitue une nouvelle étape de lecture.

**⚠️ IMPORTANT :**

Les critères de sélection actuels ont plusieurs effets potentiellement contre-intuitifs :

- un dossier législatif dont le texte a été inscrit à l'ordre du jour à un moment donné, puis retiré ou reporté sans avoir été débattu en séance publique, reste **retenu** : seule l'absence du texte à l'ordre du jour _à la date d'extraction des données_ est vérifiée, indépendamment de ses inscriptions passées ;
- un dossier législatif dont la dernière étape de lecture a fait l'objet d'un débat en séance publique est **exclu**, y compris lorsque ce débat n'a pas abouti à un vote : c'est la tenue de la séance publique elle-même, et non son issue, qui détermine l'exclusion ;
- un dossier législatif dont la dernière étape de lecture est la commission mixte paritaire est **exclu**, y compris lorsque cette commission a abouti à un désaccord sans nouvelle lecture.

De plus, faute d'information disponible dans les données open data, les dossiers législatifs dont le texte a été retiré ou abandonné, ou dont les dispositions ont depuis été reprises dans d'autres textes promulgués, ne sont pas exclus (cf. [#2](https://github.com/younesaassila/tiroirs-du-parlement/issues/2)).

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
