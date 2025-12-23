/**
 * Tailwind CSS configuration for Hugo CMS
 */

module.exports = {
    content: [
        // Theme app templates
        '../templates/**/*.html',

        // Hugo app templates
        '../../hugo/templates/**/*.html',
        '../../hugo/templates/**/*.hbs',

        // Hugo generated HTML (MOST IMPORTANT - this is what actually gets served!)
        // This is where all the classes from hugo_stats.json are rendered into actual HTML
        '../../hugo_output/*/public/**/*.html',
        '../../hugo_output/strippin-v2/public/test_scan.html',

        // Keep layouts and content as backup
        '../../hugo_output/**/layouts/**/*.html',
        '../../hugo_output/**/content/**/*.md',
    ],

    darkMode: 'class',

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
