from django import template
from django.template.loader import get_template
from submissions.models import Phase

register = template.Library()


@register.simple_tag(takes_context=True)
def get_navigation(context, template='navigation.html'):
	return get_template(template).render({
		},
		request=context['request'])


@register.tag(name="evaluate")
def evaluate(parser, token):
	"""
	Parses text fields for template tags.
	Usage::
		{% evaluate object.textfield %}
	"""
	try:
		tag_name, variable = token.split_contents()

	except ValueError:
		raise template.TemplateSyntaxError(
			'{0} tag requires a single argument'.format(token.contents.split()[0]))

	return EvaluateNode(variable)


class EvaluateNode(template.Node):
	def __init__(self, variable):
		self.variable = template.Variable(variable)

	def render(self, context):
		try:
			content = self.variable.resolve(context)
			t = template.Template(content)
			return t.render(context)

		except (template.VariableDoesNotExist, template.TemplateSyntaxError) as error:
			return error
