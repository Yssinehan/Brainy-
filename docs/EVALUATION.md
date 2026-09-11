# Évaluation

Brainy ne publie aucune métrique sans jeu de vérité terrain. Les fonctions dans
`brainy.eval.metrics` calculent Precision@K, Recall@K, MRR et NDCG à partir de
chunks pertinents explicitement étiquetés pour chaque requête.

Pour comparer Vector RAG, Hybrid RAG et Hybrid RAG + Knowledge Graph, utiliser le
même corpus, les mêmes requêtes étiquetées, le même `K` et la même machine. Mesurer
séparément la latence de retrieval et celle de génération. Les résultats doivent être
conservés avec la version du corpus et de la configuration utilisée.
