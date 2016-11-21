// project/client/static/main.js

$(document).ready(function() {
  console.log('Sanity Check!');

  $(".button-collapse").sideNav();

  $('.hvr-bounce-to-right').hide();

  $('#test').click(function(e) {
    $('.welcome h1').addClass('top');
    $('.welcome span').addClass('top');
    $('#top').addClass('header-top');
    e.stopPropagation();
    e.preventDefault();
  });

  $('#search').click(function(e) {
    $('.hvr-bounce-to-right').show();
    e.stopPropagation();
    e.preventDefault();
  })
});
