from ai_act_assistant.corpus import extract_citations, load_corpus, parse_corpus

from .conftest import SAMPLE


def test_sample_is_split_by_article_and_annex():
    chunks = load_corpus(SAMPLE)
    refs = [c.ref for c in chunks]
    assert "Article 5" in refs and "Annexe III" in refs
    assert len(refs) == len(set(refs)) == 11
    art5 = next(c for c in chunks if c.ref == "Article 5")
    assert art5.title == "Pratiques interdites en matière d'IA"
    assert "notation sociale" in art5.text


def test_text_before_first_article_is_ignored():
    chunks = parse_corpus("Préambule\n\nArticle 1\nObjet\nLe texte.\n")
    assert [(c.ref, c.title, c.text) for c in chunks] == [("Article 1", "Objet", "Le texte.")]


def test_long_article_is_split_and_keeps_its_reference():
    body = "\n".join(f"Paragraphe {i} " + "x" * 80 for i in range(10))
    chunks = parse_corpus(f"Article 7\nTitre\n{body}\n", max_chars=300)
    assert len(chunks) > 1
    assert {c.ref for c in chunks} == {"Article 7"}
    assert [c.id for c in chunks][:2] == ["article-7", "article-7#2"]
    assert "\n".join(c.text for c in chunks) == body


def test_mention_of_an_article_inside_a_sentence_is_not_a_heading():
    chunks = parse_corpus("Article 1\nObjet\nVoir l'article 5.\nArticle 5 s'applique.\n")
    assert [c.ref for c in chunks] == ["Article 1"]


def test_extract_citations_normalizes_and_deduplicates():
    text = "Interdit [Article 5]. Voir [annexe iii] et encore [Article  5], pas Article 9."
    assert extract_citations(text) == ["Article 5", "Annexe III"]


def test_article_premier_is_article_1():
    chunks = parse_corpus("Article premier\nObjet\nLe texte.\n\nArticle 2\nChamp\nSuite.\n")
    assert [c.ref for c in chunks] == ["Article 1", "Article 2"]
