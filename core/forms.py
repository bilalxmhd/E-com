from django import forms
from core.models import *
from django_countries.widgets import CountrySelectWidget

class ProductForm(forms.ModelForm):

    class Meta:
        model= Product
        fields = '__all__'


class CheckoutForm(forms.Form):
    street_address = forms.CharField(widget=forms.TextInput(attrs={
        'class':'form-control',
        'placeholder': ' 1234 Main St' 
    }) )
    apartment_address = forms.CharField(required=False, widget=forms.TextInput(attrs={
            'class':'form-control',
            'placeholder': ' Apartment' 
        }) )
    country = CountryField(blank_label='(select country)').formfield(widget=CountrySelectWidget(attrs={
        'class':'custom-select d-block w-100'
         
    }) )
    zip = forms.CharField(widget=forms.TextInput(attrs={
        'class':'form-control',
        
    }) )    