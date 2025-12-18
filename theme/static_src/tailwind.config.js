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

        // Hugo stats file (tracks all class usage) - Tailwind automatically extracts classes from JSON
        '../../hugo_output/**/hugo_stats.json',
    ],

    safelist: [
        // Safelist all bg-opacity variants for user-entered CSS classes
        {pattern: /^bg-opacity-/},
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
