"""
Custom template filters for courses app.
"""
from django import template
import re

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get an item from a dictionary by key.
    Usage: {{ mydict|get_item:key }}
    """
    if dictionary is None:
        return None
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter
def in_list(value, the_list):
    """
    Check if value is in list.
    Usage: {% if value|in_list:my_list %}
    """
    return value in the_list


@register.filter
def replace(value, args):
    """
    Replace occurrences of a string.
    Usage: {{ value|replace:"old,new" }}
    """
    if not value:
        return value
    try:
        old, new = args.split(',')
        return str(value).replace(old, new)
    except ValueError:
        return value


@register.filter
def youtube_embed(url):
    """
    Convert YouTube URL to embed URL.
    Handles: youtube.com/watch?v=ID, youtu.be/ID, youtube.com/embed/ID
    Usage: {{ video_url|youtube_embed }}
    """
    if not url:
        return url
    
    url = str(url)
    
    # Already an embed URL
    if 'youtube.com/embed/' in url:
        # Ensure nocookie domain for better iframe support
        return url.replace('youtube.com', 'youtube-nocookie.com')
    
    # Extract video ID from various YouTube URL formats
    video_id = None
    
    # youtube.com/watch?v=VIDEO_ID
    match = re.search(r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)', url)
    if match:
        video_id = match.group(1)
    
    # youtu.be/VIDEO_ID
    if not video_id:
        match = re.search(r'youtu\.be/([a-zA-Z0-9_-]+)', url)
        if match:
            video_id = match.group(1)
    
    if video_id:
        return f'https://www.youtube-nocookie.com/embed/{video_id}'
    
    return url


@register.filter
def multiply(value, arg):
    """Multiply the value by arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Divide the value by arg."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
