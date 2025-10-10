from django import template
from django.contrib.auth.models import AnonymousUser

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def has_role(user, role_name):
    """
    Check if user has specific role.

    Args:
        user: User instance
        role_name: Role name to check ('tester', 'programmer')

    Returns:
        bool: True if user has the role, False otherwise
    """
    if isinstance(user, AnonymousUser) or not hasattr(user, 'employee'):
        return False

    return user.employee.role == role_name


@register.filter
def is_tester(user):
    """
    Check if user is a tester.

    Args:
        user: User instance

    Returns:
        bool: True if user is a tester, False otherwise
    """
    if isinstance(user, AnonymousUser) or not hasattr(user, 'employee'):
        return False

    return user.employee.is_tester


@register.filter
def is_programmer(user):
    """
    Check if user is a programmer.

    Args:
        user: User instance

    Returns:
        bool: True if user is a programmer, False otherwise
    """
    if isinstance(user, AnonymousUser) or not hasattr(user, 'employee'):
        return False

    return user.employee.is_programmer
