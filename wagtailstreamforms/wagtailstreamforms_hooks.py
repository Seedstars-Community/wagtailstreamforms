import json

from django.template.defaultfilters import pluralize

from wagtailstreamforms.hooks import register
from wagtailstreamforms.models import FormSubmissionFile
from wagtailstreamforms.serializers import FormSubmissionSerializer
from wagtailstreamforms.utils.general import get_slug_from_string


@register('process_form_submission')
def save_form_submission_data(instance, form):
    """ saves the form submission data """

    # copy the cleaned_data so we dont mess with the original
    submission_data = form.cleaned_data.copy()

    # getting another copy to iterate over without touching the original
    data_copy = deepcopy(submission_data)
    
    form_fields = instance.get_form_fields()

    # Swapping field labels fields with uuid fields
    for key in data_copy:
        for field in form_fields:
            label = get_slug_from_string(field['value']['label']) 
            if  label == key:
                new_key = field['id']
                submission_data[new_key] = submission_data.pop(key)
                break

    # change the submission data to a count of the files
    for field in form.files.keys():
        count = len(form.files.getlist(field))
        submission_data[field] = '{} file{}'.format(count, pluralize(count))

    # save the submission data
    submission = instance.get_submission_class().objects.create(
        form_data=json.dumps(submission_data, cls=FormSubmissionSerializer),
        form=instance
    )

    # save the form files
    for field in form.files:
        for file in form.files.getlist(field):
            FormSubmissionFile.objects.create(
                submission=submission,
                field=field,
                file=file
            )
