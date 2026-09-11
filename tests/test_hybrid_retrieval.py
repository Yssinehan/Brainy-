from brainy.graph.kg import Triple, store_triples
from brainy.memory.ingest import ingest_text
from brainy.memory.types import Chunk
from brainy.rag.retrievers import GraphRetriever, HybridRetriever, KeywordRetriever


def test_keyword_retriever_finds_lexical_overlap(store, vectors, router):
    ingest_text(store, vectors, router, text="Brainy uses hybrid retrieval.", doc_id="brainy", source="notes", extract_kg=False)

    results = KeywordRetriever(store).retrieve("hybrid retrieval")

    assert results and results[0].doc_id == "brainy"


def test_graph_retriever_uses_chunk_provenance(store, vectors, router):
    result = ingest_text(store, vectors, router, text="Brainy uses Chroma.", doc_id="brainy", source="notes", extract_kg=False)
    chunk = store.all_chunks()[0]
    store_triples(store, chunk, [Triple(subject="Brainy", relation="uses", object="Chroma")])

    results = GraphRetriever(store).retrieve("What does Brainy use?")

    assert results and results[0].chunk_id == chunk.id


def test_hybrid_retriever_keeps_vector_retrieval_as_a_fallback(store, vectors, router):
    ingest_text(store, vectors, router, text="Brainy stores long-term memory.", doc_id="memory", source="notes", extract_kg=False)

    results = HybridRetriever(store, vectors, router).retrieve("long-term memory")

    assert results and results[0].doc_id == "memory"
