from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from .models import Product, Supplier, ProductSupplier, OrderItem
from django.contrib.auth.models import User


from django import forms
from .models import Product, Stock

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['product_name', 'description', 'suppliers', 'image','category']



class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name', 'email']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['product', 'price', 'expiring_date']



class SupplierForm(forms.ModelForm):
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'w-full px-4 py-2 rounded border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'
        })
    )

    class Meta:
        model = Supplier
        fields = ['supplier_name', 'supplier_location', 'email', 'contact_number', 'products']  # ✅ Added contact_number
        widgets = {
            'supplier_name': forms.TextInput(attrs={'class': 'form-input'}),
            'supplier_location': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-input'}),  # ✅ Added widget
        }




class ProductSupplierForm(forms.ModelForm):
    class Meta:
        model = ProductSupplier
        fields = ['product', 'quantity_ordered']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'quantity_ordered': forms.NumberInput(attrs={'class': 'form-input'}),
        }

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity']  # Fields to be shown in the form

    product = forms.ModelChoiceField(queryset=Product.objects.all(), empty_label="Select Product")
    quantity = forms.IntegerField(min_value=1, required=True, widget=forms.NumberInput(attrs={'class': 'form-input'}))

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')

        if product and quantity:
            # You can add validation here to check stock or other conditions
            pass

        return cleaned_data