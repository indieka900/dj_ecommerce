from rest_framework import viewsets
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from ecommerce.models import (
    Brand, Category, Product, Review, Order, Cart, 
    Wishlist, ProductImage, ProductVariant, ParentCategory
)
from .serializers import (
    BrandSerializer, CategorySerializer, ProductSerializer, ReviewSerializer, 
    CartSerializer, WishlistSerializer, ProductImageSerializer, 
    ProductVariantSerializer, BulkProductImageSerializer, ParentCategorySerializer
)
from appcontent.utils import IsAdminUserOrReadOnly
from django.db.models import Sum, Count

class ParendCategoryViewSet(viewsets.ModelViewSet):
    queryset = ParentCategory.objects.all()
    serializer_class = ParentCategorySerializer
    permission_classes = [IsAdminUserOrReadOnly]
    
class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    
    def get_queryset(self):
        """
        Override queryset to include product count for GET requests
        """
        if self.action in ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy']:
            return Brand.objects.annotate(
                product_count=Count('product_brand') 
            )
        return super().get_queryset()

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUserOrReadOnly]
    
    def get_queryset(self):
        """
        Override queryset to include product count for GET requests
        """
        if self.action in ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy']:
            return Category.objects.annotate(
                product_count=Count('product') 
            )
        return super().get_queryset()

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.prefetch_related('variants', 'images').all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUserOrReadOnly]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# class OrderViewSet(viewsets.ModelViewSet):
#     queryset = Order.objects.prefetch_related('items__product').annotate(
#         total_items=Sum('items__quantity')
#     )
#     serializer_class = OrderSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Order.objects.filter(user=self.request.user)

class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)
    
class ProductImageViewSet(viewsets.ModelViewSet):
    queryset = ProductImage.objects.all()
    serializer_class = ProductImageSerializer
    permission_classes = [IsAdminUserOrReadOnly]
    
    def perform_create(self, serializer):
        product = self.request.data.get('product')
        if not product:
            raise ValueError("Product must be specified for the image.")
        try:
            product = Product.objects.get(id=product)
        except Product.DoesNotExist:
            raise ValueError("Product with the specified ID does not exist.")
        serializer.save(product=product)
        
    @action(detail=False, methods=['post'], url_path='bulk-upload')
    def bulk_upload(self, request):
        """
        Bulk upload multiple images for a product
        
        Expected payload:
        {
            "product": 1,
            "images": [image1, image2, image3, ...],
            "alt_texts": ["Alt text 1", "Alt text 2", "Alt text 3", ...] (optional)
        }
        """
        try:
            serializer = BulkProductImageSerializer(data=request.data)
            
            if serializer.is_valid():
                with transaction.atomic():
                    created_images = serializer.save()
                
                # Serialize the created images for response
                response_serializer = ProductImageSerializer(created_images, many=True)
                
                return Response({
                    'message': f'Successfully uploaded {len(created_images)} images',
                    'images': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response(
                {'error': f'Error uploading images: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    @action(detail=False, methods=['post'], url_path='bulk-upload-form')
    def bulk_upload_form(self, request):
        """
        Alternative bulk upload endpoint that handles form data
        Useful when uploading from HTML forms or when images are sent as separate fields
        
        Expected form data:
        - product: 1
        - image_1: file
        - image_2: file
        - image_3: file
        - alt_text_1: "Alt text 1" (optional)
        - alt_text_2: "Alt text 2" (optional)
        - alt_text_3: "Alt text 3" (optional)
        """
        try:
            product_id = request.data.get('product')
            if not product_id:
                return Response(
                    {'error': 'Product ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return Response(
                    {'error': 'Product with the specified ID does not exist'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Extract images and alt texts from form data
            images = []
            alt_texts = []
            
            # Look for image fields (image_1, image_2, etc.)
            for key, value in request.data.items():
                if key.startswith('image_') and hasattr(value, 'read'):
                    images.append(value)
                    
                    # Look for corresponding alt text
                    alt_key = key.replace('image_', 'alt_text_')
                    alt_text = request.data.get(alt_key, '')
                    alt_texts.append(alt_text)

            if not images:
                return Response(
                    {'error': 'No images provided'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if len(images) > 10:
                return Response(
                    {'error': 'Maximum 10 images allowed per request'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            created_images = []
            
            with transaction.atomic():
                for i, image in enumerate(images):
                    alt_text = alt_texts[i] if i < len(alt_texts) else ''
                    
                    product_image = ProductImage.objects.create(
                        product=product,
                        image=image,
                        alt_text=alt_text
                    )
                    created_images.append(product_image)

            # Serialize the created images for response
            response_serializer = ProductImageSerializer(created_images, many=True)
            
            return Response({
                'message': f'Successfully uploaded {len(created_images)} images',
                'images': response_serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {'error': f'Error uploading images: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAdminUserOrReadOnly]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        product = self.request.data.get('product_id')
        if not product:
            raise ValueError("Product must be specified for the variant.")
        prod = get_object_or_404(Product, id=product)
        if not prod.has_variants:
            prod.has_variants = True
            prod.save()
        serializer.save(product=prod)
        
    @action(detail=False, methods=['get'], url_path='product-variants')
    def product_variants(self, request):
        """
        Get all variants for a specific product

        Example: GET /api/product-variants/?product=1
        """
        product_id = request.query_params.get('product')
        if not product_id:
            return Response(
                {'error': 'Product ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(id=product_id)
            variants = ProductVariant.objects.filter(product=product)
            serializer = self.get_serializer(variants, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Product.DoesNotExist:
            return Response(
                {'error': 'Product with the specified ID does not exist'}, 
                status=status.HTTP_404_NOT_FOUND
            )
