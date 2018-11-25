import json
from copy import deepcopy

from django.db import models
from django.utils.translation import ugettext_lazy as _

from wagtailstreamforms.utils.general import get_slug_from_string

class FormSubmission(models.Model):
    """ Data for a form submission. """

    form_data = models.TextField(
        _('Form data'),
    )
    form = models.ForeignKey(
        'Form',
        verbose_name=_('Form'),
        on_delete=models.CASCADE
    )
    submit_time = models.DateTimeField(
        _('Submit time'),
        auto_now_add=True
    )

    def get_data(self):
        """ Returns dict with form data. """
        form_data = json.loads(self.form_data)

        # getting a copy to iterate over, without touching the original dict
        data_copy = deepcopy(form_data)
        
        form_fields = self.form.get_form_fields()
        
        # Swapping uuid fields with field labels
        for key in data_copy:
            for field in form_fields:
                if  field['id'] == key:
                    new_key = get_slug_from_string(field['value']['label'])
                    # swapping keys
                    form_data[new_key] = form_data.pop(key)
                    break

        form_data.update(
            {'submit_time': self.submit_time, }
        )
        
        return form_data

    def __str__(self):
        return self.form_data

    class Meta:
        ordering = ['-submit_time', ]
        verbose_name = _('Form submission')
