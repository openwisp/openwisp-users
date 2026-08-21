from django.dispatch import Signal

organization_disabled = Signal()
organization_disabled.__doc__ = """
Providing arguments: ['instance']
"""
organization_enabled = Signal()
organization_enabled.__doc__ = """
Providing arguments: ['instance']
"""
