from django import forms
from django.forms import modelform_factory
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import OperationalError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from .audit import EDITABLE, StaleRecord, correct_record
from .models import RecordAudit


class CorrectionForm(forms.ModelForm):
    revision = forms.IntegerField(min_value=0, widget=forms.HiddenInput)
    reason = forms.CharField(max_length=1000, widget=forms.Textarea(attrs={'rows': 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('value', 'unit', 'reference_range', 'notes', 'laboratory_name', 'report_number',
                     'specimen', 'collection_time_text', 'received_time_text'):
            if name in self.fields:
                self.fields[name].strip = False

    def clean_full_name(self):
        name = self.cleaned_data['full_name'].strip()
        if not name:
            raise forms.ValidationError('Enter a full name.')
        return name

    def clean_value(self):
        value = self.cleaned_data['value']
        if not value.strip():
            raise forms.ValidationError('Enter the reported value.')
        return value


def correction_view(model, view_permissions):
    label = model._meta.label_lower
    fields = EDITABLE[label]
    form_class = modelform_factory(model, form=CorrectionForm, fields=fields,
        widgets={name: forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'})
                 for name in ('date_of_birth', 'report_date', 'test_date', 'height_measured_on',
                              'weight_measured_on', 'medications_as_of', 'conditions_as_of') if name in fields})

    @login_required
    @permission_required(view_permissions, raise_exception=True)
    @require_http_methods(['GET', 'POST'])
    def view(request, pk, patient_pk=None):
        filters = {'pk': pk}
        if patient_pk is not None:
            filters['patient_id'] = patient_pk
        record = get_object_or_404(model, **filters)
        can_change = request.user.has_perm(f'{model._meta.app_label}.change_{model._meta.model_name}')
        if request.method == 'POST' and not can_change:
            raise PermissionDenied
        form = form_class(request.POST if request.method == 'POST' else None,
                          instance=record, initial={'revision': record.revision})
        status = 200
        if request.method == 'POST' and form.is_valid():
            try:
                correct_record(model, record.pk, form.cleaned_data['revision'],
                               {name: form.cleaned_data[name] for name in fields},
                               form.cleaned_data['reason'], request.user)
            except StaleRecord as exc:
                form.add_error(None, str(exc))
                status = 409
            except ValidationError as exc:
                form.add_error(None, '; '.join(exc.messages))
            except OperationalError:
                form.add_error(None, 'Database busy or unavailable. Nothing confirmed; reload before retrying.')
                status = 503
            else:
                return redirect(request.path)
        # ModelForm validation mutates its instance; never display it as persisted data.
        record.refresh_from_db()
        history = Paginator(RecordAudit.objects.filter(
            record_type=label, record_id=record.pk), 25).get_page(request.GET.get('page'))
        return render(request, 'core/record_correction.html', {
            'record': record, 'form': form, 'can_change': can_change,
            'history': history, 'record_label': model._meta.verbose_name,
            'patient_id': record.pk if label == 'patients.patient' else record.patient_id,
        }, status=status)
    return view
