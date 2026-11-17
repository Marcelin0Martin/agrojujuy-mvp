from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib import messages

from .models import PostComunidad
from .forms import PostComunidadForm, RespuestaComunidadForm
from application.use_cases import PublicarEnComunidadUseCase, ResponderPostComunidadUseCase
from infrastructure.adapters.repositories import DjangoComunidadRepository


class MuroComunidadView(View):
    """
    Foro / Muro Comunitario de AgroJujuy:
    - Accesible para lectura pública sin necesidad de iniciar sesión.
    - Incluye barra de búsqueda por temas o palabras clave (?q=...).
    - Muestra resumen breve por publicación (con despliegue bajo demanda) y paginación.
    """
    template_name = 'community/foro.html'
    PER_PAGE = 6

    def get(self, request):
        query = request.GET.get('q', '').strip()
        page_number = request.GET.get('page', 1)

        qs = PostComunidad.objects.select_related('autor').prefetch_related(
            'respuestas', 'respuestas__autor'
        ).order_by('-fecha_creacion')

        if query:
            qs = qs.filter(
                Q(titulo__icontains=query) |
                Q(contenido__icontains=query) |
                Q(autor__first_name__icontains=query) |
                Q(autor__last_name__icontains=query)
            )

        destacados = list(qs[:4])
        paginator = Paginator(qs, self.PER_PAGE)
        page_obj = paginator.get_page(page_number)

        post_form = PostComunidadForm()
        respuesta_form = RespuestaComunidadForm()
        return render(request, self.template_name, {
            'posts': page_obj.object_list,
            'page_obj': page_obj,
            'total_posts': paginator.count,
            'destacados': destacados,
            'query': query,
            'post_form': post_form,
            'respuesta_form': respuesta_form,
        })

    def post(self, request):
        if not request.user.is_authenticated:
            messages.info(request, "Debes iniciar sesión para publicar o responder en el foro comunitario.")
            return redirect('login')

        action = request.POST.get('action')
        repo = DjangoComunidadRepository()

        if action == 'crear_post':
            form = PostComunidadForm(request.POST)
            if form.is_valid():
                use_case = PublicarEnComunidadUseCase(repo)
                res = use_case.ejecutar(
                    autor_id=request.user.id,
                    titulo=form.cleaned_data['titulo'],
                    contenido=form.cleaned_data['contenido']
                )
                if res.exito:
                    messages.success(request, "Publicación compartida con la comunidad agraria.")
                else:
                    messages.error(request, res.mensaje)

        elif action == 'responder_post':
            post_id = request.POST.get('post_id')
            form = RespuestaComunidadForm(request.POST)
            if form.is_valid() and post_id:
                use_case = ResponderPostComunidadUseCase(repo)
                res = use_case.ejecutar(
                    post_id=int(post_id),
                    autor_id=request.user.id,
                    contenido=form.cleaned_data['contenido']
                )
                if res.exito:
                    messages.success(request, "Respuesta agregada al hilo de discusión.")
                else:
                    messages.error(request, res.mensaje)

        return redirect('foro_comunidad')
