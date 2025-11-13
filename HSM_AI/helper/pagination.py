from rest_framework.pagination import PageNumberPagination
from HSM_AI.utils import success_response  # ✅ correct import path

class CustomPagination(PageNumberPagination):
    page_size = 10                  # Default page size
    page_size_query_param = 'limit' # Allow client to override
    max_page_size = 100

    def get_paginated_response(self, data):
        return success_response(
            message="Modules fetched successfully.",
            data={
                "list": data,                 # Actual results
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
            },
        )
