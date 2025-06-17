from django.db import models
from django.forms import ValidationError
from accounts.models import Address, CustomUser as User
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
import uuid


class AppContent(models.Model):
    title = models.CharField(max_length=15)
    logo = models.ImageField(upload_to='app_logos/')
    banner = models.ImageField(upload_to='banners')
    tel_no = models.CharField(max_length=20)
    location = models.CharField(max_length=50, default='')
    email = models.EmailField()
    favIcon = models.FileField(upload_to='fav-icons/', blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
class Slider(models.Model):
    app = models.ForeignKey(AppContent, on_delete=models.CASCADE)
    title = models.CharField(max_length=20)
    subtitle = models.CharField(max_length=25)
    image = models.ImageField(upload_to='app_siders/')
    
    def __str__(self):
        return self.title
    
class Brand(models.Model):
    brand_title = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.brand_title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.brand_title

class ParentCategory(models.Model):
    parent_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.parent_name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.parent_name
    
    class Meta:
        verbose_name_plural = "Parent Categories"
        
class Category(models.Model):
    category_name = models.CharField(max_length=50)
    parent_category = models.ForeignKey(ParentCategory, on_delete=models.CASCADE)
    slug = models.SlugField(unique=True,  blank=True)
    
    def save(self, *args, **kwargs):
        self.slug = slugify(f"{self.category_name} for {self.parent_category.parent_name}")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.category_name} for {self.parent_category.parent_name}"
    
    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ['category_name', 'parent_category']

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='product')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, related_name='product_brand')
    title = models.CharField(max_length=100)
    # slug = models.SlugField(unique=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    featured = models.BooleanField(default=False)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=0)
    description = models.TextField()
    prod_img = models.ImageField(upload_to='prod_images/')
    keywords = models.TextField()
    rating = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    has_variants = models.BooleanField(default=False)
    min_variant_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    max_variant_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save initial data to get access to related objects

        # Update min and max variant prices if variants exist
        if self.variants.exists():
            variant_prices = self.variants.values_list('variant_price', flat=True)
            variant_prices = [p for p in variant_prices if p is not None]

            if variant_prices:
                self.has_variants = True
                self.min_variant_price = min(variant_prices)
                self.max_variant_price = max(variant_prices)
            else:
                self.has_variants = False
                self.min_variant_price = None
                self.max_variant_price = None
        else:
            self.has_variants = False
            self.min_variant_price = None
            self.max_variant_price = None

        # Save again to persist updated variant-related fields
        super().save(update_fields=[
            'has_variants',
            'min_variant_price',
            'max_variant_price'
        ])


    def calculate_selling_price(self, custom_discount=None, variant_price=None):
        """
        Calculate selling price considering variants and discounts
        
        Args:
            custom_discount: Optional custom discount percentage
            variant_price: Optional specific variant price to calculate from
        """
        discount = custom_discount if custom_discount is not None else self.discount
        base_price = variant_price if variant_price is not None else self.price
        
        if discount < 0 or discount > 100:
            raise ValueError("Discount percentage must be between 0 and 100")
        
        discount_amount = base_price * (discount / 100)
        selling_price = base_price - discount_amount
        
        return round(selling_price, 2)
    
    @property
    def current_selling_price(self):
        return self.calculate_selling_price()

    @property
    def display_price(self):
        """
        Returns a price display that shows variant price range or single price,
        with discounts applied
        """
        if self.has_variants and self.min_variant_price and self.max_variant_price:
            min_selling_price = self.calculate_selling_price(variant_price=self.min_variant_price)
            max_selling_price = self.calculate_selling_price(variant_price=self.max_variant_price)
            
            if min_selling_price == max_selling_price:
                return f"Ksh {min_selling_price}"
            return f"Ksh {min_selling_price} - Ksh {max_selling_price}"
        return f"Ksh {self.current_selling_price}"



    def __str__(self):
        return self.title

class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to="product_images/")
    alt_text = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"Image for {self.product.title}"

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    size = models.CharField(max_length=10, blank=True)
    color = models.CharField(max_length=20, blank=True)
    stock = models.PositiveIntegerField(default=0)
    variant_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def clean(self):
        if self.product.has_variants and not self.variant_price:
            raise ValidationError("Variant price is required for products with size variations")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        
        self.product.save()
    
    @property
    def selling_price(self):
        """
        Calculate the selling price for this specific variant
        """
        if self.variant_price:
            return self.product.calculate_selling_price(variant_price=self.variant_price)
        return self.product.current_selling_price

    def __str__(self):
        return f"{self.product.title} - {self.size}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    name = models.CharField(max_length=50)
    email = models.EmailField()
    review_title = models.CharField(max_length=15)
    review = models.TextField()
    rating = models.DecimalField(max_digits=2, decimal_places=1)
    created_at = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s review for {self.product.title}"
    
    @property
    def rating_percentage(self):
        return self.rating * 15

class Order(models.Model):
    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Processing", "Processing"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
        ("Refunded", "Refunded")
    )

    PAYMENT_STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Cash-On-Delivery", "Cash-On-Delivery"),
        ("Paid", "Paid"),
        ("Failed", "Failed"),
        ("Refunded", "Refunded")
    )
    
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="Pending")
    
    # Address Information
    shipping_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='shipping_orders', blank=True)
    billing_address = models.ForeignKey(Address, on_delete=models.PROTECT, related_name='billing_orders', blank=True)
    
    # Price Information
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.00'))])
    
    # Payment Information
    payment_method = models.CharField(max_length=50, blank=True)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Additional Information
    notes = models.TextField(blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['order_number']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
        ]

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        super().save(*args, **kwargs)

    def generate_order_number(self):
        """Generate a unique order number"""
        return f"ORD-{uuid.uuid4().hex[:8].upper()}"

    @property
    def is_paid(self):
        return self.payment_status == "Paid"

    @property
    def can_cancel(self):
        return self.status in ["Pending", "Processing"]

    def __str__(self):
        return f"Order {self.order_number} - {self.user.email}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.PROTECT)
    product = models.ForeignKey('Product', on_delete=models.PROTECT)
    variant = models.ForeignKey(
        ProductVariant, 
        on_delete=models.PROTECT,
        null=True, 
        blank=True
    )
    
    # Price Information
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Product Information at Time of Purchase
    product_name = models.CharField(max_length=255)  # Store product name at time of purchase
    variant_info = models.JSONField(null=True, blank=True)  # Store variant details (size, color, etc.)
    
    class Meta:
        ordering = ['id']
        indexes = [
            models.Index(fields=['order', 'product']),
        ]

    def save(self, *args, **kwargs):
        # Calculate subtotal
        self.subtotal = self.quantity * self.unit_price
        
        # Store current product information
        self.product_name = self.product.title
        if self.variant:
            self.variant_info = {
                'size': self.variant.size,
                'color': self.variant.color,
                'variant_price': str(self.variant.variant_price)
            }
        
        super().save(*args, **kwargs)

    def __str__(self):
        variant_info = f" ({self.variant})" if self.variant else ""
        return f"{self.quantity}x {self.product_name}{variant_info}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.email}"

    def total_price(self):
        return sum(item.total_item_price for item in self.cart_items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(
        ProductVariant, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product', 'variant']
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['cart', 'product']),
            models.Index(fields=['added_at']),
        ]
    
    def __str__(self):
        variant_info = f" ({self.variant})" if self.variant else ""
        return f"{self.quantity} of {self.product.title}{variant_info}"

    @property
    def total_item_price(self):
        """
        Calculate total price for this cart item
        """
        # Use variant price if exists, otherwise use product price
        price = (self.variant.selling_price if self.variant and self.variant.variant_price 
                 else self.product.current_selling_price)
        return self.quantity * price

    def clean(self):
        """
        Validate cart item before saving
        """
        # Validate quantity against product stock
        available_stock = (
            self.variant.stock if self.variant 
            else self.product.quantity
        )
        # print(available_stock)
        
        if self.quantity > available_stock:
            raise ValidationError(_('Requested quantity exceeds available stock'))


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Wishlist for {self.user.email}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['wishlist', 'product']

    def __str__(self):
        return f"{self.product.title} in {self.wishlist.user.email}'s wishlist"
    
models_ = [
    Slider,
    Brand,
    Category,
    ParentCategory,
    Cart,
    CartItem,
    Product,
    ProductVariant,
    ProductImage,
    Order,
    OrderItem,
    Wishlist,
    WishlistItem,
    Review,
]
#url
'''
https://github.com/quintuslabs/fashion-cube.git
https://github.com/noorjsdivs/orebishopping
'''    

# Create your models here.
