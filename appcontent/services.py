from django.db.models import Q, Count, Avg, Sum
from ecommerce.models import ParentCategory, Product, Category

class ProductService:
    
    @staticmethod
    def get_parent_categories_with_products(limit_categories=None, products_per_tab=8):
        """
        Get parent categories with their products organized by tabs
        (Latest, Best Selling, Top Rating, Featured)
        """
        # Get parent categories that have products
        parent_categories = ParentCategory.objects.annotate(
            total_products=Count('category__product', filter=Q(category__product__quantity__gt=0))
        ).filter(total_products__gt=0).order_by('id')
        
        if limit_categories:
            parent_categories = parent_categories[:limit_categories]
        
        categories_data = []
        
        for parent_cat in parent_categories:
            # Base queryset for this parent category
            base_products = Product.objects.filter(
                category__parent_category=parent_cat,
                quantity__gt=0
            ).select_related('category', 'brand')
            
            category_data = {
                'parent_category': parent_cat,
                'slug': parent_cat.slug,
                'latest_products': base_products.order_by('-created_at')[:products_per_tab],
                'featured_products': base_products.filter(featured=True).order_by('-created_at')[:products_per_tab],
                'best_selling_products': ProductService._get_best_selling_by_parent(parent_cat, products_per_tab),
                'top_rating_products': base_products.filter(rating__gt=0).order_by('-rating', '-created_at')[:products_per_tab],
                'total_products': base_products.count(),
            }
            
            categories_data.append(category_data)
        
        return categories_data
    
    @staticmethod
    def _get_best_selling_by_parent(parent_category, limit):
        """
        Get best selling products for a parent category.
        This is a placeholder - implement based on your sales tracking.
        """
        # Option 1: Use rating as proxy for best selling
        # return Product.objects.filter(
        #     category__parent_category=parent_category,
        #     quantity__gt=0
        # ).order_by('-rating', '-created_at')[:limit]
        
        # Option 2: If you have order items, use actual sales data
        from django.db.models import Count
        return Product.objects.filter(
            category__parent_category=parent_category,
            quantity__gt=0
        ).annotate(
            sales_count=Count('orderitem__quantity')
        ).order_by('-sales_count', '-created_at')[:limit]
    
    @staticmethod
    def get_featured_categories(limit=6):
        """Get categories that have the most products"""
        return Category.objects.annotate(
            product_count=Count('product', filter=Q(product__quantity__gt=0))
        ).filter(product_count__gt=0).order_by('-product_count')[:limit]
    
    @staticmethod
    def get_category_stats():
        """Get statistics for all categories"""
        return {
            'total_products': Product.objects.filter(quantity__gt=0).count(),
            'total_categories': Category.objects.annotate(
                product_count=Count('product', filter=Q(product__quantity__gt=0))
            ).filter(product_count__gt=0).count(),
            'total_parent_categories': ParentCategory.objects.annotate(
                product_count=Count('category__product', filter=Q(category__product__quantity__gt=0))
            ).filter(product_count__gt=0).count(),
        }