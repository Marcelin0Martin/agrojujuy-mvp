def global_roles_context(request):
    if not request.user.is_authenticated:
        return {
            'is_admin_user': False,
            'effective_role': 'ANONYMOUS',
            'simulated_role': None,
        }

    is_admin = (request.user.role == 'ADMIN' or request.user.is_staff or request.user.is_superuser)
    simulated_role = request.session.get('simulated_role')
    effective_role = simulated_role if (is_admin and simulated_role) else request.user.role

    return {
        'is_admin_user': is_admin,
        'effective_role': effective_role,
        'simulated_role': simulated_role,
        'user_productor': getattr(request.user, 'perfil_productor', None),
        'user_profesional': getattr(request.user, 'perfil_profesional', None),
    }
