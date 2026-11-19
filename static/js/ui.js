/**
 * AgroJujuy UI & Usability Engine
 * Iconos SVG a color (amigables e intuitivos para productores e ingenieros) + Filtros y Accesibilidad.
 * Cumple 100% con OWASP CSP (script-src 'self').
 */
(function () {
    'use strict';

    // Paleta de colores amigables por icono (Color principal + Fondo suave duotono)
    const ICON_THEMES = {
        'sprout':         { stroke: '#059669', bg: '#D1FAE5' },
        'leaf':           { stroke: '#10B981', bg: '#D1FAE5' },
        'trees':          { stroke: '#047857', bg: '#A7F3D0' },
        'tractor':        { stroke: '#D97706', bg: '#FEF3C7' },
        'sun':            { stroke: '#EA580C', bg: '#FFEDD5' },
        'mountain':       { stroke: '#92400E', bg: '#FDE68A' },
        'graduation-cap': { stroke: '#2563EB', bg: '#DBEAFE' },
        'award':          { stroke: '#7C3AED', bg: '#EDE9FE' },
        'shield-check':   { stroke: '#059669', bg: '#D1FAE5' },
        'search':         { stroke: '#0284C7', bg: '#E0F2FE' },
        'compass':        { stroke: '#0284C7', bg: '#E0F2FE' },
        'map-pin':        { stroke: '#DC2626', bg: '#FEE2E2' },
        'microscope':     { stroke: '#7C3AED', bg: '#EDE9FE' },
        'clipboard-list': { stroke: '#D97706', bg: '#FEF3C7' },
        'inbox':          { stroke: '#0284C7', bg: '#E0F2FE' },
        'megaphone':      { stroke: '#059669', bg: '#D1FAE5' },
        'message-square': { stroke: '#0284C7', bg: '#E0F2FE' },
        'messages-square':{ stroke: '#059669', bg: '#D1FAE5' },
        'user':           { stroke: '#0F766E', bg: '#CCFBF1' },
        'user-check':     { stroke: '#059669', bg: '#D1FAE5' },
        'key-round':      { stroke: '#D97706', bg: '#FEF3C7' },
        'lock':           { stroke: '#B45309', bg: '#FEF3C7' },
        'settings':       { stroke: '#475569', bg: '#F1F5F9' },
        'log-out':        { stroke: '#DC2626', bg: '#FEE2E2' },
        'check-circle':   { stroke: '#059669', bg: '#D1FAE5' },
        'clock':          { stroke: '#D97706', bg: '#FEF3C7' },
        'flag':           { stroke: '#059669', bg: '#D1FAE5' },
        'alert-circle':   { stroke: '#DC2626', bg: '#FEE2E2' },
        'info':           { stroke: '#0284C7', bg: '#E0F2FE' },
        'help-circle':    { stroke: '#0284C7', bg: '#E0F2FE' },
        'phone':          { stroke: '#059669', bg: '#D1FAE5' },
        'mail':           { stroke: '#0284C7', bg: '#E0F2FE' },
        'edit-3':         { stroke: '#D97706', bg: '#FEF3C7' },
        'send':           { stroke: '#059669', bg: '#D1FAE5' },
        'building-2':     { stroke: '#0F766E', bg: '#CCFBF1' },
        'sparkles':       { stroke: '#D97706', bg: '#FEF3C7' },
        'filter':         { stroke: '#0284C7', bg: '#E0F2FE' },
        'layers':         { stroke: '#0F766E', bg: '#CCFBF1' },
        'file-text':      { stroke: '#0284C7', bg: '#E0F2FE' },
        'arrow-left':     { stroke: 'currentColor', bg: 'transparent' },
        'arrow-right':    { stroke: 'currentColor', bg: 'transparent' },
        'x':              { stroke: 'currentColor', bg: 'transparent' },
        'menu':           { stroke: 'currentColor', bg: 'transparent' }
    };

    const LUCIDE_ICONS = {
        'sprout': '<path d="M7 20h10"/><path d="M10 20c5.5-2.5.8-6.4 3-10"/><path d="M9.5 9.4c1.1.8 1.8 2.2 2.3 3.7-2 .4-3.5.4-4.8-.3-1.2-.6-2.3-1.9-3-4.2 2.8-.5 4.4 0 5.5.8z" fill="currentColor" fill-opacity="0.22"/><path d="M14.1 6a7 7 0 0 0-1.1 4c1.9-.1 3.3-.6 4.3-1.4 1-1 1.6-2.3 1.7-4.6-2.7.1-4 1-4.9 2z" fill="currentColor" fill-opacity="0.22"/>',
        'search': '<circle cx="11" cy="11" r="8" fill="currentColor" fill-opacity="0.15"/><path d="m21 21-4.3-4.3"/>',
        'clipboard-list': '<rect width="8" height="4" x="8" y="2" rx="1" ry="1" fill="currentColor" fill-opacity="0.2"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" fill="currentColor" fill-opacity="0.12"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
        'megaphone': '<path d="m3 11 18-5v12L3 14v-3z" fill="currentColor" fill-opacity="0.2"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/>',
        'message-square': '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" fill="currentColor" fill-opacity="0.18"/>',
        'messages-square': '<path d="M14 9a2 2 0 0 1-2 2H6l-4 4V4c0-1.1.9-2 2-2h8a2 2 0 0 1 2 2z" fill="currentColor" fill-opacity="0.18"/><path d="M18 9h2a2 2 0 0 1 2 2v11l-4-4h-6a2 2 0 0 1-2-2v-1"/>',
        'user': '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4" fill="currentColor" fill-opacity="0.2"/>',
        'user-check': '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4" fill="currentColor" fill-opacity="0.2"/><polyline points="16 11 18 13 22 9"/>',
        'shield-check': '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" fill="currentColor" fill-opacity="0.18"/><path d="m9 12 2 2 4-4"/>',
        'tractor': '<path d="m10 11 11 .9c.6 0 .9.5.8 1.1l-.8 5h-1" fill="currentColor" fill-opacity="0.18"/><path d="M16 18h-5"/><path d="M18 5a1 1 0 0 0-1 1v5.573"/><path d="M3 4h9l1 7.246" fill="currentColor" fill-opacity="0.15"/><path d="M4 11V4"/><path d="M7 15h.01"/><path d="M8 10.1V4"/><circle cx="18" cy="18" r="2" fill="currentColor" fill-opacity="0.25"/><circle cx="7" cy="15" r="5" fill="currentColor" fill-opacity="0.25"/>',
        'graduation-cap': '<path d="M21.42 10.922a1 1 0 0 0-.019-1.838L12.83 5.18a2 2 0 0 0-1.66 0L2.6 9.08a1 1 0 0 0 0 1.832l8.57 3.908a2 2 0 0 0 1.66 0z" fill="currentColor" fill-opacity="0.22"/><path d="M22 10v6"/><path d="M6 12.5V16a6 3 0 0 0 12 0v-3.5"/>',
        'key-round': '<path d="M2 18v3c0 .6.4 1 1 1h4v-3h3v-3h2l1.4-1.4a6.5 6.5 0 1 0-4-4Z" fill="currentColor" fill-opacity="0.2"/><circle cx="16.5" cy="7.5" r=".5"/>',
        'map-pin': '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" fill="currentColor" fill-opacity="0.2"/><circle cx="12" cy="10" r="3"/>',
        'compass': '<circle cx="12" cy="12" r="10" fill="currentColor" fill-opacity="0.14"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76" fill="currentColor" fill-opacity="0.25"/>',
        'microscope': '<path d="M6 18h8"/><path d="M3 22h18"/><path d="M14 22a7 7 0 1 0 0-14h-1"/><path d="M9 14h2"/><path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z" fill="currentColor" fill-opacity="0.22"/><path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/>',
        'inbox': '<polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" fill="currentColor" fill-opacity="0.16"/>',
        'settings': '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" fill="currentColor" fill-opacity="0.16"/><circle cx="12" cy="12" r="3"/>',
        'log-out': '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" x2="9" y1="12" y2="12"/>',
        'check-circle': '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" fill="currentColor" fill-opacity="0.18"/><polyline points="22 4 12 14.01 9 11.01"/>',
        'clock': '<circle cx="12" cy="12" r="10" fill="currentColor" fill-opacity="0.18"/><polyline points="12 6 12 12 16 14"/>',
        'flag': '<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z" fill="currentColor" fill-opacity="0.22"/><line x1="4" x2="4" y1="22" y2="15"/>',
        'alert-circle': '<circle cx="12" cy="12" r="10" fill="currentColor" fill-opacity="0.18"/><line x1="12" x2="12" y1="8" y2="12"/><line x1="12" x2="12.01" y1="16" y2="16"/>',
        'info': '<circle cx="12" cy="12" r="10" fill="currentColor" fill-opacity="0.18"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
        'help-circle': '<circle cx="12" cy="12" r="10" fill="currentColor" fill-opacity="0.18"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
        'phone': '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" fill="currentColor" fill-opacity="0.2"/>',
        'mail': '<rect width="20" height="16" x="2" y="4" rx="2" fill="currentColor" fill-opacity="0.16"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
        'lock': '<rect width="18" height="11" x="3" y="11" rx="2" ry="2" fill="currentColor" fill-opacity="0.2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
        'edit-3': '<path d="M12 20h9"/><path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" fill="currentColor" fill-opacity="0.2"/>',
        'send': '<path d="m22 2-7 20-4-9-9-4Z" fill="currentColor" fill-opacity="0.2"/><path d="M22 2 11 13"/>',
        'arrow-left': '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
        'arrow-right': '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
        'mountain': '<path d="m8 3 4 8 5-5 5 15H2L8 3z" fill="currentColor" fill-opacity="0.22"/>',
        'sun': '<circle cx="12" cy="12" r="4" fill="currentColor" fill-opacity="0.28"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
        'trees': '<path d="M10 10v.2A3 3 0 0 1 8.9 16v0H5v0h0a3 3 0 0 1-1-5.8V10a3 3 0 0 1 6 0Z" fill="currentColor" fill-opacity="0.24"/><path d="M7 16v6"/><path d="M13 19v3"/><path d="M12 19h8.3a1 1 0 0 0 .7-1.7L18 14h.3a1 1 0 0 0 .7-1.7L16 9h.2a1 1 0 0 0 .8-1.7L13 3l-1.4 1.5"/>',
        'leaf': '<path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z" fill="currentColor" fill-opacity="0.22"/><path d="M2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12"/>',
        'building-2': '<path d="M6 22V4a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v18Z" fill="currentColor" fill-opacity="0.16"/><path d="M6 12H4a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"/><path d="M18 9h2a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2h-2"/><path d="M10 6h4"/><path d="M10 10h4"/><path d="M10 14h4"/><path d="M10 18h4"/>',
        'sparkles': '<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" fill="currentColor" fill-opacity="0.25"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/>',
        'filter': '<polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" fill="currentColor" fill-opacity="0.2"/>',
        'x': '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
        'menu': '<line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/>',
        'layers': '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z" fill="currentColor" fill-opacity="0.22"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
        'award': '<circle cx="12" cy="8" r="6" fill="currentColor" fill-opacity="0.22"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>',
        'file-text': '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z" fill="currentColor" fill-opacity="0.16"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>'
    };

    function renderLucideIcons() {
        const elements = document.querySelectorAll('[data-lucide]');
        elements.forEach(function (el) {
            const name = el.getAttribute('data-lucide');
            const paths = LUCIDE_ICONS[name];
            if (!paths) return;

            const size = parseInt(el.getAttribute('data-size') || '18', 10);
            const theme = ICON_THEMES[name] || { stroke: 'currentColor', bg: 'transparent' };
            const insideDarkOrBtn = el.closest('.btn-primary, .btn-secondary, .btn-tertiary, .global-header, footer, .badge-success, .badge-warning, .badge-danger');

            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
            svg.setAttribute('width', String(size));
            svg.setAttribute('height', String(size));
            svg.setAttribute('viewBox', '0 0 24 24');
            svg.setAttribute('fill', 'none');
            svg.setAttribute('stroke', insideDarkOrBtn ? 'currentColor' : theme.stroke);
            svg.setAttribute('stroke-width', '2.1');
            svg.setAttribute('stroke-linecap', 'round');
            svg.setAttribute('stroke-linejoin', 'round');
            svg.setAttribute('aria-hidden', 'true');
            svg.setAttribute('class', ('lucide-icon ' + (el.className || '')).trim());

            if (!insideDarkOrBtn && theme.bg !== 'transparent') {
                svg.style.color = theme.stroke;
                svg.style.backgroundColor = theme.bg;
                svg.style.padding = '3px';
                svg.style.borderRadius = '7px';
                svg.style.boxSizing = 'content-box';
            }

            svg.innerHTML = paths;
            el.replaceWith(svg);
        });
    }

    // Auto-submit confiable para filtros del buscador (sin inline JS que pueda fallar)
    function initSearchFilters() {
        const buscadorForm = document.getElementById('buscador-form');
        if (!buscadorForm) return;

        const selects = buscadorForm.querySelectorAll('select');
        selects.forEach(function (sel) {
            sel.addEventListener('change', function () {
                const regionSel = document.getElementById('id_region');
                const espSel = document.getElementById('id_especialidad');
                const mostrarInput = document.getElementById('id_mostrar_hidden');

                // Si el usuario limpia ambos selectores estando en el buscador, mantener 'mostrar=todos' para que no quede vacía la pantalla
                if (mostrarInput && regionSel && espSel) {
                    if (!regionSel.value && !espSel.value) {
                        mostrarInput.value = 'todos';
                    } else {
                        mostrarInput.value = '';
                    }
                }
                buscadorForm.submit();
            });
        });
    }

    function initFormLoadingStates() {
        const forms = document.querySelectorAll('form[data-loading-text]');
        forms.forEach(function (form) {
            form.addEventListener('submit', function () {
                const btn = form.querySelector('button[type="submit"]');
                if (btn && !btn.disabled) {
                    const loadingText = form.getAttribute('data-loading-text') || 'Procesando...';
                    btn.disabled = true;
                    btn.classList.add('btn-loading');
                    btn.innerHTML = '<span class="spinner-inline" aria-hidden="true"></span> ' + loadingText;
                }
            });
        });
    }

    function initConfirmActions() {
        const confirmForms = document.querySelectorAll('form[data-confirm]');
        confirmForms.forEach(function (form) {
            form.addEventListener('submit', function (e) {
                const msg = form.getAttribute('data-confirm');
                if (msg && !window.confirm(msg)) {
                    e.preventDefault();
                }
            });
        });
    }

    function initMobileNav() {
        const toggleBtn = document.getElementById('mobile-nav-toggle');
        const navMenu = document.getElementById('primary-nav-links');
        if (toggleBtn && navMenu) {
            toggleBtn.addEventListener('click', function () {
                const expanded = toggleBtn.getAttribute('aria-expanded') === 'true';
                toggleBtn.setAttribute('aria-expanded', String(!expanded));
                navMenu.classList.toggle('nav-open');
            });
        }
    }


    function initMapaJujuy() {
        const dataScript = document.getElementById('datos-regiones-jujuy');
        const svgMap = document.getElementById('mapa-jujuy-svg');
        if (!dataScript || !svgMap) return;

        let datosRegiones = {};
        try {
            datosRegiones = JSON.parse(dataScript.textContent);
        } catch (e) {
            return;
        }

        const paths = svgMap.querySelectorAll('path[data-region]');
        const buttons = document.querySelectorAll('[data-region-btn]');
        const tituloEl = document.getElementById('detalle-region-titulo');
        const descEl = document.getElementById('detalle-region-desc');
        const kpiProdEl = document.getElementById('kpi-productores');
        const kpiProfEl = document.getElementById('kpi-profesionales');
        const kpiTicketsEl = document.getElementById('kpi-tickets');
        const rubrosEl = document.getElementById('detalle-region-rubros');
        const btnBuscarEl = document.getElementById('btn-buscar-en-region');

        function seleccionarRegion(regionNombre) {
            const info = datosRegiones[regionNombre];
            if (!info) return;

            paths.forEach(function (p) {
                const esActiva = p.getAttribute('data-region') === regionNombre;
                p.style.opacity = esActiva ? '1' : '0.62';
                p.style.strokeWidth = esActiva ? '4.5' : '2.5';
                p.style.stroke = esActiva ? '#FDE68A' : '#FFFFFF';
            });

            buttons.forEach(function (b) {
                if (b.getAttribute('data-region-btn') === regionNombre) {
                    b.classList.add('filter-pill-active');
                } else {
                    b.classList.remove('filter-pill-active');
                }
            });

            if (tituloEl) tituloEl.textContent = 'Región ' + info.nombre;
            if (descEl) descEl.textContent = info.descripcion;
            if (kpiProdEl) kpiProdEl.textContent = info.productores;
            if (kpiProfEl) kpiProfEl.textContent = info.profesionales;
            if (kpiTicketsEl) kpiTicketsEl.textContent = info.tickets_totales;

            if (rubrosEl) {
                rubrosEl.innerHTML = '';
                if (info.top_rubros && info.top_rubros.length > 0) {
                    info.top_rubros.forEach(function (rubro) {
                        const span = document.createElement('span');
                        span.className = 'badge badge-soft';
                        span.textContent = rubro;
                        rubrosEl.appendChild(span);
                    });
                } else {
                    const span = document.createElement('span');
                    span.className = 'badge badge-soft';
                    span.textContent = 'Diversos cultivos regionales';
                    rubrosEl.appendChild(span);
                }
            }

            if (btnBuscarEl) {
                const hrefActual = btnBuscarEl.getAttribute('href') || '';
                const baseUrl = hrefActual.split('?')[0];
                if (baseUrl) {
                    btnBuscarEl.setAttribute('href', baseUrl + '?region=' + encodeURIComponent(regionNombre));
                }
                btnBuscarEl.textContent = 'Ver Ingenieros en ' + regionNombre;
            }
        }

        paths.forEach(function (p) {
            p.addEventListener('click', function () {
                seleccionarRegion(p.getAttribute('data-region'));
            });
        });

        buttons.forEach(function (b) {
            b.addEventListener('click', function () {
                seleccionarRegion(b.getAttribute('data-region-btn'));
            });
        });

        seleccionarRegion('Puna');
    }

    document.addEventListener('DOMContentLoaded', function () {
        initMapaJujuy();
        renderLucideIcons();
        initSearchFilters();
        initFormLoadingStates();
        initConfirmActions();
        initMobileNav();
    });
})();
