from __future__ import annotations
from .config import settings
from .context import assemble_context
from .generation import MockLLMProvider
from .models import AnswerRequest, AnswerResponse, DocumentChunk
from .query_transform import QueryTransformer
from .retrieval import MemoryHybridRetriever
from .seed_data import SEED_CHUNKS

class RAGPipeline:
    def __init__(self, chunks: list[DocumentChunk] | None = None, score_threshold: float | None = None):
        self.chunks = chunks if chunks is not None else SEED_CHUNKS
        self.transformer = QueryTransformer()
        self.retriever = MemoryHybridRetriever(self.chunks)
        self.llm = MockLLMProvider()
        self.score_threshold = settings.score_threshold if score_threshold is None else score_threshold

    def answer(self, request: AnswerRequest) -> AnswerResponse:
        steps = ["validate_request"]
        variations = self.transformer.multi_query(request.question) if request.multi_query else [request.question.strip()]
        steps.append("multi_query_expansion" if request.multi_query else "original_query")
        retrieval_queries = list(variations)
        if request.hyde:
            retrieval_queries.append(self.transformer.hyde_document(request.question))
            steps.append("hyde_query_representation")
        retrieved = self.retriever.search(retrieval_queries, top_k=request.top_k)
        steps.extend(["hybrid_retrieval", "relevance_threshold_check"])
        accepted = [chunk for chunk in retrieved if chunk.score >= self.score_threshold]
        # Mock cross-encoder stage: lexical relevance is already combined; this
        # final deterministic sort stands in for a trained cross-encoder reranker.
        accepted.sort(key=lambda c: (c.score, len(c.text)), reverse=True)
        steps.append("reranking")
        context = assemble_context(accepted)
        steps.append("context_assembly")
        if not accepted:
            return AnswerResponse(
                question=request.question,
                answer="I don't know based on the available documents. The retrieved passages did not meet the relevance threshold.",
                citations=[], retrieved_chunk_ids=[c.chunk_id for c in retrieved], confidence="low", fallback_used=True,
                query_variations=variations, pipeline=steps + ["fallback_response", "citation_validation"],
            )
        answer, citations = self.llm.generate(request.question, accepted)
        # Every returned citation must point to an actually retrieved chunk and exact page.
        allowed = {(c.chunk_id, c.page_number): c for c in accepted}
        citations = [c for c in citations if (c.chunk_id, c.page_number) in allowed and c.quote in allowed[(c.chunk_id, c.page_number)].text]
        if not citations or answer.startswith("I don't know"):
            answer = "I don't know based on the available documents."
            citations = []
            fallback = True
            confidence = "low"
        else:
            fallback = False
            confidence = "medium" if accepted[0].score < 0.45 else "high"
        steps.extend(["grounded_generation", "citation_validation"])
        return AnswerResponse(
            question=request.question, answer=answer, citations=citations,
            retrieved_chunk_ids=[c.chunk_id for c in accepted], confidence=confidence,
            fallback_used=fallback, query_variations=variations, pipeline=steps,
        )
