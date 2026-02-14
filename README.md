# 📊 Projet Big Data — CY Tech 2025

Ce dépôt contient un projet **Big Data** (CY Tech — 2025) organisé en exercices progressifs couvrant un pipeline complet :
**récupération** → **ingestion & cleaning** → **modélisation SQL** → **dashboard** → **service de prédiction ML**.

> 🧑‍🏫 **Projet réalisé sous l’encadrement de Rakib SHEIKH**
> GitHub : [https://github.com/Noobzik](https://github.com/Noobzik)

> 📦 Repository : `projet_big_data_cytech_25`

---

## 🧱 Structure du dépôt

```text
.
├── ex01_data_retrieval/
├── ex02_data_ingestion/
├── ex03_sql_table_creation/
├── ex04_dashboard/
├── ex05_ml_prediction_service/
├── ex06_airflow/
├── data/
├── docker-compose.yml
└── README.md
```

### 🎯 Rôle des modules

| Dossier                      | Objectif                                              | Livrable principal                |
| ---------------------------- | ----------------------------------------------------- | --------------------------------- |
| `ex01_data_retrieval`        | Récupération des données avec Spark                   | Lecture source + écriture parquet |
| `ex02_data_ingestion`        | Nettoyage et transformations (bronze → silver → gold) | Jobs Spark/Scala                  |
| `ex03_sql_table_creation`    | Modélisation SQL                                      | Tables, dimensions, faits         |
| `ex04_dashboard`             | Visualisation & analyse                               | Dashboard + KPI                   |
| `ex05_ml_prediction_service` | Service de prédiction ML                              | API REST + modèle                 |
| `ex06_airflow`               | Orchestration du pipeline                             | DAG Airflow                       |

---

## 🐳 Environnement Docker

Le projet repose sur **Docker Compose** pour fournir un environnement reproductible incluant **Spark** et **MinIO (S3 compatible)**.

### Prérequis

* Docker & Docker Compose
* Java / Scala (si exécution locale Spark)
* uv 0.9.26

### Lancer l’environnement

```bash
docker compose up -d
```

### Arrêter l’environnement

```bash
docker compose down
```

---

## 🪣 Stockage objet — MinIO

MinIO est utilisé comme backend **S3** pour stocker les datasets et résultats Spark.

* Console : [http://localhost:9001](http://localhost:9001)
* Endpoint S3 : [http://localhost:9000](http://localhost:9000)

Identifiants (par défaut) :

* **user** : `minio`
* **password** : `minio123`


## ⚡ Apache Spark (Scala)

Les exercices `ex01` et `ex02` sont implémentés en **Scala Spark**.

### Configuration S3A (MinIO)

```scala
import org.apache.spark.sql.SparkSession

val spark = SparkSession.builder()
  .appName("SparkApp")
  .config("fs.s3a.access.key", "minio")
  .config("fs.s3a.secret.key", "minio123")
  .config("fs.s3a.endpoint", "http://minio:9000")
  .config("fs.s3a.path.style.access", "true")
  .getOrCreate()

spark.sparkContext.setLogLevel("WARN")
```

---

## 🛢️ SQL & PostgreSQL (ex03)

Création des tables analytiques (dimensions & faits).

### Exécution d’un script SQL

```bash
psql -h localhost -p 5432 -U <user> -d <database> \
     -f ex03_sql_table_creation/<script>.sql
```

⚠️ **Important**

* `COPY FROM` → fichier côté serveur
* `\copy FROM` → fichier côté client (recommandé)

---

## 📈 Dashboard (ex04)

Ce module contient la couche **visualisation** :

* requêtes SQL analytiques
* KPI métiers
* graphiques (temps, zones, volumes, etc.)

---

## 🤖 Service de prédiction ML (ex05)


## 🔄 Orchestration avec Airflow (ex06)

Airflow orchestre l’ensemble du pipeline :

1. Récupération des données
2. Ingestion & nettoyage
3. Création des tables SQL
4. Mise à jour du dashboard
5. Entraînement / déploiement ML

Contenu attendu :

* DAG principal
* tâches ordonnées
* logs d’exécution

---

## ✅ Bonnes pratiques

* Un README par exercice
* Logs clairs (volumes, temps, erreurs)
* Validation qualité des données
* Versionnement des modèles ML
* Pipelines reproductibles

---

## 📝 Licence

Projet académique — **CY Tech 2025**

---

## 👤 Auteur

**Mohamed LIMAM**
GitHub : [https://github.com/LIMAMMohamedlimam](https://github.com/LIMAMMohamedlimam)
