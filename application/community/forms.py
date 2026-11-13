from django import forms
from .models import PostComunidad, RespuestaComunidad


class PostComunidadForm(forms.ModelForm):
    class Meta:
        model = PostComunidad
        fields = ['titulo', 'contenido']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'placeholder': '¿Qué problema, consulta o idea deseas compartir con la comunidad?',
                'class': 'w-full'
            }),
            'contenido': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Explica los detalles de tu consulta técnica, manejo de cultivo, etc...',
                'class': 'w-full'
            }),
        }


class RespuestaComunidadForm(forms.ModelForm):
    class Meta:
        model = RespuestaComunidad
        fields = ['contenido']
        widgets = {
            'contenido': forms.TextInput(attrs={
                'placeholder': 'Escribe una respuesta o aporte técnico...',
                'class': 'w-full'
            }),
        }
