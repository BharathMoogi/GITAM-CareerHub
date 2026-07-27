"""
RAG (Retrieval-Augmented Generation) Interfaces.

These abstract base classes define the contracts for:
  - Retriever       : Finds relevant documents given a query
  - EmbeddingProvider: Converts text to vector embeddings
  - VectorStore     : Stores and searches embeddings

Implementations (e.g. ChromaDB, Pinecone, PGVector, FAISS)
are added without changing the AI Mentor business logic.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Document:
    """A retrieved document chunk with its embedding metadata."""
    id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0             # Similarity score (higher = more relevant)
    source: Optional[str] = None   # e.g. "course:uuid", "project:uuid"


@dataclass
class EmbeddingResult:
    """Result of embedding a text chunk."""
    text: str
    embedding: List[float]
    model: str
    token_count: int = 0


class BaseRetriever(ABC):
    """
    Retriever interface — finds relevant documents for a given query.

    Implementations might use:
      - Dense retrieval (semantic search via embeddings)
      - Sparse retrieval (BM25 keyword search)
      - Hybrid (weighted combination of both)
    """

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """
        Retrieve the top-k most relevant documents for a query.

        Args:
            query: Natural language query string.
            top_k: Maximum number of documents to return.
            filters: Optional metadata filters (e.g. {"branch": "AIML"}).

        Returns:
            List of Document objects ordered by relevance.
        """

    @abstractmethod
    async def add_documents(self, documents: List[Document]) -> None:
        """Ingest a batch of documents into the retrieval index."""

    @abstractmethod
    async def delete_documents(self, ids: List[str]) -> None:
        """Remove documents from the index by their IDs."""


class BaseEmbeddingProvider(ABC):
    """
    Embedding provider interface — converts text to dense vector representations.

    Implementations:
      - OpenAI text-embedding-3-small / text-embedding-3-large
      - Google text-embedding-004
      - Sentence Transformers (local)
      - Cohere embed-v3
    """

    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResult:
        """Embed a single text string."""

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Embed multiple texts in a single API call for efficiency."""

    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """The dimensionality of produced embeddings."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier."""


class BaseVectorStore(ABC):
    """
    Vector store interface — persists and searches embedding vectors.

    Implementations:
      - ChromaDB (local / managed)
      - Pinecone (managed cloud)
      - PGVector (PostgreSQL extension)
      - FAISS (in-memory, fast local search)
      - Weaviate (managed cloud)
    """

    @abstractmethod
    async def upsert(self, documents: List[Document], embeddings: List[EmbeddingResult]) -> None:
        """Store or update document embeddings."""

    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        """Find the top-k nearest neighbours to a query embedding."""

    @abstractmethod
    async def delete(self, ids: List[str]) -> None:
        """Remove vectors from the store."""

    @abstractmethod
    async def count(self) -> int:
        """Return total number of stored vectors."""


class NoOpRetriever(BaseRetriever):
    """
    No-operation retriever — returns empty results.
    Used as the default until a real retriever is configured.
    This allows the AI Mentor to function (using LLM knowledge only)
    even before RAG is implemented.
    """

    async def retrieve(self, query: str, top_k: int = 5, filters: Optional[Dict[str, Any]] = None) -> List[Document]:
        return []

    async def add_documents(self, documents: List[Document]) -> None:
        pass

    async def delete_documents(self, ids: List[str]) -> None:
        pass
