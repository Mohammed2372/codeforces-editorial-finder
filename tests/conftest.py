import pytest

from unittest.mock import AsyncMock
from application.orchestrator import AsyncEditorialOrchestrator


@pytest.fixture(scope="function")
def mock_dependencies() -> dict[str, AsyncMock]:
    return {
        "http_client": AsyncMock(),
        "ai_client": AsyncMock(),
        "cache_client": AsyncMock(),
    }


@pytest.fixture(scope="function")
def orchestrator(mock_dependencies) -> AsyncEditorialOrchestrator:
    orch = AsyncEditorialOrchestrator(
        http_client=mock_dependencies["http_client"],
        ai_client=mock_dependencies["ai_client"],
        cache_client=mock_dependencies["cache_client"],
        use_cache=True,
    )

    # Mock internal components to isolate orchestrator logic
    orch.problem_parser = AsyncMock()
    orch.tutorial_parser = AsyncMock()
    orch.tutorial_finder = AsyncMock()
    orch.editorial_extractor = AsyncMock()

    return orch
