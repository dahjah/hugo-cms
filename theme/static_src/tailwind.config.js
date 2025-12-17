/**
 * Tailwind CSS configuration for Hugo CMS
 */

module.exports = {
    content: [
        // Theme app templates
        '../templates/**/*.html',

        // Hugo app templates
        '../../hugo/templates/**/*.html',

        // Hugo generated site templates (most important for production CSS)
        '../../hugo_output/**/layouts/**/*.html',
        '../../hugo_output/**/content/**/*.md',
    ],
    safelist: [
        // DaisyUI alert variants
        'alert',
        'alert-info',
        'alert-success',
        'alert-warning',
        'alert-error',
        'alert-dash',
        'alert-soft',
        'alert-vertical',
        'alert-horizontal',

        // DaisyUI button variants
        'btn',
        'btn-primary',
        'btn-secondary',
        'btn-accent',
        'btn-info',
        'btn-success',
        'btn-warning',
        'btn-error',
        'btn-ghost',
        'btn-link',
        'btn-outline',
        'btn-active',
        'btn-disabled',
        'btn-sm',
        'btn-md',
        'btn-lg',
        'btn-xs',
        'btn-wide',
        'btn-block',
        'btn-circle',
        'btn-square',

        // DaisyUI collapse variants
        'collapse',
        'collapse-arrow',
        'collapse-plus',
        'collapse-open',
        'collapse-close',

        // DaisyUI badge variants
        'badge',
        'badge-primary',
        'badge-secondary',
        'badge-accent',
        'badge-info',
        'badge-success',
        'badge-warning',
        'badge-error',
        'badge-ghost',
        'badge-outline',
        'badge-lg',
        'badge-md',
        'badge-sm',
        'badge-xs',

        // DaisyUI card variants
        'card',
        'card-title',
        'card-body',
        'card-actions',
        'card-bordered',
        'card-compact',
        'card-normal',
        'card-side',

        // DaisyUI steps variants
        'steps',
        'steps-vertical',
        'steps-horizontal',
        'step',
        'step-primary',
        'step-secondary',
        'step-accent',
        'step-info',
        'step-success',
        'step-warning',
        'step-error',

        // DaisyUI menu variants
        'menu',
        'menu-title',
        'menu-dropdown',
        'menu-dropdown-show',
        'menu-sm',
        'menu-md',
        'menu-lg',
        'menu-xs',
        'menu-horizontal',
        'menu-vertical',

        // DaisyUI navbar variants
        'navbar',
        'navbar-start',
        'navbar-center',
        'navbar-end',

        // DaisyUI modal variants
        'modal',
        'modal-box',
        'modal-action',
        'modal-backdrop',
        'modal-open',
        'modal-top',
        'modal-middle',
        'modal-bottom',

        // DaisyUI input variants
        'input',
        'input-bordered',
        'input-ghost',
        'input-primary',
        'input-secondary',
        'input-accent',
        'input-info',
        'input-success',
        'input-warning',
        'input-error',
        'input-sm',
        'input-md',
        'input-lg',

        // DaisyUI join variants
        'join',
        'join-item',
        'join-horizontal',
        'join-vertical',
    ],



    theme: {
        extend: {},
    },
    plugins: [
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/aspect-ratio'),
        require('daisyui'),
    ],
    daisyui: {
        themes: ["light", "dark", "cupcake", "bumblebee", "emerald", "corporate", "synthwave", "retro", "cyberpunk", "valentine", "halloween", "garden", "forest", "aqua", "lofi", "pastel", "fantasy", "wireframe", "black", "luxury", "dracula", "cmyk", "autumn", "business", "acid", "lemonade", "night", "coffee", "winter"],  // All built-in themes
        base: true,
        styled: true,
        utils: true,
    },
}
