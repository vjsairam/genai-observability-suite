"""
Sample RAG Pipeline with GenAI OpenTelemetry Instrumentation

This example demonstrates all span types:
- embed: Query embedding
- retrieve: Vector search
- rerank: Result reranking
- generate: LLM completion
- tool_call: External tool invocation
"""

import os
import sys
from typing import List, Dict, Any

# Add SDK to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../sdk/python'))

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

from genai_otel import (
    trace_embed,
    trace_retrieve,
    trace_rerank,
    trace_generate,
    trace_tool_call,
    GenAIConfig,
    set_config,
)

# Initialize OpenTelemetry
resource = Resource.create({"service.name": "rag-pipeline-demo"})
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(
    OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"))
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# Configure GenAI instrumentation
config = GenAIConfig(
    service_name="rag-pipeline-demo",
    environment="demo",
    log_prompts=True,
    sample_rate=1.0,  # Log everything for demo
    tenant_id="demo-tenant",
    user_id="demo-user",
)
set_config(config)


class MockEmbeddingResponse:
    """Mock OpenAI embedding response"""
    def __init__(self, embedding: List[float], tokens: int):
        self.data = [type('obj', (object,), {'embedding': embedding})]
        self.usage = type('obj', (object,), {'total_tokens': tokens})


class MockChatResponse:
    """Mock OpenAI chat response"""
    def __init__(self, content: str, input_tokens: int, output_tokens: int):
        self.choices = [
            type('obj', (object,), {
                'message': type('obj', (object,), {'content': content}),
                'finish_reason': 'stop'
            })
        ]
        self.usage = type('obj', (object,), {
            'prompt_tokens': input_tokens,
            'completion_tokens': output_tokens,
            'total_tokens': input_tokens + output_tokens
        })


class RAGPipeline:
    """RAG Pipeline with full observability"""

    @trace_embed(model="text-embedding-3-small", provider="openai", dimensions=1536)
    def embed_query(self, text: str) -> MockEmbeddingResponse:
        """Generate query embedding"""
        print(f"📊 Embedding query: {text[:50]}...")
        # Mock embedding generation
        embedding = [0.1] * 1536
        return MockEmbeddingResponse(embedding, tokens=8)

    @trace_retrieve(source="pinecone", top_k=10, index_name="knowledge-base")
    def retrieve_documents(self, query_vector: List[float]) -> List[Dict[str, Any]]:
        """Retrieve relevant documents"""
        print("🔍 Retrieving documents from vector store...")
        # Mock retrieval results
        return [
            {"id": "doc1", "text": "RAG stands for Retrieval-Augmented Generation.", "score": 0.92},
            {"id": "doc2", "text": "RAG combines retrieval with LLM generation.", "score": 0.87},
            {"id": "doc3", "text": "OpenTelemetry provides observability standards.", "score": 0.81},
        ]

    @trace_rerank(model="rerank-english-v3.0", provider="cohere", input_count=3, top_n=2)
    def rerank_results(self, query: str, documents: List[Dict]) -> List[Dict]:
        """Rerank retrieved documents"""
        print("🎯 Reranking results for relevance...")
        # Mock reranking (return top 2)
        return documents[:2]

    @trace_generate(
        model="gpt-4",
        provider="openai",
        temperature=0.7,
        max_tokens=500
    )
    def generate_answer(self, prompt: str) -> MockChatResponse:
        """Generate answer using LLM"""
        print("💬 Generating answer with LLM...")
        # Mock LLM response
        answer = (
            "RAG (Retrieval-Augmented Generation) is a technique that combines document retrieval "
            "with language model generation to produce more accurate and contextual responses. "
            "It works by first retrieving relevant documents, then using them as context for generation."
        )
        return MockChatResponse(answer, input_tokens=150, output_tokens=45)

    @trace_tool_call(tool_name="web_search", parameters={"engine": "google", "max_results": 5})
    def search_web(self, query: str) -> Dict[str, Any]:
        """Perform web search (tool call example)"""
        print(f"🌐 Searching web for: {query}")
        # Mock search results
        return {
            "results": [
                {"title": "RAG Overview", "url": "https://example.com/rag"},
                {"title": "OpenTelemetry Guide", "url": "https://example.com/otel"},
            ],
            "count": 2
        }

    def run(self, question: str) -> str:
        """Execute complete RAG pipeline"""
        print(f"\n{'='*60}")
        print(f"❓ Question: {question}")
        print(f"{'='*60}\n")

        # Step 1: Embed the query
        embedding_response = self.embed_query(question)
        query_vector = embedding_response.data[0].embedding

        # Step 2: Retrieve relevant documents
        documents = self.retrieve_documents(query_vector)
        print(f"   Found {len(documents)} documents\n")

        # Step 3: Rerank for relevance
        reranked_docs = self.rerank_results(question, documents)
        print(f"   Reranked to top {len(reranked_docs)} documents\n")

        # Step 4: Optional - Search web for additional context
        web_results = self.search_web(question)
        print(f"   Found {web_results['count']} web results\n")

        # Step 5: Generate answer
        context = "\n".join([doc["text"] for doc in reranked_docs])
        prompt = f"Context:\n{context}\n\nQuestion: {question}\n\nAnswer:"
        response = self.generate_answer(prompt)
        answer = response.choices[0].message.content

        print(f"\n{'='*60}")
        print(f"✅ Answer: {answer}")
        print(f"{'='*60}\n")

        return answer


def main():
    """Run sample RAG pipeline"""
    pipeline = RAGPipeline()

    questions = [
        "What is RAG and how does it work?",
        "How does OpenTelemetry help with observability?",
    ]

    for question in questions:
        pipeline.run(question)
        print("\n")

    print("✨ Demo complete! Check your observability backend for traces.")
    print("   - Traces show linked spans across embed → retrieve → rerank → generate")
    print("   - Token usage and costs are automatically calculated")
    print("   - All operations are tracked with proper attributes")


if __name__ == "__main__":
    main()
