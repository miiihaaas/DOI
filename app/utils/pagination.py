"""
Pagination utilities for the DOI Management application.
"""

from typing import Optional, Dict, Any
from flask import request, url_for
from sqlalchemy.orm.query import Query


def paginate_query(query: Query, page: int = 1, per_page: int = 10, 
                  endpoint: str = None, **kwargs) -> object:
    """
    Paginate a SQLAlchemy query with additional parameters.
    
    Args:
        query: SQLAlchemy query object
        page: Current page number
        per_page: Items per page
        endpoint: Flask endpoint for pagination links
        **kwargs: Additional parameters to include in pagination links
        
    Returns:
        Pagination object
    """
    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Add endpoint and extra parameters for template use
    if endpoint:
        pagination._endpoint = endpoint
        pagination._kwargs = kwargs
    
    return pagination


def get_pagination_params() -> Dict[str, Any]:
    """
    Extract pagination parameters from request.
    
    Returns:
        Dictionary with pagination parameters
    """
    return {
        'page': request.args.get('page', 1, type=int),
        'per_page': min(request.args.get('per_page', 10, type=int), 100),  # Max 100 per page
        'search': request.args.get('search', '').strip(),
        'status': request.args.get('status', 'all')
    }


def build_pagination_url(endpoint: str, page: int, **kwargs) -> str:
    """
    Build URL for pagination with additional parameters.
    
    Args:
        endpoint: Flask endpoint
        page: Page number
        **kwargs: Additional URL parameters
        
    Returns:
        Built URL string
    """
    kwargs['page'] = page
    return url_for(endpoint, **kwargs)