from django import template

register = template.Library()


@register.filter
def widget_type(field):
    return field.field.widget.__class__.__name__


@register.filter
def add_class(field, css):
    existing = field.field.widget.attrs.get('class', '')
    return field.as_widget(attrs={'class': f'{existing} {css}'.strip()})


@register.filter
def initials(user):
    first, last = (user.first_name or user.username)[:1], (user.last_name or '')[:1]
    return (first + last).upper()
