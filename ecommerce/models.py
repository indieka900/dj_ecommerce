from django.db import models
from django.forms import ValidationError
from accounts.models import CustomUser as User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class AppContent(models.Model):
    title = models.CharField(max_length=15)
    logo = models.ImageField(upload_to='app_logos/')
    banner = models.ImageField(upload_to='banners')
    tel_no = models.CharField(max_length=20)
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
        if not self.slug:
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
        if not self.slug:
            self.slug = slugify(f"{self.category_name} for {self.parent_category.parent_name}")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.category_name} for {self.parent_category.parent_name}"
    
    class Meta:
        verbose_name_plural = "Categories"
        unique_together = ['category_name', 'parent_category']

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='product')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
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

    def calculate_selling_price(self, custom_discount=None):
        discount = custom_discount if custom_discount is not None else self.discount
        
        if discount < 0 or discount > 100:
            raise ValueError("Discount percentage must be between 0 and 100")
        
        discount_amount = self.price * (discount / 100)
        selling_price = self.price - discount_amount
        
        return round(selling_price, 2)
    
    @property
    def current_selling_price(self):
        return self.calculate_selling_price()


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
        ("Cancelled", "Cancelled")
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='OrderItem')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    transaction_id = models.CharField(max_length=100, unique=True)
    paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.pk} by {self.user.email}"

class OrderItem(models.Model):
    STATUS_CHOICES = (
        ("Pending", "Pending"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled")
    )
    
    order = models.ForeignKey(Order, related_name='order_items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)  # Store the price at purchase time
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    
    def __str__(self):
        return f"{self.product.title} - {self.status}"

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart for {self.user.email}"

    def total_price(self):
        return sum(item.total_item_price() for item in self.cart_items.all())  # assuming cart_items related_name

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    size = models.CharField(max_length=15, blank=True, null=True)
    color = models.CharField(max_length=30, blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Added At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    class Meta:
        verbose_name = _('Cart Item')
        verbose_name_plural = _('Cart Items')
        unique_together = ['cart', 'product', 'size', 'color']
        ordering = ['-added_at']
        indexes = [
            models.Index(fields=['cart', 'product']),
            models.Index(fields=['added_at']),
        ]
    
    def __str__(self):
        return f"{self.quantity} of {self.product.title} in cart for {self.cart.user.email}"

    def total_item_price(self):
        return self.quantity * self.product.current_selling_price
    
    @property
    def total_price(self):
        """
        Calculate total price for this cart item
        """
        return self.product.price * self.quantity

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def clean(self):
        """
        Validate cart item before saving
        """
        # Check product availability
        if self.product.quantity < self.quantity:
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
    AppContent,
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
