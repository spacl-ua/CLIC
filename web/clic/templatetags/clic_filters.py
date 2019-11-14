from django import template

register = template.Library()

@register.filter
def get(h, key):
    return h.get(key, '')
