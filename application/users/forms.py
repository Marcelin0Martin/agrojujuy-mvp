from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, Productor, Profesional
from domain.rules import validar_matricula_ciapa, REGIONES_VALIDAS, ESPECIALIDADES_VALIDAS


class RegistroProductorForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Nombre")
    last_name = forms.CharField(max_length=30, required=True, label="Apellido")
    email = forms.EmailField(required=True, label="Correo Electrónico")
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
    telefono = forms.CharField(max_length=30, required=True, label="Teléfono / WhatsApp de Contacto")
    direccion_finca = forms.CharField(max_length=255, required=False, label="Ubicación / Finca")

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email')

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
                region=self.cleaned_data['region'],
                rubro_productivo=self.cleaned_data['rubro_productivo'],
                telefono=self.cleaned_data['telefono'],
                direccion_finca=self.cleaned_data.get('direccion_finca', '')
            )
        return user


class RegistroProfesionalForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label="Nombre")
    last_name = forms.CharField(max_length=30, required=True, label="Apellido")
    email = forms.EmailField(required=True, label="Correo Electrónico")
    matricula_provincial = forms.CharField(
        max_length=50,
        required=True,
        label="Número de Matrícula Provincial (CIAPA)",
        help_text="Requisito obligatorio para habilitación profesional en Jujuy"
    )
    especialidad = forms.ChoiceField(
        choices=[(e, e) for e in ESPECIALIDADES_VALIDAS],
        required=True,
        label="Especialidad Principal"
    )
    zonas_cobertura = forms.MultipleChoiceField(
        choices=[(r, r) for r in REGIONES_VALIDAS],
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Zonas Geográficas de Cobertura"
    )
    telefono = forms.CharField(max_length=30, required=True, label="Teléfono de Contacto")
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
            raise ValidationError("El formato de matrícula provincial CIAPA no es válido.")
        if Profesional.objects.filter(matricula_provincial=mat).exists():
            raise ValidationError("Esta matrícula ya se encuentra registrada en el sistema.")
        return mat

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'PROFESSIONAL'
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            zonas = ", ".join(self.cleaned_data['zonas_cobertura'])
            Profesional.objects.create(
                usuario=user,
                matricula_provincial=self.cleaned_data['matricula_provincial'],
                especialidad=self.cleaned_data['especialidad'],
                zonas_cobertura=zonas,
                telefono=self.cleaned_data['telefono'],
                biografia=self.cleaned_data.get('biografia', ''),
                estado_validacion='Pendiente'  # Onboarding bloqueado hasta aprobación institucional
            )
        return user


class PerfilProductorForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label="Nombre")
    last_name = forms.CharField(max_length=30, label="Apellido")
    email = forms.EmailField(label="Correo Electrónico")

    class Meta:
        model = Productor
        fields = ['region', 'rubro_productivo', 'telefono', 'direccion_finca']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.usuario:
            self.fields['first_name'].initial = self.instance.usuario.first_name
            self.fields['last_name'].initial = self.instance.usuario.last_name
            self.fields['email'].initial = self.instance.usuario.email

    def save(self, commit=True):
        productor = super().save(commit=False)
        if commit:
            productor.save()
            u = productor.usuario
            u.first_name = self.cleaned_data['first_name']
            u.last_name = self.cleaned_data['last_name']
            u.email = self.cleaned_data['email']
            u.save()
        return productor


class PerfilProfesionalForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, label="Nombre")
    last_name = forms.CharField(max_length=30, label="Apellido")
    email = forms.EmailField(label="Correo Electrónico")

    zonas = forms.MultipleChoiceField(
        choices=[(r, r) for r in REGIONES_VALIDAS],
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Zonas de Cobertura"
    )

    class Meta:
        model = Profesional
        fields = ['especialidad', 'telefono', 'biografia']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.usuario:
            self.fields['first_name'].initial = self.instance.usuario.first_name
            self.fields['last_name'].initial = self.instance.usuario.last_name
            self.fields['email'].initial = self.instance.usuario.email
            zonas_actuales = [z.strip() for z in self.instance.zonas_cobertura.split(',') if z.strip()]
            self.fields['zonas'].initial = zonas_actuales

    def save(self, commit=True):
        profesional = super().save(commit=False)
        profesional.zonas_cobertura = ", ".join(self.cleaned_data['zonas'])
        if commit:
            profesional.save()
            u = profesional.usuario
            u.first_name = self.cleaned_data['first_name']
            u.last_name = self.cleaned_data['last_name']
            u.email = self.cleaned_data['email']
            u.save()
        return profesional
