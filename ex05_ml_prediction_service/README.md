# 🚖 Prédiction du montant des courses NYC Taxi

Ce projet implémente un **pipeline de Machine Learning** pour prédire le montant total (`total_amount`) des courses de taxis jaunes à New York.
Il prend en charge **l’entraînement d’un modèle de régression** ainsi que **l’inférence batch** sur des fichiers **CSV, JSON et JSONL**.

---

## 📋 Structure du projet

L’architecture du code est organisée dans le dossier `src/` :

* **`src/train.py`**
  Pipeline d’entraînement complet :

  * chargement des données (local ou S3/MinIO)
  * validation
  * feature engineering
  * split train / test
  * entraînement
  * évaluation (RMSE)
  * sauvegarde des artefacts

* **`src/predict.py`**
  Script d’inférence batch 

* **`src/features.py`**
  Logique d’ingénierie des features (features temporelles, durée de trajet, normalisation).

* **`src/validate.py`**
  Validation stricte des données (schéma, types, contraintes métier).

* **`src/io_minio.py`**
  Module d’entrées/sorties compatible avec les chemins locaux et les URIs **S3/MinIO** (`s3://...`).

* **`schema.json`** : Définition des features (numériques / catégorielles) et de la cible.

* **`metrics.json`** : Fichier généré contenant les performances du modèle.

---

## 🛠️ Installation

```bash
# Cloner le dépôt
git clone https://github.com/LIMAMMohamedlimam/projet_big_data_cytech_25.git
cd projet_big_data_cytech_25/ex05_ml_prediction_service

# Installer les dépendances
uv pip intasll -r requirements.txt
```

**Dépendances principales** :

* `pandas`
* `numpy`
* `scikit-learn`
* `joblib`
* `tqdm`
* `s3fs` (support S3 / MinIO)

---

## 🎯 Prérequis des données

### Colonnes minimales (obligatoires)

Le fichier d’entrée doit contenir :

* `tpep_pickup_datetime` : date et heure de prise en charge
* `trip_distance` : distance du trajet
* `PULocationID` : zone de départ
* `DOLocationID` : zone d’arrivée

### Colonnes optionnelles (recommandées)

Ces colonnes améliorent la précision du modèle :

* `tpep_dropoff_datetime` (calcul de `trip_duration_min`)
* `passenger_count`
* `VendorID`
* `RatecodeID`
* `store_and_fwd_flag`
* `payment_type`

> ⚠️ **Note** : pour l’entraînement, la colonne cible **`total_amount`** est obligatoire.

---

## 🚀 Entraînement du modèle

### Depuis un fichier local

```bash
uv venv .venv
uv pip install -r requirements.txt
uv run src.train --data /chemin/vers/fichier.parquet
```

### Depuis MinIO / S3

Configurer l’environnement :

```bash
export MINIO_ENDPOINT_URL=http://localhost:9000
export MINIO_ACCESS_KEY=votre_access_key
export MINIO_SECRET_KEY=votre_secret_key
export MINIO_REGION=us-east-1  # optionnel
```

Puis lancer l’entraînement :

```bash
uv run src.train --data s3://mon-bucket/yellow_tripdata.parquet
```

### Plus d'options 

```bash
uv run  src.train \
  --data data/yellow.parquet \
  --max-rows 300000 \
  --test-size 0.2 \
  --seed 42
```

#### Paramètres

| Paramètre     | Description                                       | Défaut |
| ------------- | ------------------------------------------------- | ------ |
| `--data`      | Chemin vers le fichier parquet (local ou `s3://`) | Requis |
| `--max-rows`  | Nombre max de lignes (0 = tout)                   | 300000 |
| `--test-size` | Proportion du jeu de test                         | 0.2    |
| `--seed`      | Graine aléatoire pour reproductibilité            | 42     |

### Artefacts générés

* Modèle sérialisé (`joblib`)
* `metrics.json` (RMSE, tailles des jeux de données)
* `schema.json` (features utilisées)

---

## 🔮 Prédictions batch

Formats supportés : **`.csv`**, **`.json`** (array) et **`.jsonl`** (NDJSON).

### Commande de base

```bash
uv run src.predict --input sample.csv --output predictions.csv
```

### Exemples

**CSV → CSV**

```bash
uv run src.predict --input donnees.csv --output resultats.csv
```

**JSON Lines → JSON Lines**

```bash
uv run src.predict --input donnees.jsonl --output resultats.jsonl
```

**JSON → CSV**

```bash
uv run src.predict --input donnees.json --output resultats.csv
```

Le fichier de sortie contient **toutes les colonnes d’origine + `pred_total_amount`**.

---
