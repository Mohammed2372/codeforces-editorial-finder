"""Parser for Codeforces problem URLs."""

import re
from urllib.parse import urlparse

from loguru import logger

from codeforces_editorial.models import ProblemIdentifier
from codeforces_editorial.utils.exceptions import URLParseError


class URLParser:
    """Parser for various Codeforces URL formats."""

    # Supported URL patterns
    PATTERNS = [
        # https://codeforces.com/contest/1234/problem/A
        r"codeforces\.(com|ru)/contest/(\d+)/problem/([A-Z]\d*)",
        # https://codeforces.com/problemset/problem/1234/A
        r"codeforces\.(com|ru)/problemset/problem/(\d+)/([A-Z]\d*)",
        # https://codeforces.com/gym/102345/problem/A
        r"codeforces\.(com|ru)/gym/(\d+)/problem/([A-Z]\d*)",
    ]

    @classmethod
    def parse(cls, url: str) -> ProblemIdentifier:
        """
        Parse Codeforces problem URL and extract problem identifier.

        Args:
            url: Codeforces problem URL

        Returns:
            ProblemIdentifier with contest_id, problem_id, and is_gym flag

        Raises:
            URLParseError: If URL format is not recognized

        Examples:
            >>> URLParser.parse("https://codeforces.com/contest/1234/problem/A")
            ProblemIdentifier(contest_id='1234', problem_id='A', is_gym=False)

            >>> URLParser.parse("https://codeforces.ru/gym/102345/problem/B1")
            ProblemIdentifier(contest_id='102345', problem_id='B1', is_gym=True)
        """
        logger.debug(f"Parsing URL: {url}")

        # Validate URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise URLParseError(f"Invalid URL format: {url}")
        except Exception as e:
            raise URLParseError(f"Failed to parse URL: {url}") from e

        # Try each pattern
        for pattern in cls.PATTERNS:
            match = re.search(pattern, url)
            if match:
                groups = match.groups()

                # Check if it's a gym problem
                is_gym = "/gym/" in url

                # Extract contest_id and problem_id
                if is_gym:
                    # Pattern: gym/contest_id/problem/problem_id
                    contest_id = groups[1]
                    problem_id = groups[2]
                else:
                    # Pattern: contest/contest_id/problem/problem_id
                    # or problemset/problem/contest_id/problem_id
                    contest_id = groups[1]
                    problem_id = groups[2]

                identifier = ProblemIdentifier(
                    contest_id=contest_id,
                    problem_id=problem_id,
                    is_gym=is_gym,
                )

                logger.info(f"Parsed URL to problem: {identifier}")
                return identifier

        # No pattern matched
        raise URLParseError(
            f"Unrecognized Codeforces URL format: {url}. "
            f"Supported formats:\n"
            f"  - https://codeforces.com/contest/<contest_id>/problem/<problem_id>\n"
            f"  - https://codeforces.com/problemset/problem/<contest_id>/<problem_id>\n"
            f"  - https://codeforces.com/gym/<contest_id>/problem/<problem_id>"
        )

    @classmethod
    def build_problem_url(cls, identifier: ProblemIdentifier) -> str:
        """
        Build problem URL from identifier.

        Args:
            identifier: Problem identifier

        Returns:
            Full problem URL
        """
        base = "https://codeforces.com"

        if identifier.is_gym:
            url = f"{base}/gym/{identifier.contest_id}/problem/{identifier.problem_id}"
        else:
            url = f"{base}/contest/{identifier.contest_id}/problem/{identifier.problem_id}"

        logger.debug(f"Built problem URL: {url}")
        return url

    @classmethod
    def build_contest_url(cls, identifier: ProblemIdentifier) -> str:
        """
        Build contest main page URL from identifier.

        Args:
            identifier: Problem identifier

        Returns:
            Contest main page URL
        """
        base = "https://codeforces.com"

        if identifier.is_gym:
            url = f"{base}/gym/{identifier.contest_id}"
        else:
            url = f"{base}/contest/{identifier.contest_id}"

        logger.debug(f"Built contest URL: {url}")
        return url

    @classmethod
    def validate_url(cls, url: str) -> bool:
        """
        Check if URL is a valid Codeforces problem URL.

        Args:
            url: URL to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            cls.parse(url)
            return True
        except URLParseError:
            return False


def parse_problem_url(url: str) -> ProblemIdentifier:
    """
    Convenience function to parse problem URL.

    Args:
        url: Codeforces problem URL

    Returns:
        ProblemIdentifier
    """
    return URLParser.parse(url)
