import pytest

from unittest.mock import MagicMock, patch
from domain.models import ProblemData, Editorial, CachedEditorial


@pytest.mark.asyncio
async def test_get_editorial_cache_miss_runs_pipeline(orchestrator, mock_dependencies) -> None:
    """Ensure full pipeline runs when cache is empty"""

    # Setup
    url = "https://codeforces.com/problemset/problem/1234/A"
    mock_dependencies["cache_client"].get.return_value = None  # *Miss* cache

    # Mocks
    mock_editorial = MagicMock(spec=Editorial)
    orchestrator.problem_parser.parse_problem_page.return_value = ProblemData(
        title="Test",
        url=url,
        identifier=MagicMock(),
    )
    orchestrator.editorial_extractor.extract.return_value = mock_editorial

    with patch("application.orchestrator.CachedEditorial") as MockCachedClass:
        # Execute
        editorial, problem_data = await orchestrator.get_editorial(url)

        # Assertions
        MockCachedClass.assert_called_once()
        mock_dependencies["cache_client"].set.assert_called_once()

    orchestrator.problem_parser.parse_problem_page.assert_called_once()
    orchestrator.tutorial_finder.find_tutorial.assert_called_once()

    assert editorial == mock_editorial
    assert problem_data.title == "Test"


@pytest.mark.asyncio
async def test_get_editorial_cache_hit_skip_pipeline(orchestrator, mock_dependencies) -> None:
    """Ensure pipeline is skipped when cache exists"""

    url = "https://codeforces.com/problemset/problem/1234/A"

    fake_cached = MagicMock(spec=CachedEditorial)
    fake_cached.editorial = MagicMock(spec=Editorial)

    mock_parsed_data = MagicMock(spec=ProblemData)
    mock_parsed_data.title = "Test Title"
    orchestrator.problem_parser.parse_problem_page.return_value = mock_parsed_data

    # Patch the from_dict method
    with patch(
        "application.orchestrator.CachedEditorial.from_dict",
        return_value=fake_cached,
    ):
        mock_dependencies["cache_client"].get.return_value = {"some": "json"}
        editorial, problem_data = await orchestrator.get_editorial(url=url)

    orchestrator.tutorial_finder.find_tutorial.assert_not_called()
    orchestrator.problem_parser.parse_problem_page.assert_called_once()

    assert editorial == fake_cached.editorial
    assert problem_data == mock_parsed_data
