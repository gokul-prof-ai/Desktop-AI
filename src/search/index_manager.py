"""
DesktopAI
Search Index Manager

Wraps a FAISS vector index so the rest of the app can add file
embeddings and search them by similarity without dealing with FAISS
directly. Two files are written to disk together:

- "<name>.faiss" - the actual vectors (FAISS's own binary format)
- "<name>.json"  - which file path each vector belongs to, in the
                    same order the vectors were added

Both are needed together; FAISS only knows about numbers, so the
JSON side file is what maps a search result back to a real file.
"""

import json
from pathlib import Path

import faiss
import numpy as np

from core.logger import get_logger

logger = get_logger("search")


class SearchIndex:
    """An in-memory FAISS index of file embeddings, with save/load support."""

    def __init__(self, dimension: int):
        """
        Args:
            dimension (int):
                The length of each embedding vector. Every vector
                added to this index must have this same length.
        """
        self.dimension = dimension
        self._index = faiss.IndexFlatIP(dimension)
        self._paths: list[str] = []

    def __len__(self) -> int:
        return len(self._paths)

    def add(self, path: str, vector: list[float]) -> None:
        """
        Add one file's embedding to the index.

        Args:
            path (str):
                The file path this vector represents.
            vector (list[float]):
                The embedding, as returned by embedder.get_embedding().
        """
        array = np.array([vector], dtype="float32")
        faiss.normalize_L2(array)  # so inner product == cosine similarity
        self._index.add(array)
        self._paths.append(path)

    def search(self, vector: list[float], top_k: int) -> list[tuple[str, float]]:
        """
        Find the files whose embeddings are most similar to `vector`.

        Args:
            vector (list[float]):
                The query embedding.
            top_k (int):
                Maximum number of results to return.

        Returns:
            list[tuple[str, float]]:
                (file_path, similarity_score) pairs, best match
                first. Scores range roughly from -1 to 1 (cosine
                similarity); higher means more similar. Returns an
                empty list if the index has nothing in it yet.
        """
        if len(self._paths) == 0:
            return []

        array = np.array([vector], dtype="float32")
        faiss.normalize_L2(array)

        # Can't return more matches than we actually have.
        k = min(top_k, len(self._paths))
        scores, indices = self._index.search(array, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            results.append((self._paths[idx], float(score)))

        return results

    def save(self, base_path: Path) -> None:
        """
        Save this index to disk as "<base_path>.faiss" and
        "<base_path>.json". Creates the parent folder if needed.

        Args:
            base_path (Path):
                Path without an extension, e.g. passing
                data/search_index writes data/search_index.faiss
                and data/search_index.json
        """
        base_path.parent.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self._index, str(base_path.with_suffix(".faiss")))

        metadata = {"dimension": self.dimension, "paths": self._paths}
        base_path.with_suffix(".json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )

        logger.info(
            "Saved search index (%d file(s)) to %s.*", len(self._paths), base_path
        )

    @classmethod
    def load(cls, base_path: Path) -> "SearchIndex":
        """
        Load a previously saved index.

        Args:
            base_path (Path):
                Same path passed to save() earlier (without an
                extension).

        Returns:
            SearchIndex:
                The restored index.

        Raises:
            FileNotFoundError:
                If no saved index exists at this path yet.
        """
        faiss_path = base_path.with_suffix(".faiss")
        json_path = base_path.with_suffix(".json")

        if not faiss_path.exists() or not json_path.exists():
            raise FileNotFoundError(
                f"No search index found at {base_path}.* — build one first."
            )

        metadata = json.loads(json_path.read_text(encoding="utf-8"))

        index = cls(dimension=metadata["dimension"])
        index._index = faiss.read_index(str(faiss_path))
        index._paths = metadata["paths"]

        logger.info(
            "Loaded search index (%d file(s)) from %s.*", len(index._paths), base_path
        )

        return index