import uuid

from django import forms
from django.template.loader import render_to_string

from wagtail.core import blocks
from wagtailstreamforms.models import Form


class InfoBlock(blocks.CharBlock):
    def render_form(self, value, prefix='', errors=None):
        field = self.field
        widget = field.widget

        widget_attrs = {'id': prefix, 'placeholder': self.label, 'disabled': 'disabled'}

        shown_value = value if value else field.help_text

        field_value = field.prepare_value(self.value_for_form(shown_value))

        if hasattr(widget, 'render_with_errors'):
            widget_html = widget.render_with_errors(prefix, field_value, attrs=widget_attrs, errors=errors)
            widget_has_rendered_errors = True
        else:
            widget_html = widget.render(prefix, field_value, attrs=widget_attrs)
            widget_has_rendered_errors = False

        return render_to_string('wagtailadmin/block_forms/field.html', {
            'name': self.name,
            'classes': self.meta.classname,
            'widget': widget_html,
            'field': field,
            'errors': errors if (not widget_has_rendered_errors) else None
        })


class FormChooserBlock(blocks.ChooserBlock):
    target_model = Form
    widget = forms.Select

    def value_for_form(self, value):
        if isinstance(value, self.target_model):
            return value.pk
        return value

    def value_from_form(self, value):
        if value == '':
            return None
        return super().value_from_form(value)

    def to_python(self, value):
        if value is None:
            return value
        else:
            try:
                return self.target_model.objects.get(pk=value)
            except self.target_model.DoesNotExist:
                return None


class WagtailFormBlock(blocks.StructBlock):
    form = FormChooserBlock()
    form_action = blocks.CharBlock(
        required=False,
        help_text='The form post action. "" or "." for the current page or a url'
    )
    form_reference = InfoBlock(
        required=False,
        help_text='This form will be given a unique reference once saved'
    )

    class Meta:
        icon = 'icon icon-form'
        template = None

    def render(self, value, context=None):
        form = value.get('form')

        # check if we have a form, as they can be deleted, and we dont want to break the site with
        # a none template value
        if form:
            self.meta.template = form.template_name
        else:
            self.meta.template = 'streamforms/non_existent_form.html'

        return super().render(value, context)

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context)

        form = value.get('form')
        form_reference = value.get('form_reference')

        if form:

            # check the context for an invalid form submitted to the page.
            # Use that instead if it has the same unique form_reference number
            invalid_form_reference = context.get('invalid_stream_form_reference')
            invalid_form = context.get('invalid_stream_form')

            if invalid_form_reference and invalid_form and invalid_form_reference == form_reference:
                context['form'] = invalid_form
            else:
                context['form'] = form.get_form(initial={'form_id': form.id, 'form_reference': form_reference})

        return context

    def clean(self, value):
        result = super().clean(value)

        # set to a new uuid so we can ensure we can identify this form
        # against other forms of the same type in the page
        if not result.get('form_reference'):
            result['form_reference'] = uuid.uuid4()

        return result
