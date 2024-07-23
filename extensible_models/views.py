from rest_framework.decorators import action
from rest_framework.response import Response


class ExtensibleModelViewSetMixin:

    @action(detail=False, methods=["get"])
    def schema(self, request):
        serializer = self.get_serializer()
        return Response(
            {
                "fields": self.get_serializer().get_fields(),
                "extension_schema": (
                    serializer.extension_schema.schema
                    if serializer.extension_schema
                    else None
                ),
            }
        )

    def options(self, request, *args, **kwargs):
        """
        Handler for OPTIONS requests.
        """
        if self.metadata_class is None:
            return self.http_method_not_allowed(request, *args, **kwargs)
        data = self.metadata_class().determine_metadata(request, self)
        serializer = self.get_serializer()
        if serializer.extension_schema:
            data["extension_schema"] = serializer.extension_schema.schema
        return Response(data)
