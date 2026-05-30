# catalog/views.py
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Product
from .serializers import ProductSerializer


class ProductListView(generics.ListAPIView):
    serializer_class   = ProductSerializer

    def get_queryset(self):
        queryset = Product.objects.all()

        # Filter by brand
        brand = self.request.query_params.get("brand")
        if brand:
            queryset = queryset.filter(brand__icontains=brand)

        # Filter by gender
        gender = self.request.query_params.get("gender")
        if gender:
            queryset = queryset.filter(gender__iexact=gender)

        # Filter by perfume type
        perfume_type = self.request.query_params.get("type")
        if perfume_type:
            queryset = queryset.filter(perfume_type__iexact=perfume_type)

        # Filter by ML size
        ml = self.request.query_params.get("ml")
        if ml:
            queryset = queryset.filter(ml=ml)

        # Filter by source site
        source = self.request.query_params.get("source")
        if source:
            queryset = queryset.filter(source_site__icontains=source)

        # Filter by availability
        available = self.request.query_params.get("available")
        if available:
            queryset = queryset.filter(available=available.lower() == "true")

        return queryset


@api_view(["GET"])
def cheapest_view(request):
    """
    Find cheapest source for a specific product.
    Usage: /api/cheapest/?brand=LATTAFA&name=YARA&ml=100
    """
    brand = request.query_params.get("brand", "")
    name  = request.query_params.get("name", "")
    ml    = request.query_params.get("ml")

    queryset = Product.objects.filter(
        brand__icontains=brand,
        product_name__icontains=name,
        available=True
    )
    if ml:
        queryset = queryset.filter(ml=ml)

    # Sort by price — cheapest first
    queryset = queryset.order_by("sale_price")

    if not queryset.exists():
        return Response({"message": "No products found"}, status=404)

    serializer = ProductSerializer(queryset, many=True)
    return Response({
        "query":    {"brand": brand, "name": name, "ml": ml},
        "cheapest": serializer.data[0],
        "all_sources": serializer.data
    })