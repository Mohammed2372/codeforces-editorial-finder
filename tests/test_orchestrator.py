import pytest

from unittest.mock import AsyncMock, MagicMock, patch
from application.orchestrator import AsyncEditorialOrchestrator
from domain.models import ProblemData, Editorial, CachedEditorial


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


@pytest.mark.asyncio
async def test_get_editorial_cache_miss_runs_pipeline(orchestrator, mock_dependencies) -> None:
    """Ensure full pipeline runs when cache is empty"""

    # Setup
    url = "https://codeforces.com/problemset/problem/1234/A"
    mock_dependencies["cache_client"].get.return_value = None  # *Miss* cache

    # Create mocks for return values
    mock_problem_data = MagicMock(spec=ProblemData)
    mock_problem_data.title = "Test Problem"

    mock_editorial = MagicMock(spec=Editorial)

    # Mock pipeline responses
    orchestrator.problem_parser.parse_problem_page.return_value = mock_problem_data
    orchestrator.tutorial_finder.find_tutorial.return_value = "http://tutorial.com"
    orchestrator.tutorial_parser.parse.return_value = MagicMock(format="markdown")
    orchestrator.editorial_extractor.extract.return_value = mock_editorial

    with patch("application.orchestrator.CachedEditorial"):
        # Execute
        result, _ = await orchestrator.get_editorial(url)

        # Assertions
        orchestrator.problem_parser.parse_problem_page.assert_called_once()
        mock_dependencies["cache_client"].set.assert_called_once()

    orchestrator.problem_parser.parse_problem_page.assert_called_once()
    assert result == mock_editorial


@pytest.mark.asyncio
async def test_get_editorial_cache_hit_skip_pipeline(orchestrator, mock_dependencies) -> None:
    """Ensure pipeline is skipped when cache exists"""

    url = "https://codeforces.com/problemset/problem/1234/A"

    fake_cached = MagicMock(spec=CachedEditorial)
    fake_cached.editorial = MagicMock(spec=Editorial)

    mock_parsed_data = MagicMock(spec=ProblemData)
    mock_parsed_data.title = "Parsed Title"
    orchestrator.problem_parser.parse_problem_page.return_value = mock_parsed_data

    # Patch the from_dict method
    with patch(
        "application.orchestrator.CachedEditorial.from_dict",
        return_value=fake_cached,
    ):
        mock_dependencies["cache_client"].get.return_value = {"some": "json"}
        result, problem_data = await orchestrator.get_editorial(url=url)

    orchestrator.tutorial_finder.find_tutorial.assert_not_called()
    orchestrator.editorial_extractor.extract.assert_not_called()
    orchestrator.problem_parser.parse_problem_page.assert_called_once()

    assert result == fake_cached.editorial
    assert problem_data == mock_parsed_data
    assert problem_data.title == "Parsed Title"
