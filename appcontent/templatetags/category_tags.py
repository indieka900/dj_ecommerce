from django import template

register = template.Library()

@register.inclusion_tag('includes/category-section.html')
def render_category_section(category_data):
    """Render a complete category section with tabs"""
    return {'data': category_data}

@register.inclusion_tag('includes/product-tabs.html')
def render_product_tabs(category_data):
    """Render product tabs for a category"""
    return {'data': category_data}

@register.filter
def has_products(product_list):
    """Check if product list has items"""
    return product_list and len(product_list) > 0