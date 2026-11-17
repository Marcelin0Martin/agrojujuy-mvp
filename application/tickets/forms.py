from django import forms
from .models import TicketAsistencia, MensajeTicket
from domain.rules import ESPECIALIDADES_VALIDAS
from application.users.forms import AccessibleFormMixin


class CrearTicketForm(AccessibleFormMixin, forms.ModelForm):
    class Meta:
        model = TicketAsistencia
        fields = ['titulo', 'descripcion']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'placeholder': 'Ej: Presencia de plagas en cultivo de maíz',
                'class': 'form-control',
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe los síntomas observados, tiempo de afectación y zona exacta de la finca...',
                'class': 'form-control',
            }),
        }


class CrearSolicitudAbiertaForm(AccessibleFormMixin, forms.ModelForm):
    especialidad_requerida = forms.ChoiceField(
        choices=[('', 'Cualquier Especialidad Agronómica')] + [(e, e) for e in ESPECIALIDADES_VALIDAS],
        required=False,
        label="Especialidad Sugerida",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = TicketAsistencia
        fields = ['titulo', 'especialidad_requerida', 'descripcion']
        widgets = {
            'titulo': forms.TextInput(attrs={
                'placeholder': 'Ej: Urgencia por helada tardía o diagnóstico de riego',
                'class': 'form-control',
            }),
            'descripcion': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe el problema para que cualquier ingeniero disponible de la red CIAPAJ pueda tomar el caso...',
                'class': 'form-control',
            }),
        }


class FinalizarTicketForm(AccessibleFormMixin, forms.Form):
    descripcion_finalizacion = forms.CharField(
        label="Informe / Descripción de Finalización del Trabajo",
        required=True,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Detalla las labores realizadas, diagnóstico final y recomendaciones entregadas al productor...',
            'class': 'form-control',
        })
    )


class MensajeChatForm(AccessibleFormMixin, forms.ModelForm):
    class Meta:
        model = MensajeTicket
        fields = ['contenido']
        widgets = {
            'contenido': forms.TextInput(attrs={
                'placeholder': 'Escribe una consulta o respuesta técnica...',
                'class': 'form-control',
                'autocomplete': 'off',
            }),
        }
