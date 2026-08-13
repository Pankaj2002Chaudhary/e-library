from rest_framework.pagination import PageNumberPagination


class BookPagination(PageNumberPagination):
    """
    Custom pagination for book listings.
    """

    # Default number of books per page
    page_size = 10

    # Allow clients to override page size
    page_size_query_param = "page_size"

    # Prevent excessively large page requests
    max_page_size = 100