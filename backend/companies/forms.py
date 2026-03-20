from __future__ import annotations

from django import forms


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_file_clean = super().clean

        if isinstance(data, (list, tuple)):
            result = [single_file_clean(item, initial) for item in data]
            if not result:
                raise forms.ValidationError('Нужно выбрать хотя бы один файл.')
            return result

        if data is None:
            raise forms.ValidationError('Нужно выбрать хотя бы один файл.')

        return [single_file_clean(data, initial)]


class AdminOpenDataImportForm(forms.Form):
    dataset_2 = MultipleFileField(
        label='Файлы первого типа',
        help_text='Можно выбрать один или несколько файлов.',
    )
    dataset_3 = MultipleFileField(
        label='Файлы второго типа',
        help_text='Можно выбрать один или несколько файлов.',
    )
    clear = forms.BooleanField(
        label='Очистить таблицы перед импортом',
        required=False,
        initial=False,
    )

    def clean(self):
        cleaned_data = super().clean()

        files_2 = cleaned_data.get('dataset_2') or []
        files_3 = cleaned_data.get('dataset_3') or []

        if not files_2:
            self.add_error('dataset_2', 'Нужно выбрать хотя бы один файл первого типа.')

        if not files_3:
            self.add_error('dataset_3', 'Нужно выбрать хотя бы один файл второго типа.')

        return cleaned_data