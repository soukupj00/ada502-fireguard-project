from typing import List, Optional

from fastapi import Request

from app.schemas import Link


def get_base_url(request: Request) -> str:
    """
    Extracts the base API versioned URL from the request.
    Example: If request path is /api/v1/risk/coords, returns /api/v1
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
    """
    Utility to create HATEOAS links dynamically based on the current API version.
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
