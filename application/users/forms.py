from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import (
    CustomUser, Productor, Profesional,
    telefono_validator, dni_validator, renspa_validator
)
from domain.rules import (
    validar_matricula_ciapa, validar_telefono, validar_dni, validar_renspa,
    REGIONES_VALIDAS, ESPECIALIDADES_VALIDAS
)


class AccessibleFormMixin:
    """
    Aplica automáticamente aria-invalid="true" y aria-describedby a los campos con errores
    o texto de ayuda para cumplir con WCAG 2.1 AA (Criterio 3.3.1 y 3.3.2).
    """

    def _post_clean(self):
        super()._post_clean()
        for name, field in self.fields.items():
            widget_attrs = field.widget.attrs
            described_by = []
            if name in self.errors:
                widget_attrs['aria-invalid'] = 'true'
                described_by.append(f'error_{name}')
            if field.help_text:
                described_by.append(f'help_{name}')
            if described_by:
                widget_attrs['aria-describedby'] = ' '.join(described_by)


class RegistroProductorForm(AccessibleFormMixin, UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="Nombre",
        widget=forms.TextInput(attrs={'autocomplete': 'given-name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Apellido",
        widget=forms.TextInput(attrs={'autocomplete': 'family-name'})
    )
    email = forms.EmailField(
        required=True,
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )
    dni = forms.CharField(
        max_length=10,
        required=True,
        validators=[dni_validator],
        label="DNI del Productor",
        help_text="7 u 8 dígitos numéricos sin puntos (ej: 35123456)"
    )
    renspa = forms.CharField(
        max_length=30,
        required=True,
        validators=[renspa_validator],
        label="Número de RENSPA",
        help_text="Registro Nacional Sanitario de Productores Agropecuarios (ej: 09.001.0.00123/00)"
    )
    region = forms.ChoiceField(
        choices=[(r, r) for r in REGIONES_VALIDAS],
        required=True,
        label="Zona Geográfica de la Finca"
    )
    rubro_productivo = forms.CharField(
        max_length=150,
        required=True,
        label="Rubro Productivo Principal",
        help_text="Ej: Cultivos Andinos, Hortalizas, Tabaco, Papa, Cítricos"
    )
    telefono = forms.CharField(
        max_length=30,
        required=True,
        validators=[telefono_validator],
        label="Teléfono / WhatsApp de Contacto",
        help_text="Formato válido de 8 a 15 dígitos (ej: +54 388 4123456)",
        widget=forms.TextInput(attrs={'autocomplete': 'tel'})
    )
    direccion_finca = forms.CharField(
        max_length=255,
        required=True,
        label="Ubicación / Dirección de Finca",
        widget=forms.TextInput(attrs={'autocomplete': 'street-address'})
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email')

    def clean_dni(self):
        dni = self.cleaned_data.get('dni', '').strip()
        if not validar_dni(dni):
            raise ValidationError("El DNI debe tener entre 7 y 8 dígitos numéricos sin puntos.")
        return dni

    def clean_renspa(self):
        renspa = self.cleaned_data.get('renspa', '').strip()
        if not validar_renspa(renspa):
            raise ValidationError("Ingrese un número de RENSPA válido (6 a 22 caracteres).")
        return renspa

    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono', '').strip()
        if not validar_telefono(tel):
            raise ValidationError("Ingrese un número de teléfono válido (entre 8 y 15 dígitos).")
        return tel

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'PRODUCER'
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Productor.objects.create(
                usuario=user,
                dni=self.cleaned_data['dni'],
                renspa=self.cleaned_data['renspa'],
                region=self.cleaned_data['region'],
                rubro_productivo=self.cleaned_data['rubro_productivo'],
                telefono=self.cleaned_data['telefono'],
                direccion_finca=self.cleaned_data['direccion_finca']
            )
        return user


class RegistroProfesionalForm(AccessibleFormMixin, UserCreationForm):
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label="Nombre",
        widget=forms.TextInput(attrs={'autocomplete': 'given-name'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label="Apellido",
        widget=forms.TextInput(attrs={'autocomplete': 'family-name'})
    )
    email = forms.EmailField(
        required=True,
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={'autocomplete': 'email'})
    )
    matricula_provincial = forms.CharField(
        max_length=50,
        required=True,
        label="Número de Matrícula Provincial (CIAPAJ)",
        help_text="Requisito obligatorio para habilitación profesional en Jujuy (ej: MP-1045/J)"
    )
    especialidades = forms.MultipleChoiceField(
        choices=[(e, e) for e in ESPECIALIDADES_VALIDAS],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Especialidades Agronómicas",
        help_text="Puedes seleccionar una o múltiples especialidades"
    )
    especialidad = forms.ChoiceField(
        choices=[('', '-- Seleccionar --')] + [(e, e) for e in ESPECIALIDADES_VALIDAS],
        required=False,
        label="Especialidad Principal (Alternativo)"
    )
    especialidad_propuesta = forms.CharField(
        max_length=150,
        required=False,
        label="Proponer Nueva Especialidad (Opcional)",
        help_text="Si tu especialidad específica no figura en el listado, ingrésala aquí"
    )
    zonas_cobertura = forms.MultipleChoiceField(
        choices=[(r, r) for r in REGIONES_VALIDAS],
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Zonas Geográficas de Cobertura"
    )
    telefono = forms.CharField(
        max_length=30,
        required=True,
        validators=[telefono_validator],
        label="Teléfono de Contacto",
        help_text="Formato válido de 8 a 15 dígitos (ej: +54 388 4123456)",
        widget=forms.TextInput(attrs={'autocomplete': 'tel'})
    )
    biografia = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
        label="Resumen Profesional / Experiencia"
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email')

    def clean_matricula_provincial(self):
        mat = self.cleaned_data.get('matricula_provincial', '').strip()
        if not validar_matricula_ciapa(mat):
            raise ValidationError("El formato de matrícula provincial CIAPAJ no es válido.")
        if Profesional.objects.filter(matricula_provincial=mat).exists():
            raise ValidationError("Esta matrícula ya se encuentra registrada en el sistema.")
        return mat

    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono', '').strip()
        if not validar_telefono(tel):
            raise ValidationError("Ingrese un número de teléfono válido (entre 8 y 15 dígitos).")
        return tel

    def clean(self):
        cleaned_data = super().clean()
        seleccionadas = list(cleaned_data.get('especialidades') or [])
        unica = cleaned_data.get('especialidad')
        if unica and unica not in seleccionadas:
            seleccionadas.append(unica)
        propuesta = (cleaned_data.get('especialidad_propuesta') or '').strip()

        if not seleccionadas and not propuesta:
            self.add_error(
                'especialidades',
                "Debes seleccionar al menos una especialidad agronómica o proponer una nueva."
            )
        else:
            cleaned_data['especialidades_consolidadas'] = ", ".join(seleccionadas) if seleccionadas else propuesta
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'PROFESSIONAL'
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            zonas = ", ".join(self.cleaned_data['zonas_cobertura'])
            especialidades_str = self.cleaned_data.get('especialidades_consolidadas', 'Agronomía General')
            propuesta = (self.cleaned_data.get('especialidad_propuesta') or '').strip()
            Profesional.objects.create(
                usuario=user,
                matricula_provincial=self.cleaned_data['matricula_provincial'],
                especialidad=especialidades_str,
                especialidad_propuesta=propuesta,
                zonas_cobertura=zonas,
                telefono=self.cleaned_data['telefono'],
                biografia=self.cleaned_data.get('biografia', ''),
                estado_validacion='Pendiente'
            )
        return user


class PerfilProductorForm(AccessibleFormMixin, forms.ModelForm):
    """
    Formulario protegido de Productor:
    Nombre, apellido, correo, DNI, RENSPA, región geográfica y dirección de finca
    están protegidos institucionalmente y no pueden ser modificados de forma autónoma.
    Solo se permite actualizar rubro_productivo y telefono.
    """

    class Meta:
        model = Productor
        fields = ['rubro_productivo', 'telefono']

    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono', '').strip()
        if not validar_telefono(tel):
            raise ValidationError("Ingrese un número de teléfono válido (entre 8 y 15 dígitos).")
        return tel


class PerfilProfesionalForm(AccessibleFormMixin, forms.ModelForm):
    """
    Formulario protegido de Profesional (Mi perfil CIAPAJ):
    Nombre, apellido, correo electrónico, matrícula y especialidad están protegidos
    institucionalmente y no pueden ser modificados por el profesional.
    Solo se permite actualizar zonas de cobertura, teléfono y biografía.
    """
    zonas = forms.MultipleChoiceField(
        choices=[(r, r) for r in REGIONES_VALIDAS],
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Zonas de Cobertura"
    )

    class Meta:
        model = Profesional
        fields = ['telefono', 'biografia']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            zonas_actuales = [z.strip() for z in self.instance.zonas_cobertura.split(',') if z.strip()]
            self.fields['zonas'].initial = zonas_actuales

    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono', '').strip()
        if not validar_telefono(tel):
            raise ValidationError("Ingrese un número de teléfono válido (entre 8 y 15 dígitos).")
        return tel

    def save(self, commit=True):
        profesional = super().save(commit=False)
        profesional.zonas_cobertura = ", ".join(self.cleaned_data['zonas'])
        if commit:
            profesional.save(update_fields=['zonas_cobertura', 'telefono', 'biografia'])
        return profesional
