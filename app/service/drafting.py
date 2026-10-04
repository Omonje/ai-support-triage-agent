"""The rule for when a draft is allowed to be generated at all: never
without at least one grounding KB article. The gateway does the actual
Claude call; this layer refuses to call it ungrounded."""


def build_draft(gateway, subject: str, body: str, kb_articles: list):
    if not kb_articles:
        raise ValueError("Cannot draft a grounded reply with no KB articles retrieved")

    return gateway.draft_reply(subject, body, kb_articles)
