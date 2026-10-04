"""Finds the knowledge-base article(s) most relevant to a message. TF-IDF
plus cosine similarity, not learned embeddings, a deliberate choice for a
small, fixed set of policy articles where keyword/term overlap is already
a strong, explainable signal. See DECISIONS.md."""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.gateways.knowledge_base_repo import Article


def retrieve(query: str, articles: list[Article], top_k: int = 2) -> list[Article]:
    if not articles:
        return []

    corpus = [f"{article.title}. {article.content}" for article in articles]
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform(corpus + [query])

    article_vectors = matrix[:-1]
    query_vector = matrix[-1]

    scores = cosine_similarity(query_vector, article_vectors)[0]
    ranked_indices = scores.argsort()[::-1][:top_k]

    return [articles[i] for i in ranked_indices]
