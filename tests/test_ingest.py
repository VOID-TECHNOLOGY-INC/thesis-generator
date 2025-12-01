from thesis_generator.tools.ingest import (
    ingest_documents,
    reset_vector_store_registry,
    search_sections,
)


def setup_function() -> None:
    # Ensure registry isolation between tests
    reset_vector_store_registry()


def test_ingest_links_parent_and_child_chunks() -> None:
    documents = [
        {
            "title": "Agentic RAG",
            "year": 2023,
            "citations": 42,
            "authors": ["Alice Smith"],
            "sections": [
                {
                    "heading": "Introduction",
                    "content": (
                        "Parent context about memory aware retrieval augmented generation. "
                        "This child chunk adds more detail about chunk linkage and vector indexes."
                    ),
                }
            ],
        }
    ]

    uri = ingest_documents(documents, chunk_size=50)
    results = search_sections("chunk linkage", vector_store_uri=uri, k=3)

    assert results, "ingest should create searchable child chunks"
    first = results[0]
    assert first.chunk.metadata["parent_id"] == first.parent.metadata["id"]
    assert first.parent.metadata["section_heading"] == "Introduction"
    assert first.chunk.metadata["authors"] == ["Alice Smith"]
    assert first.parent.metadata["citations"] == 42


def test_year_filter_excludes_out_of_range_results() -> None:
    documents = [
        {
            "title": "Legacy RAG",
            "year": 2018,
            "citations": 12,
            "authors": ["Bob Lee"],
            "sections": [
                {
                    "heading": "Background",
                    "content": "Early neural retrieval approaches and evaluation baselines.",
                }
            ],
        },
        {
            "title": "Modern RAG",
            "year": 2022,
            "citations": 85,
            "authors": ["Carol Kim"],
            "sections": [
                {
                    "heading": "Methods",
                    "content": "Neural retrievers and dense vector search for transformers.",
                }
            ],
        },
    ]

    uri = ingest_documents(documents, chunk_size=40)

    recent = search_sections(
        "neural",
        vector_store_uri=uri,
        filters={"year": {"gte": 2020}},
        k=5,
    )
    assert recent, "recent documents should match the query"
    assert all(result.chunk.metadata["year"] >= 2020 for result in recent)

    older_only = search_sections(
        "neural",
        vector_store_uri=uri,
        filters={"year": {"lte": 2019}},
        k=5,
    )
    assert len(older_only) == 1
    assert older_only[0].chunk.metadata["year"] == 2018
