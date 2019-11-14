from django import template
from django.template.loader import get_template
from submissions.models import Phase

register = template.Library()

@register.simple_tag(takes_context=True)
def get_navigation(context, template='navigation.html'):
	phases = Phase.objects.filter(active=True)
	phases.prefetch_related('task')
	return get_template(template).render({
			'phases': phases,
		},
		request=context['request'])

print()
print('ABC')
print()
