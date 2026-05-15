"""Semantic index backend contracts and reset implementation helpers."""

from .inventory import SEMANTIC_INDEX_SURFACES
from .backend import (
    SemanticIndexBackend,
    SemanticIndexDeleteRequest,
    SemanticIndexHealth,
    SemanticIndexRebuildPlan,
    SemanticIndexVector,
    SemanticIndexVectorMatch,
    SemanticIndexVectorQuery,
    SemanticIndexWriteResult,
    SQLiteVecSemanticIndex,
)
from .sqlite_vec import (
    SQLITE_VEC_PACKAGE,
    SQLITE_VEC_VERSION,
    SQLiteVecLoadState,
    load_sqlite_vec_extension,
    sqlite_vec_dependency_state,
    sqlite_vec_runtime_state,
)
from .service import (
    SemanticIndexDocument,
    SemanticIndexDeleteResult,
    SemanticIndexMetadataRebuildPlan,
    SemanticIndexRepository,
    SemanticIndexService,
    semantic_content_hash,
    semantic_index_entry_id,
)
from .search import (
    FUSION_WEIGHTS,
    HybridSemanticSearcher,
    SemanticSearchMatch,
    SemanticSearchQuery,
    SemanticSearchRepository,
)

__all__ = [
    "SEMANTIC_INDEX_SURFACES",
    "SemanticIndexBackend",
    "SemanticIndexDeleteRequest",
    "SemanticIndexHealth",
    "SemanticIndexRebuildPlan",
    "SemanticIndexVector",
    "SemanticIndexVectorMatch",
    "SemanticIndexVectorQuery",
    "SemanticIndexWriteResult",
    "SemanticIndexDocument",
    "SemanticIndexDeleteResult",
    "SemanticIndexMetadataRebuildPlan",
    "SemanticIndexRepository",
    "SemanticIndexService",
    "FUSION_WEIGHTS",
    "HybridSemanticSearcher",
    "SemanticSearchMatch",
    "SemanticSearchQuery",
    "SemanticSearchRepository",
    "SQLITE_VEC_PACKAGE",
    "SQLITE_VEC_VERSION",
    "SQLiteVecSemanticIndex",
    "SQLiteVecLoadState",
    "load_sqlite_vec_extension",
    "semantic_content_hash",
    "semantic_index_entry_id",
    "sqlite_vec_dependency_state",
    "sqlite_vec_runtime_state",
]
