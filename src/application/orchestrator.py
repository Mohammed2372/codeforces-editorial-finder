"""Async orchestrator for coordinating the editorial extraction process."""

from loguru import logger

from domain.models import Editorial, CachedEditorial, ProblemData, ProblemIdentifier, TutorialFormat
from domain.parsers.url_parser import URLParser
from domain.parsers.problem_page import ProblemPageParser
from domain.parsers.tutorial_parser import TutorialParser
from domain.fetchers.tutorial_finder import TutorialFinder
from domain.extractors.editorial_extractor import EditorialExtractor
from domain.exceptions import CodeforcesEditorialError


class AsyncEditorialOrchestrator:
    """Async orchestrator for editorial extraction process."""

    def __init__(
        self,
        http_client,
        ai_client,
        cache_client=None,
        use_cache: bool = True,
    ):
        """
        Initialize async orchestrator with dependency injection.

        Args:
            http_client: Async HTTP client (AsyncHTTPClient)
            ai_client: Async OpenAI client (AsyncOpenAIClient)
            cache_client: Optional async cache client (Redis)
            use_cache: Whether to use caching
        """
        self.http_client = http_client
        self.ai_client = ai_client
        self.cache_client = cache_client
        self.use_cache = use_cache and cache_client is not None

        # Initialize parsers and extractors
        self.problem_parser = ProblemPageParser(self.http_client)
        self.tutorial_parser = TutorialParser(self.http_client)
        self.tutorial_finder = TutorialFinder(self.ai_client, self.http_client)
        self.editorial_extractor = EditorialExtractor(self.ai_client)

    async def get_editorial(self, url: str) -> tuple[Editorial, ProblemData]:
        """Get editorial for problem URL with caching strategy."""

        logger.debug(f"Starting editorial extraction for URL: {url}")

        try:
            identifier = URLParser.parse(url)
            logger.debug(f"Resolved problem identifier: {identifier}")

            # Try Cache
            if self.use_cache and self.cache_client:
                cached_result = await self._get_from_cache(identifier)
                if cached_result:
                    problem_data = await self.problem_parser.parse_problem_page((identifier))
                    return cached_result, problem_data

            logger.debug(f"Parsing problem page for {identifier}")
            problem_data = await self.problem_parser.parse_problem_page(identifier)

            logger.debug(f"Finding tutorial for {identifier}")
            tutorial_url = await self.tutorial_finder.find_tutorial(identifier)

            logger.debug(f"Parsing tutorial content from {tutorial_url}")
            tutorial_data = await self.tutorial_parser.parse(tutorial_url)

            logger.debug("Extracting editorial content")
            editorial = await self.editorial_extractor.extract(
                tutorial_data,
                identifier,
                problem_data.title,
            )

            # Save to Cache
            if self.use_cache and self.cache_client:
                await self._save_to_cache(
                    identifier,
                    editorial,
                    tutorial_url,
                    tutorial_data.format,
                )

            logger.info(f"Editorial extraction completed for {identifier}")
            return editorial, problem_data

        except CodeforcesEditorialError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in orchestrator: {e}")
            raise CodeforcesEditorialError(f"Failed to get editorial: {e}") from e

    async def _get_from_cache(self, identifier: ProblemIdentifier) -> Editorial | None:
        """Fetch from cache and return if found."""

        if not self.cache_client:
            return None

        try:
            cached_data = await self.cache_client.get(identifier.cache_key)

            if cached_data:
                logger.debug(f"Get editorial for {identifier=} from cache")
                cached = CachedEditorial.from_dict(cached_data)
                return cached.editorial

            logger.debug(f"Cache miss for {identifier.cache_key}")
            return None

        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")
            return None

    async def _save_to_cache(
        self,
        identifier: ProblemIdentifier,
        editorial: Editorial,
        url: str,
        fmt: TutorialFormat,
    ) -> None:
        """Save editorial to Redis cache."""

        if not self.cache_client:
            return

        try:
            logger.debug(f"Saving editorial to cache: {identifier.cache_key}")
            cached_editorial = CachedEditorial(
                problem=identifier,
                editorial=editorial,
                tutorial_url=url,
                tutorial_format=fmt,
            )
            cached_data = cached_editorial.to_dict()
            await self.cache_client.set(identifier.cache_key, cached_data)
        except Exception as e:
            logger.warning(f"Failed to save to cache: {e}")

    async def clear_cache(self) -> None:
        """Clear the cache."""
        if self.cache_client:
            logger.info("Clearing cache")
            await self.cache_client.flushdb()
        else:
            logger.warning("Cache is not enabled")
