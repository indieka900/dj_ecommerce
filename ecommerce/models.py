from django.db import models
from accounts.models import CustomUser as User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify

class Brand(models.Model):
    brand_title = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.brand_title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.brand_title

class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.category_name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.category_name
    
    class Meta:
        verbose_name_plural = "Categories"

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True)
    title = models.CharField(max_length=100)
    # slug = models.SlugField(unique=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    featured = models.BooleanField(default=False)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    description = models.TextField()
    keywords = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def calculate_selling_price(self, custom_discount=None):
        discount = custom_discount if custom_discount is not None else self.discount_price
        
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
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.TextField()
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username}'s review for {self.product.title}"

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
    products = models.ManyToManyField(Product, through='CartItem')
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
    
    def __str__(self):
        return f"{self.quantity} of {self.product.title} in cart for {self.cart.user.email}"

    def total_item_price(self):
        return self.quantity * self.product.price


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    products = models.ManyToManyField(Product, through='WishlistItem')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wishlist for {self.user.email}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.product.title} in {self.wishlist.user.email}'s wishlist"
    
models_ = [
    Brand,
    Category,
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
