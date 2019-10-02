from django import forms


class SubmitForm(forms.Form):
	task = forms.ChoiceField(choices=[('lowrate', 'lowrate'), ('pframe', 'pframe')])
	phase = forms.ChoiceField(choices=[('valid', 'validation'), ('test', 'test')])
	files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
