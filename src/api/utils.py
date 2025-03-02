"""
Utility functions for the API module.

Contains helper functions for:
- Response formatting
- Error handling
- Parameter validation
- Data transformation
"""
from typing import Dict, Any, List, Optional, Union
from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError
import json

# Standard API response model
class ApiResponse(BaseModel):
    """Standard API response model."""
    success: bool
    message: str
    data: Optional[Any] = None
    errors: Optional[List[Dict[str, Any]]] = None

def success_response(message: str = "Success", data: Any = None) -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        message: Success message
        data: Data to include in the response
        
    Returns:
        Dictionary with standard response format
    """
    return ApiResponse(
        success=True,
        message=message,
        data=data,
        errors=None
    ).dict()

def error_response(
    message: str = "An error occurred", 
    errors: List[Dict[str, Any]] = None,
    data: Any = None
) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        errors: List of detailed error information
        data: Optional data to include in the response
        
    Returns:
        Dictionary with standard response format
    """
    return ApiResponse(
        success=False,
        message=message,
        data=data,
        errors=errors or []
    ).dict()

def validation_exception_handler(exc: ValidationError) -> HTTPException:
    """
    Handle Pydantic validation errors and convert to HTTPException.
    
    Args:
        exc: The validation error
        
    Returns:
        HTTPException with formatted error details
    """
    error_details = []
    for error in exc.errors():
        error_details.append({
            "location": error.get("loc", []),
            "message": error.get("msg", ""),
            "type": error.get("type", "")
        })
    
    return HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=error_response(
            message="Validation error",
            errors=error_details
        )
    )

def parse_query_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and normalize query parameters.
    
    Args:
        params: Raw query parameters
        
    Returns:
        Processed query parameters
    """
    result = {}
    
    # Process boolean values
    for key, value in params.items():
        if isinstance(value, str):
            # Convert string boolean representations
            if value.lower() == "true":
                result[key] = True
            elif value.lower() == "false":
                result[key] = False
            # Convert numeric strings
            elif value.isdigit():
                result[key] = int(value)
            elif is_float(value):
                result[key] = float(value)
            # Handle JSON strings
            elif is_json(value):
                try:
                    result[key] = json.loads(value)
                except json.JSONDecodeError:
                    result[key] = value
            else:
                result[key] = value
        else:
            result[key] = value
    
    return result

def is_float(value: str) -> bool:
    """
    Check if a string can be converted to float.
    
    Args:
        value: String to check
        
    Returns:
        True if convertible to float, False otherwise
    """
    try:
        float(value)
        return True
    except ValueError:
        return False

def is_json(value: str) -> bool:
    """
    Check if a string is valid JSON.
    
    Args:
        value: String to check
        
    Returns:
        True if valid JSON, False otherwise
    """
    try:
        json.loads(value)
        return True
    except (ValueError, TypeError):
        return False

def paginate_results(
    items: List[Any], 
    page: int = 1, 
    page_size: int = 20
) -> Dict[str, Any]:
    """
    Paginate a list of items.
    
    Args:
        items: List of items to paginate
        page: Page number (1-indexed)
        page_size: Number of items per page
        
    Returns:
        Dictionary with pagination information and items
    """
    # Ensure valid page and page_size
    page = max(1, page)
    page_size = max(1, min(100, page_size))  # Limit page size between 1 and 100
    
    # Calculate indices
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    # Get paginated items
    paginated_items = items[start_idx:end_idx]
    
    # Calculate total pages
    total_items = len(items)
    total_pages = (total_items + page_size - 1) // page_size
    
    return {
        "items": paginated_items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    }