from app.gateways.knowledge_base_repo import Article
from app.service.retrieval import retrieve

_ARTICLES = [
    Article(
        id="defect_process",
        title="Defect and Damage Process",
        content=(
            "If a part arrives broken, cracked, or defective, start a defect "
            "claim within 14 days of delivery. We offer a replacement or a "
            "full refund once the defect is confirmed."
        ),
    ),
    Article(
        id="shipping_policy",
        title="Shipping Policy",
        content=(
            "Standard orders ship within 3-5 business days via our freight "
            "partners. You will receive a tracking number by email once the "
            "order leaves the warehouse."
        ),
    ),
    Article(
        id="quote_process",
        title="Quote Process",
        content=(
            "To request a custom quote, send us your specifications and "
            "quantity. Quotes are typically returned within 2 business days."
        ),
    ),
    Article(
        id="lead_times",
        title="Lead Times",
        content=(
            "Custom manufacturing lead times run 4-6 weeks depending on "
            "order volume and material availability."
        ),
    ),
]


def test_returns_most_relevant_article_for_a_defect_message():
    results = retrieve(
        "The bracket I received is cracked and one bolt hole is missing entirely.",
        _ARTICLES,
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].id == "defect_process"


def test_returns_most_relevant_article_for_a_shipping_message():
    results = retrieve(
        "Hi, can you tell me when my order will ship and if there's tracking?",
        _ARTICLES,
        top_k=1,
    )

    assert len(results) == 1
    assert results[0].id == "shipping_policy"


def test_top_k_limits_the_number_of_results():
    results = retrieve("quote for a bulk order", _ARTICLES, top_k=2)

    assert len(results) == 2


def test_empty_article_list_returns_no_results_without_crashing():
    results = retrieve("anything at all", [], top_k=2)

    assert results == []
