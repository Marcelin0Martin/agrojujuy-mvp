from django import forms
from .models import PostComunidad, RespuestaComunidad
from application.users.forms import AccessibleFormMixin


class PostComunidadForm(AccessibleFormMixin, forms.ModelForm):
    class Meta:
        model = PostComunidad
        fields = ['titulo', 'contenido']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'placeholder': '¿Qué problema, consulta o idea deseas compartir con la comunidad?',
                'class': 'form-control w-full'
            }),
            'contenido': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Explica los detalles de tu consulta técnica, manejo de cultivo, síntomas o sugerencias...',
                'class': 'form-control w-full'
            }),
        }


class RespuestaComunidadForm(AccessibleFormMixin, forms.ModelForm):
    class Meta:
        model = RespuestaComunidad
        fields = ['contenido']
        widgets = {
            'contenido': forms.TextInput(attrs={
                'placeholder': 'Escribe una respuesta o aporte técnico...',
                'class': 'form-control w-full'
            }),
        }
