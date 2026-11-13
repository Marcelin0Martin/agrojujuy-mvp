from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View
from django.contrib import messages

from .models import PostComunidad, RespuestaComunidad
from .forms import PostComunidadForm, RespuestaComunidadForm
from application.use_cases import PublicarEnComunidadUseCase, ResponderPostComunidadUseCase
from infrastructure.adapters.repositories import DjangoComunidadRepository


class MuroComunidadView(LoginRequiredMixin, View):
    template_name = 'community/foro.html'

    def get(self, request):
        posts = PostComunidad.objects.all().prefetch_related('respuestas', 'respuestas__autor').order_by('-fecha_creacion')
        post_form = PostComunidadForm()
        respuesta_form = RespuestaComunidadForm()
        return render(request, self.template_name, {
            'posts': posts,
            'post_form': post_form,
            'respuesta_form': respuesta_form,
        })

    def post(self, request):
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
