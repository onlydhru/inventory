module.exports = {
  content: [
      './templates/**/*.html',
  ],
  theme: {

    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      'white': '#ffffff',
      'purple': '#3f3cbb',
      'midnight': '#121063',
      'metal': '#565584',
      'tahiti': '#3ab7bf',
      'silver': '#ecebff',
      'bubble-gum': '#ff77e9',
      'bermuda': '#78dcca',
      'darkteal': '#04445F',
      'darkyellow': '#ED9B09',
      'red': '#C20006',
      'green': '#009700',
      'bg-green': '#BEE0CF',
      'bg-red': '#E7C7CA',
      'bg-gray': '#F8E9C5',
    },
    fontFamily: {
      fredoka: ['Fredoka', 'sans-serif'], 
      inter: ['Inter', 'san-serif'], 
    extend: {
    },
  },
  plugins: [ require('flowbite/plugin'),

  ],
}

}
