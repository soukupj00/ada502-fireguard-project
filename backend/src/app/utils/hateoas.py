"""HATEOAS link generation and API version extraction utilities.

Provides helpers for creating REST response links and extracting versioned
API base URLs from incoming FastAPI requests. Links dynamically adapt to
the API version in the request path, enabling client-driven navigation.
"""

from typing import List, Optional

from fastapi import Request

from app.schemas import Link


def get_base_url(request: Request) -> str:
    """Extract the base API versioned URL (e.g., /api/v1) from request path.

    Args:
        request: FastAPI Request object with URL path.

    Returns:
        Versioned API base path like /api/v1 or /api/v2, extracted from request.
        Defaults to /api/v1 if path format is unrecognized.

    Example:
        Request path /api/v1/risk/coords → /api/v1
    """
    path = request.url.path
    parts = path.split("/")
    # Parts will be ['', 'api', 'v1', ...]
    if len(parts) >= 3 and parts[1] == "api":
        return f"/api/{parts[2]}"
    return "/api/v1"  # Fallback


def create_links(
    request: Request, self_rel_path: str, others: Optional[List[dict]] = None
) -> List[Link]:
    """Generate HATEOAS links for a REST response, adapting to request API version.

    Creates a "self" link for the current endpoint plus any additional links
    provided. All links are automatically prefixed with the detected API version
    (e.g., /api/v1) ensuring correct routing for versioned API consumers.

    Args:
        request: FastAPI Request for extracting API version and base URL.
        self_rel_path: Relative path for the self link (e.g., "/risk/history").
        others: Optional list of dicts with 'href' and 'rel' keys to include
                as additional links (e.g., [{"href": "/zones", "rel": "zones"}]).

    Returns:
        List of Link objects ready for serialization in REST responses.
        Always includes a self link; additional links appended if provided.
    """
    base_url = get_base_url(request)

    links = [Link(href=f"{base_url}{self_rel_path}", rel="self")]
    if others:
        for item in others:
            # If href starts with /, assume it needs base_url prepended
            # if it doesn't already have it
            href = item["href"]
            if href.startswith("/") and not href.startswith(base_url):
                full_href = f"{base_url}{href}"
            else:
                full_href = href
            links.append(Link(href=full_href, rel=item["rel"]))
    return links
