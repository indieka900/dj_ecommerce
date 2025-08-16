from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply filter for template calculations"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def star_rating(rating):
    """Generate star rating HTML"""
    try:
        rating = float(rating)
        width = (rating / 5) * 100
        return mark_safe(f'<div class="star" title="{rating} out of 5"><span style="width:{width}%"></span></div>')
    except (ValueError, TypeError):
        return mark_safe('<div class="star"><span style="width:0%"></span></div>')

@register.filter
def format_price(price):
    """Format price with currency"""
    try:
        return f"Ksh {float(price):,.2f}"
    except (ValueError, TypeError):
        return "Ksh 0.00"

@register.filter
def discount_tag(product):
    """Generate discount tag"""
    if hasattr(product, 'discount') and product.discount > 0:
        return mark_safe(f'<div class="tag sale"><span>-{int(product.discount)}%</span></div>')
    elif hasattr(product, 'featured') and product.featured:
        return mark_safe('<div class="tag featured"><span>FEATURED</span></div>')
    return ""

@register.inclusion_tag('includes/product-card.html')
def product_card(product):
    """Render product card"""
    return {'item': product}

@register.simple_tag
def category_url(category_type, slug):
    """Generate category URLs"""
    if category_type == 'parent':
        return f'/shop/{slug}/'
    elif category_type == 'category':
        return f'/category/{slug}/'
    return '#'