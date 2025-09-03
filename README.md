# Projet de Détection de Cyberintimidation et de Harcèlement

## 1. Introduction

Ce projet vise à développer un système de détection de cyberintimidation et de harcèlement en ligne. Il intègre plusieurs étapes, allant de l'ingestion de données brutes à l'analyse avancée du langage naturel (NLP) et à l'indexation dans une base de données de recherche pour une exploration efficace. L'objectif est de traiter des textes pour identifier des comportements potentiellement nuisibles et de les rendre interrogeables pour des analyses ultérieures.

## 2. Architecture du Projet

Le projet est structuré en plusieurs modules Python, chacun ayant une responsabilité spécifique dans le pipeline de traitement des données. L'architecture est conçue pour être modulaire, permettant une maintenance et une extension faciles. Les données transitent d'un fichier CSV vers MongoDB, puis sont enrichies par des analyses NLP avant d'être indexées dans Elasticsearch.

```mermaid
graph TD
    A[Fichier CSV (Données Brutes)] --> B(scraper.py)
    B --> C[MongoDB (Données Brutes et Nettoyées)]
    C --> D(preprocessing.py)
    D --> E[MongoDB (Données Prétraitées)]
    E --> F(nlp_pipeline.py)
    F --> G[MongoDB (Données Enrichies NLP)]
    G --> H(es_ingest.py)
    H --> I[Elasticsearch (Données Indexées pour Recherche)]
```

## 3. Configuration de l'Environnement

### Prérequis

Avant de lancer le projet, assurez-vous d'avoir les éléments suivants installés sur votre système :

*   **Python 3.x**
*   **MongoDB** : Une instance de MongoDB doit être en cours d'exécution (généralement sur `mongodb://localhost:27017/`).
*   **Elasticsearch** : Une instance d'Elasticsearch doit être en cours d'exécution (généralement sur `http://localhost:9200`).

### Installation des Dépendances



**Note sur NLTK** : Après l'installation de `nltk`, vous devrez télécharger certains de ses corpus. Exécutez le script Python suivant une fois :

```python
import nltk
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('averaged_perceptron_tagger')
```

## 4. Composants du Projet

Chaque script Python joue un rôle crucial dans le pipeline de traitement des données.

### Scraper (`scraper.py`)

Ce script est responsable de l'ingestion initiale des données à partir d'un fichier CSV et de leur chargement dans MongoDB. Il effectue également des opérations de nettoyage et de normalisation de base sur les données brutes.

**Fonctionnalités clés :**

*   **`load_data()`** : Charge les données depuis le fichier CSV spécifié par `DATA_PATH`.
*   **`drop_duplicate_rows()`** : Supprime les lignes en double du DataFrame.
*   **`normalize_types()` et `normalize_label()`** : Fonctions utilitaires pour normaliser les valeurs des colonnes 'Types' et 'Label'.
*   **`apply_function()`** : Applique une fonction donnée à une colonne spécifique du DataFrame.
*   **`generate_post_time()`** : Génère des horodatages aléatoires pour les publications, simulant une distribution réaliste.
*   **`insert_to_mongo()`** : Insère les données traitées dans une collection MongoDB nommée `posts` dans la base de données `harcelement`.

**Choix Techniques :**

*   Utilisation de `pandas` pour la manipulation des données tabulaires.
*   `pymongo` pour l'interaction avec MongoDB.

### Prétraitement (`preprocessing.py`)

Ce module se concentre sur le nettoyage et le prétraitement du texte pour préparer les données à l'analyse NLP. Il est conçu pour être exécuté après l'ingestion des données par le scraper.

**Classe `TextPreprocessor` :**

*   **`clean_html()`** : Supprime les balises HTML du texte.
*   **`clean_urls()`** : Supprime les URLs du texte.
*   **`clean_special_chars()`** : Supprime les caractères spéciaux et les espaces supplémentaires.
*   **`remove_punctuation_and_digits()`** : Supprime la ponctuation et les chiffres.
*   **`remove_stopwords()`** : Supprime les mots vides (stop words) en utilisant le corpus NLTK.
*   **`lemmatize_tokens()`** : Applique la lemmatisation aux tokens pour réduire les mots à leur forme de base, en utilisant `WordNetLemmatizer` et le `pos_tag` pour une lemmatisation plus précise.
*   **`preprocess_text()`** : La fonction principale qui orchestre toutes les étapes de prétraitement du texte.

**Classe `MongoPreprocessor` :**

*   **`preprocess_collection()`** : Parcourt la collection MongoDB, applique le prétraitement à la colonne de texte originale et met à jour les documents avec les champs `original_text` et `preprocessed_text`.

**Choix Techniques :**

*   `nltk` pour la tokenisation, la suppression des mots vides et la lemmatisation.
*   `BeautifulSoup` pour le nettoyage HTML.
*   `re` (expressions régulières) pour le nettoyage de motifs spécifiques (URLs, caractères spéciaux).

### Pipeline NLP (`nlp_pipeline.py`)

Ce script applique diverses techniques de traitement du langage naturel aux textes prétraités stockés dans MongoDB. Il enrichit les documents avec des informations telles que la langue, le sentiment et un score de toxicité.

**Classe `NLPPipeline` :**

*   **`detect_language()`** : Détecte la langue du texte en utilisant une approche hybride avec `langdetect` et `langid` pour une robustesse accrue.
*   **`analyze_sentiment()`** : Effectue une analyse de sentiment en combinant `TextBlob` (pour la polarité et la subjectivité) et `VADER` (pour un score composé de sentiment). Le score VADER est utilisé pour classer le sentiment en positif, négatif ou neutre.
*   **`calculate_toxicity_score()`** : Calcule un score de toxicité basé sur le label fourni (Bullying/Not Bullying) et le score VADER. Ce score est une heuristique qui peut être affinée.
*   **`process_document()`** : Traite un seul document en appliquant la détection de langue, l'analyse de sentiment et le calcul du score de toxicité.
*   **`process_collection()`** : Parcourt la collection MongoDB par lots, applique le traitement NLP à chaque document et met à jour les documents dans la base de données.
*   **`get_analysis_summary()`** : Fournit un résumé statistique des analyses NLP effectuées, y compris la distribution des sentiments et des langues.

**Choix Techniques :**

*   `pymongo` pour l'interaction avec MongoDB.
*   `textblob` pour l'analyse de sentiment générale.
*   `vaderSentiment` pour l'analyse de sentiment spécifique aux médias sociaux.
*   `langdetect` et `langid` pour la détection de langue robuste.
*   `tqdm` pour afficher une barre de progression lors du traitement des collections.

### Ingestion Elasticsearch (`es_ingest.py`)

Ce script est la dernière étape du pipeline, responsable du transfert des données enrichies de MongoDB vers Elasticsearch. Il configure l'index Elasticsearch, transforme les documents et effectue une ingestion en masse.

**Classe `ElasticsearchIngestor` :**

*   **`__init__()`** : Initialise les connexions à Elasticsearch et MongoDB.
*   **`create_index_mapping()`** : Crée un index Elasticsearch avec un mappage prédéfini qui spécifie les types de données pour chaque champ (par exemple, `text`, `keyword`, `float`, `date`). Il supprime l'index existant s'il y en a un avant de le recréer.
*   **`transform_document()`** : Transforme un document MongoDB en un format adapté à Elasticsearch, en gérant les types de données et en générant des champs si nécessaire (par exemple, un titre basé sur l'ID du post, un auteur anonyme, une URL factice).
*   **`bulk_index_documents()`** : Effectue l'ingestion en masse des documents de MongoDB vers Elasticsearch en utilisant `helpers.parallel_bulk` pour des performances optimales.
*   **`verify_indexing()`** : Vérifie que les documents ont été correctement indexés dans Elasticsearch et renvoie des statistiques et des exemples de documents.
*   **`create_sample_queries()`** : Crée et exécute des requêtes d'exemple sur l'index Elasticsearch pour démontrer les capacités de recherche (par exemple, posts à haute toxicité, sentiment négatif, posts de cyberintimidation).

**Choix Techniques :**

*   `elasticsearch-py` pour l'interaction avec Elasticsearch.
*   `pymongo` pour la lecture des données depuis MongoDB.
*   `helpers.parallel_bulk` pour une ingestion efficace et performante.

## 5. Flux d'Exécution

Pour exécuter le pipeline complet, vous devez lancer les scripts dans l'ordre suivant :

1.  **Exécuter le scraper :**
    ```bash
    python scraper.py
    ```
    Cela chargera les données du CSV dans MongoDB.

2.  **Exécuter le script de prétraitement :**
    ```bash
    python preprocessing.py
    ```
    Cela nettoiera et prétraitera les textes dans MongoDB.

3.  **Exécuter le pipeline NLP :**
    ```bash
    python nlp_pipeline.py
    ```
    Cela effectuera l'analyse NLP et mettra à jour les documents dans MongoDB.

4.  **Exécuter le script d'ingestion Elasticsearch :**
    ```bash
    python es_ingest.py
    ```
    Cela transférera les données enrichies de MongoDB vers Elasticsearch.

Chaque script est conçu pour être exécuté indépendamment, mais ils dépendent des étapes précédentes pour que les données soient disponibles et dans le bon format.

## 6. Choix Techniques

### MongoDB

**Raison du choix :** MongoDB est une base de données NoSQL orientée document, ce qui la rend très flexible pour stocker des données semi-structurées comme des publications de médias sociaux. Sa nature sans schéma permet d'ajouter facilement de nouveaux champs (par exemple, les résultats de l'analyse NLP) aux documents existants sans nécessiter de migrations complexes. Elle est également bien adaptée pour servir de zone de transit pour les données entre les différentes étapes du pipeline.

### Elasticsearch

**Raison du choix :** Elasticsearch est un moteur de recherche et d'analyse distribué. Il est idéal pour indexer de grandes quantités de données textuelles et les rendre rapidement interrogeables. Pour un projet de détection de cyberintimidation, Elasticsearch permet de rechercher efficacement des publications par mots-clés, sentiment, score de toxicité ou d'autres attributs NLP, ce qui est crucial pour l'exploration et l'analyse des données.

### TextBlob et VADER

**Raison du choix :**

*   **TextBlob** : Fournit une API simple pour les tâches NLP courantes, y compris l'analyse de sentiment (polarité et subjectivité). Il est facile à utiliser et offre une bonne base pour l'analyse de sentiment générale.
*   **VADER (Valence Aware Dictionary and sEntiment Reasoner)** : Est spécifiquement conçu pour l'analyse de sentiment sur les textes des médias sociaux. Il est sensible à la valence, à l'intensité et au contexte, ce qui le rend particulièrement efficace pour les données informelles et courtes souvent trouvées en ligne. La combinaison des deux permet une analyse de sentiment plus complète et nuancée.

### Langdetect et Langid

**Raison du choix :** La détection de langue est une étape cruciale pour s'assurer que les outils NLP sont appliqués correctement (par exemple, les stop words et la lemmatisation sont spécifiques à la langue). L'utilisation combinée de `langdetect` et `langid` offre une robustesse accrue. `langdetect` est souvent rapide et précis pour de nombreux cas, tandis que `langid` peut offrir une meilleure performance sur des textes plus courts ou plus complexes, et leur combinaison permet de gérer une plus grande variété de scénarios de détection de langue.

## 7. Utilisation

Pour utiliser ce projet, suivez les étapes de configuration de l'environnement et le flux d'exécution décrits ci-dessus. Assurez-vous que vos instances MongoDB et Elasticsearch sont en cours d'exécution avant de lancer les scripts.

Vous pouvez modifier le fichier `scraper.py` pour pointer vers votre propre fichier CSV de données brutes en ajustant la variable `DATA_PATH`.

## 8. Structure des Données

Les documents stockés dans MongoDB et indexés dans Elasticsearch ont la structure suivante après le traitement NLP et le prétraitement :

```json
{
    "_id": "<ObjectId de MongoDB>",
    "Id_post": "<ID unique du post>",
    "Text": "<Texte original du post (tel que lu du CSV)>",
    "Label": "<Label original du post (e.g., 'B' pour Bullying, 'NB' pour Not Bullying)>",
    "Types": "<Type original de harcèlement (e.g., 'religion', 'ethnicity')>",
    "original_text": "<Texte original après nettoyage initial (HTML, URLs)>",
    "preprocessed_text": "<Texte après prétraitement (minuscules, sans ponctuation, stop words, lemmatisation)>",
    "created_at": "<Date et heure de création du post>",
    "language": "<Langue détectée du post (e.g., 'en', 'fr')>",
    "sentiment": "<Sentiment général du post ('positive', 'negative', 'neutral')>",
    "polarity": "<Score de polarité TextBlob (-1.0 à 1.0)>",
    "subjectivity": "<Score de subjectivité TextBlob (0.0 à 1.0)>",
    "vader_compound": "<Score composé VADER (-1.0 à 1.0)>",
    "toxicity_score": "<Score de toxicité calculé (0.0 à 1.0)>",
    "nlp_processed_at": "<Date et heure du dernier traitement NLP>"
}
```
## 10. Tableau de Bord Kibana

Une fois les données ingérées dans Elasticsearch, vous pouvez créer un tableau de bord interactif dans Kibana pour visualiser et explorer les données de cyberintimidation et de harcèlement. Voici les éléments clés à inclure dans votre tableau de bord :

### Composants du Tableau de Bord

**Répartition des langues :** Un graphique (par exemple, un graphique à barres ou un graphique circulaire) montrant la distribution des langues détectées dans les publications. Cela permet d'identifier les langues prédominantes et d'adapter les stratégies d'analyse si nécessaire.

**Répartition des sentiments :** Un graphique (par exemple, un graphique à barres ou un graphique circulaire) illustrant la proportion de publications classées comme positives, négatives ou neutres. Cela offre un aperçu rapide de la tonalité générale des discussions.

•
**Évolution temporelle des publications :** Un graphique linéaire ou en aires montrant le nombre de publications au fil du temps. Cela peut aider à identifier des pics d'activité, des tendances ou des événements spécifiques qui ont pu influencer le volume de contenu.

**Liste des contenus les plus négatifs / toxiques :** Un tableau affichant les publications ayant les scores de toxicité ou de sentiment négatif les plus élevés. Ce tableau devrait inclure le texte original, le score de toxicité, le sentiment, et potentiellement d'autres métadonnées pertinentes comme la date ou l'auteur. Cela permet une revue rapide des contenus les plus préoccupants.

### Filtres Interactifs

Pour une exploration dynamique des données, le tableau de bord devrait inclure les filtres interactifs suivants :

**Langue :** Permet de filtrer les publications par langue spécifique.

**Score (Toxicité, Polarité, VADER) :** Permet de filtrer les publications en fonction de leurs scores numériques (par exemple, afficher uniquement les publications avec un score de toxicité supérieur à un certain seuil).

**Date :** Permet de filtrer les publications par période (par exemple, les dernières 24 heures, la semaine dernière, un intervalle de dates personnalisé).

**Source :** Si des sources différentes sont identifiées (par exemple, différentes plateformes de médias sociaux), un filtre par source peut être utile.

### Création dans Kibana

**1.Accéder à Kibana :** Ouvrez votre interface Kibana (sur http://localhost:5601).

**2.Créer un Index Pattern :** Assurez-vous d'avoir un index pattern configuré pour votre index Elasticsearch (harcelement_posts par défaut).

**3.Créer des Visualisations :** Utilisez l'onglet "Visualize" pour créer les graphiques et tableaux mentionnés ci-dessus en utilisant les champs disponibles dans votre index Elasticsearch (par exemple, language.keyword, sentiment.keyword, created_at, toxicity_score, contenu).

**4.Construire le Tableau de Bord :** Dans l'onglet "Dashboard", créez un nouveau tableau de bord et ajoutez-y toutes les visualisations créées. Organisez-les de manière logique et ajoutez les contrôles de filtre nécessaires.


**Note :** Certains champs comme `Id_post`, `Text`, `Label`, `Types` proviennent directement du fichier CSV initial. Les champs `original_text`, `preprocessed_text`, `created_at`, `language`, `sentiment`, `polarity`, `subjectivity`, `vader_compound`, `toxicity_score`, et `nlp_processed_at` sont ajoutés ou mis à jour par les scripts de prétraitement et NLP.




