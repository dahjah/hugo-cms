module.exports = {
    content: [
        '../templates/**/*.html',
        '../../hugo/templates/**/*.html',
        '../../hugo_output/**/layouts/**/*.html',
        '../../hugo_output/**/content/**/*.md',
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
        themes: ["lemonade"],
        base: true,
        styled: true,
        utils: true,
    },
}
