from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation
from django.forms import inlineformset_factory
from .apps import user_registered
from .models import AdvUser, SuperRubric, SubRubric, Bb, AdditionalImage, Comment
from captcha.fields import CaptchaField
from phonenumber_field.formfields import PhoneNumberField


class ChangeUserInfoForm(forms.ModelForm):
    email = forms.EmailField(required=True,
                             label='Адрес Электронной почты')

    class Meta:
        model = AdvUser
        fields = ('username', 'email', 'first_name', 'last_name',
                  'send_messages')


class RegisterUserForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Адрес электронной почты')
    password1 = forms.CharField(label='Пароль',
        widget=forms.PasswordInput,
        help_text=password_validation.password_validators_help_text_html())
    password2 = forms.CharField(label='Пароль повторно',
        widget=forms.PasswordInput,
        help_text='Введите тот же самый пароль еще раз для проверки')
    
    def clean_password1(self):
        password1 = self.cleaned_data['password1']
        if password1:
            password_validation.validate_password(password1)
        return password1

    def clean(self):
        super().clean()
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']
        if password1 and password2 and password1 != password2:
            errors = {
                'password2': ValidationError('Введенные пароли не совпадают',
                    code='password_mismath'
                    )
                
                }
            raise ValidationError(errors)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = True
        user.is_activated = True
        if commit:
            user.save()
        user_registered.send(RegisterUserForm, instance=user)
        return user

    class Meta:
        model = AdvUser
        fields = ('username', 'email', 'password1', 'password2', 'first_name',
            'last_name', 'send_messages')


class SubRubricForm(forms.ModelForm):
    super_rubric = forms.ModelChoiceField(
                    queryset=SuperRubric.objects.all(), empty_label=None,
                    required=True, label='Надрубрика')
    class Meta:
        model = SubRubric
        fields = '__all__'


class SearchForm(forms.Form):
    rubric = forms.ModelChoiceField(queryset=SubRubric.objects.all(), empty_label=None, label='')
    keyword = forms.CharField(required=False, max_length=20, label='')
    class Meta:
        widgets = {'keyword': forms.TextInput(attrs={'class': 'form-control'}),
                   'rubric': forms.Select(attrs={'class': 'form-control'})
        }

class BbForm(forms.ModelForm):
    class Meta:
        model = Bb
        fields = ('rubric', 'title', 'content', 'author',
                  'price', 'contacts', 'image', 'phone_number')
        widgets = {'author': forms.HiddenInput}

AIFormSet = inlineformset_factory(Bb, AdditionalImage, fields = ('image',), extra = 3)


class UserCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        exclude = ('is_active',)
        widgets = {'bb':forms.HiddenInput}

class GuestCommentForm(forms.ModelForm):
    captcha = CaptchaField(label = 'Введите текст с каритнки',
                           error_messages = {'invalid': 'Неправильный текст'})
    class Meta:
        model = Comment
        exclude = ('is_active',)
        widgets = {'bb':forms.HiddenInput}