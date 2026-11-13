from django import forms
from .models import TicketAsistencia, MensajeTicket


class CrearTicketForm(forms.ModelForm):
    class Meta:
        model = TicketAsistencia
        fields = ['titulo', 'descripcion']
        widgets = {
            'titulo': forms.TextInput(attrs={'placeholder': 'Ej: Presencia de plagas en cultivo de maíz', 'class': 'w-full'}),
            'descripcion': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe los síntomas observados, tiempo de afectación y zona exacta de la finca...', 'class': 'w-full'}),
        }


class MensajeChatForm(forms.ModelForm):
    class Meta:
        model = MensajeTicket
        fields = ['contenido']
        widgets = {
            'contenido': forms.TextInput(attrs={'placeholder': 'Escribe una consulta técnica...', 'class': 'w-full', 'autocomplete': 'off'}),
        }
