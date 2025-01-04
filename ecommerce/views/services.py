from decimal import Decimal
from django.db.models import Avg, Count, Q, FloatField, F, Min, Max
from django.db.models.functions import Cast
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.db import transaction
from django.core.exceptions import ValidationError
from django.shortcuts import get_list_or_404
from ..models import (
    Product, Category, AppContent, Slider, Wishlist, Cart,CartItem,
    ParentCategory, Review, WishlistItem, ProductVariant, Order, OrderItem
)

class CommonService:
    @staticmethod
    def get_common_context(request):
        """
        Retrieve common context data for the application.
        """
        # Fetch app-wide content
        app_data = AppContent.objects.first()
        
        # Initialize default context
        context = {
            'app_data': app_data,
            'sliders': Slider.objects.filter(app=app_data),
            'categories': Category.objects.all(),
            'cart_items': [],
            'total_items': 0,
            'total_price': 0
        }
        
        if request.user.is_authenticated:
            try:
                cart = Cart.objects.prefetch_related(
                    'cart_items__product'
                ).get(user=request.user)
                
                cart_items = cart.cart_items.all()
                
                context.update({
                    'cart_items': cart_items,
                    'total_items': cart_items.count(),
                    'total_price': cart.total_price() if cart_items.exists() else 0
                })
            
            except Cart.DoesNotExist:
                pass
        
        return context

class ProductService:
    @classmethod
    def get_product_list(cls, page_number=1, per_page=12):
        """
        Retrieve paginated product list with optional filtering.
        
        Args:
            page_number (int): Current page number
            per_page (int): Number of products per page
        
        Returns:
            tuple: Paginated products and paginator object
        """
        products = Product.objects.select_related('category__parent_category', 'brand')
        paginator = Paginator(products, per_page)
        page_obj = paginator.get_page(page_number)
        
        return page_obj, paginator

    @classmethod
    def get_products_by_category(cls, category_slug, page_number=1, per_page=12):
        """
        Retrieve products for a specific category.
        
        Args:
            category_slug (str): Slug of the category
            page_number (int): Current page number
            per_page (int): Number of products per page
        
        Returns:
            tuple: Paginated products and paginator object
        """
        try:
            # Fetch the category with its parent
            category = Category.objects.select_related('parent_category').get(
                Q(slug__iexact=category_slug)
            )
            
            # Filter products by this category
            products = Product.objects.filter(category=category)
            
            # Apply pagination
            paginator = Paginator(products, per_page)
            page_obj = paginator.get_page(page_number)
            
            return page_obj, paginator, category
        
        except Category.DoesNotExist:
            return None, None, None

    @classmethod
    def get_products_by_parent_category(cls, parent_category_slug, page_number=1, per_page=12):
        """
        Retrieve products for a specific parent category.
        Returns:
            tuple: Paginated products, paginator, and parent category
        """
        try:
            # Fetch the parent category
            parent_category = ParentCategory.objects.get(slug=parent_category_slug)
            
            # Filter products by categories under this parent category
            products = Product.objects.filter(
                category__parent_category=parent_category
            ).select_related('category', 'brand')
            
            categories = Category.objects.filter(
                parent_category=parent_category
            ).annotate(
                product_count=Count('product', filter=Q(product__isnull=False))
            )
            
            paginator = Paginator(products, per_page)
            page_obj = paginator.get_page(page_number)
            
            return page_obj, paginator, parent_category, categories
        
        except ParentCategory.DoesNotExist:
            return None, None, None, None

    @classmethod
    def filter_products(cls, 
                        category_slug=None, 
                        parent_category_slug=None, 
                        min_price=None, 
                        max_price=None, 
                        brands=None, 
                        page_number=1, 
                        per_page=12):
        """
        Advanced product filtering method.
        
        Args:
            category_slug (str, optional): Category slug to filter
            parent_category_slug (str, optional): Parent category slug to filter
            min_price (float, optional): Minimum price filter
            max_price (float, optional): Maximum price filter
            brands (list, optional): List of brand IDs to filter
            page_number (int): Current page number
            per_page (int): Number of products per page
        
        Returns:
            tuple: Paginated products, paginator, and additional context
        """
        # Start with base queryset
        products = Product.objects.select_related('category__parent_category', 'brand')
        
        # Filter by category
        if category_slug:
            try:
                category = Category.objects.get(
                    Q(category_name__iexact=category_slug) | 
                    Q(slug=category_slug)
                )
                products = products.filter(category=category)
            except Category.DoesNotExist:
                return None, None, {'error': 'Category not found'}
        
        # Filter by parent category
        if parent_category_slug:
            try:
                parent_category = ParentCategory.objects.get(slug=parent_category_slug)
                products = products.filter(category__parent_category=parent_category)
            except ParentCategory.DoesNotExist:
                return None, None, {'error': 'Parent category not found'}
        
        # Price filtering
        if min_price is not None:
            products = products.annotate(
                selling_price=Cast('price', FloatField()) * (1 - F('discount') / 100)
            ).filter(selling_price__gte=min_price)
        
        if max_price is not None:
            products = products.annotate(
                selling_price=Cast('price', FloatField()) * (1 - F('discount') / 100)
            ).filter(selling_price__lte=max_price)
        
        # Brand filtering
        if brands:
            products = products.filter(brand__id__in=brands)
        
        # Pagination
        paginator = Paginator(products, per_page)
        page_obj = paginator.get_page(page_number)
        
        # Prepare context
        context = {
            'total_products': products.count(),
            'applied_filters': {
                'category': category_slug,
                'parent_category': parent_category_slug,
                'min_price': min_price,
                'max_price': max_price,
                'brands': brands
            }
        }
        
        return page_obj, paginator, context

    @classmethod
    def get_available_filters(cls, parent_category_slug=None, category_slug=None):
        """
        Retrieve available filters for product listing.
        
        Args:
            parent_category_slug (str, optional): Parent category slug
            category_slug (str, optional): Category slug
        
        Returns:
            dict: Available filters including price range, brands, etc.
        """
        # Base queryset
        products = Product.objects.all()
        
        # Filter by category or parent category if provided
        if category_slug:
            try:
                category = Category.objects.get(
                    Q(category_name__iexact=category_slug) | 
                    Q(slug=category_slug)
                )
                products = products.filter(category=category)
            except Category.DoesNotExist:
                return {}
        
        if parent_category_slug:
            try:
                parent_category = ParentCategory.objects.get(slug=parent_category_slug)
                products = products.filter(category__parent_category=parent_category)
            except ParentCategory.DoesNotExist:
                return {}
        
        # Calculate price range
        price_range = products.aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        
        # Get available brands
        available_brands = products.values('brand__id', 'brand__name').distinct()
        
        return {
            'price_range': price_range,
            'brands': list(available_brands)
        }

    @classmethod
    def get_product_detail(cls, pk):
        """
        Retrieve detailed product information.
        
        Args:
            pk (int): Primary key of the product
        
        Returns:
            dict: Comprehensive product details
        """
        # Fetch product with related data
        product = Product.objects.select_related(
            'category'
        ).prefetch_related(
            'images',
            'variants'
        ).get(pk=pk)
        
        # Fetch reviews with annotations
        reviews = Review.objects.filter(product=product)
        
        # Calculate average rating
        average_rating = reviews.aggregate(
            avg_rating=Avg('rating')
        )['avg_rating'] or 0.0
        
        # Prepare variant information
        variants = product.variants.all()
        
        # Group variants by size if applicable
        variant_groups = {}
        if product.has_variants:
            for variant in variants:
                if variant.size:
                    variant_groups.setdefault(variant.size, []).append(variant)
        
        # Get similar products
        similar_products = Product.objects.filter(
            category=product.category
        ).exclude(pk=product.pk)[:4]
        
        # Get unique variants
        variants = product.variants.all()
        unique_colors = list(set(
            variant.color for variant in variants if variant.color
        ))
        
        return {
            'product': product,
            'reviews': reviews,
            'average_rating': round(average_rating, 1),
            'images': product.images.all(),
            'similar_products': similar_products,
            'variants': variants,
            'variant_groups': variant_groups,
            'unique_colors': unique_colors
        }

    @classmethod
    def get_latest_products(cls, limit=4):
        """
        Retrieve latest products.
        
        Args:
            limit (int): Number of products to retrieve
        
        Returns:
            QuerySet: Latest products
        """
        return Product.objects.all()[:limit]

    @classmethod
    def get_featured_categories(cls, limit=3):
        """
        Retrieve featured categories.
        
        """
        return Category.objects.all()[:limit]
    
    @classmethod
    def get_featured_products(cls):
        """
        Retrieve featured products.
        
        """
        # prds = get_list_or_404(Product, featured=True)
        prds = Product.objects.filter(featured=True)
        return prds if prds else []
    
    @classmethod
    def search_products(cls, query, category=None, per_page=10, page_number=1):
        """
        search products with category filtering
        """
        # Validate and sanitize inputs
        if not query:
            return None, None
        
        # Optimize the query with select_related and prefetch_related
        base_query = Product.objects.select_related(
            'brand', 
            'category', 
            'category__parent_category'
        )
        
        # Construct search conditions
        search_conditions = (
            Q(title__icontains=query) |
            Q(keywords__icontains=query) |
            Q(brand__brand_title__icontains=query) |
            Q(category__category_name__icontains=query) |
            Q(category__parent_category__parent_name__icontains=query)
        )
        
        # Apply category filter if provided
        if category:
            products = base_query.filter(category=category).filter(search_conditions)
        else:
            products = base_query.filter(search_conditions)
        
        # Remove duplicates and ensure unique results
        products = products.distinct()
        
        try:
            paginator = Paginator(products, per_page)
            page_obj = paginator.get_page(page_number)
            return page_obj, paginator
        except (EmptyPage, InvalidPage):
            return None, None
    
class CartService:
    """
    Service class to handle cart-related operations
    """
    @classmethod
    @transaction.atomic
    def add_to_cart(cls, user, product : Product, quantity=1, size=None, color=None):
        
        if quantity < 1:
            raise ValidationError("Quantity must be at least 1")

        # Get or create user's cart
        cart, _ = Cart.objects.get_or_create(user=user)

        # Find variant if product has variants
        variant = None
        if product.has_variants:
            # Find matching variant
            variant = ProductVariant.objects.filter(
                Q(product=product) & (
                Q(size=size) |
                Q(color=color))
            ).first()
            
            if variant:
                if variant.stock < quantity:
                    raise ValidationError(f"Only {variant.stock} items available in this variant")
                
                variant.stock -= quantity
                variant.save()
                product.quantity -= quantity
                product.save()
            
        else:
            # Check product stock for non-variant products
            if product.quantity < quantity:
                raise ValidationError(f"Only {product.quantity} items available")
            
            # Reduce product stock
            product.quantity -= quantity
            product.save()

        # Try to find existing cart item
        try:
            cart_item = CartItem.objects.get(
                cart=cart,
                product=product,
                variant=variant
            )
            cart_item.quantity += quantity
        except CartItem.DoesNotExist:
            cart_item = CartItem(
                cart=cart,
                product=product,
                variant=variant,
                quantity=quantity
            )
        
        # Validate and save
        cart_item.full_clean()
        cart_item.save()
        
        return cart_item
    
    @classmethod
    @transaction.atomic
    def update_cart_item(cls, cart_item:CartItem, new_quantity):
        
        product = cart_item.product
        
        # Validate quantity
        if new_quantity < 1:
            raise ValidationError("Quantity must be at least 1.")
        
        # Check if enough product is available
        available_quantity = product.quantity + cart_item.quantity
        if new_quantity > available_quantity:
            raise ValidationError(f"Only {available_quantity} items available.")
        
        # Calculate quantity difference
        qty_diff = new_quantity - cart_item.quantity
        
        # Update product and cart item quantities
        product.quantity -= qty_diff
        cart_item.quantity = new_quantity
        
        # Save changes
        product.save()
        cart_item.save()
        
        return cart_item

    @classmethod
    @transaction.atomic
    def remove_cart_item(cls, cart_item:CartItem):
        product = cart_item.product
        if product.has_variants:
            # Find matching variant
            variant = ProductVariant.objects.filter(
                Q(product=product) |
                Q(size=cart_item.variant.size) |
                Q(color=cart_item.variant.color)
            ).first()

            if variant:
                variant.stock += cart_item.quantity
                variant.save()
        
        # Return product quantity back to inventory
        product.quantity += cart_item.quantity
        product.save()
        
        # Delete the cart item
        cart_item.delete()
        
        return product
    
class WishListService:
    
    @classmethod
    @transaction.atomic
    def add_to_wishlist(self, user, product):
        w_list, _ = Wishlist.objects.get_or_create(user=user)
        try:
            wishlist_item = WishlistItem.objects.get(wishlist=w_list, product=product)
        except WishlistItem.DoesNotExist:
            wishlist_item = WishlistItem.objects.create(
                wishlist = w_list, product=product
            )
        return wishlist_item
    
# order service
class OrderService:
    @classmethod
    @transaction.atomic
    def create_order_from_cart(cls, cart : Cart, shipping_address, billing_address=None, payment_method=None, notes=None):
        """
        Create an order from a cart
        """
        # Calculate totals
        subtotal = cart.total_price()
        shipping_cost = Decimal('0.00')  # Calculate based on your shipping rules
        tax = subtotal * Decimal('0.16')  # 16% VAT for example
        total = subtotal + shipping_cost + tax

        # Create order
        order = Order.objects.create(
            user=cart.user,
            shipping_address=shipping_address,
            billing_address=billing_address or shipping_address,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax=tax,
            total=total,
            payment_method=payment_method,
            notes=notes
        )

        # Create order items from cart items
        for cart_item in cart.cart_items.all():
            price = (cart_item.variant.variant_price 
                    if cart_item.variant 
                    else cart_item.product.current_selling_price)
            
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                variant=cart_item.variant,
                quantity=cart_item.quantity,
                unit_price=price,
                subtotal=price * cart_item.quantity
            )

        # Clear the cart
        # cart.cart_items.all().delete()

        return order
