import numpy as np

from ai_act_assistant.corpus import load_corpus
from ai_act_assistant.evaluate import evaluate_retrieval
from ai_act_assistant.retriever import Retriever, reciprocal_rank_fusion, tokenize

from .conftest import ROOT, SAMPLE


def test_tokenize_folds_accents_plurals_and_stopwords():
    assert tokenize("Les déployeurs et l'Éducation") == ["deployeur", "education"]


def test_lexical_search_finds_the_right_article():
    r = Retriever(load_corpus(SAMPLE))
    assert r.search("amende chiffre d'affaires", k=1)[0].ref == "Article 99"
    assert r.search("conservation des journaux six mois", k=1)[0].ref == "Article 26"


def test_query_without_any_known_word_returns_nothing():
    r = Retriever(load_corpus(SAMPLE))
    assert r.search("ratatouille aubergine courgette") == []
    assert r.search("") == []


def test_reciprocal_rank_fusion_rewards_agreement():
    assert reciprocal_rank_fusion([[0, 1, 2], [2, 1, 0], [1, 0, 2]])[0] == 1


def test_dense_ranking_can_rescue_a_query_with_no_shared_word():
    chunks = load_corpus(SAMPLE)
    target = next(i for i, c in enumerate(chunks) if c.ref == "Article 99")

    class OneHotEmbedder:
        """Place la question sur le même axe que l'article 99."""

        def embed(self, texts):
            if len(texts) == 1:
                return np.eye(len(chunks))[[target]]
            return np.eye(len(chunks))

    r = Retriever(chunks, embedder=OneHotEmbedder())
    assert r.search("punition pecuniaire", k=1)[0].ref == "Article 99"


def test_golden_set_hit_rate_stays_above_threshold():
    report = evaluate_retrieval(Retriever(load_corpus(SAMPLE)), ROOT / "eval" / "golden.jsonl", k=4)
    assert report["cases"] >= 15
    assert report["hit_rate"] >= 0.9, report["misses"]
