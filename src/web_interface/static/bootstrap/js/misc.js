(function ($) {
  'use strict';
  $(function () {
    var body = $('body');
    var contentWrapper = $('.content-wrapper');
    var scroller = $('.container-scroller');
    var footer = $('.footer');
    var sidebar = $('#sidebar');

    //Change sidebar and content-wrapper height

    $('[data-toggle="minimize"]').on("click", function () {
      if ((body.hasClass('sidebar-toggle-display')) || (body.hasClass('sidebar-absolute'))) {
        body.toggleClass('sidebar-hidden');
      } else {
        body.toggleClass('sidebar-icon-only');
      }
    });

    //checkbox and radios
    $(".form-check label,.form-radio label").append('<i class="input-helper"></i>');
  });

  $('[data-toggle="tooltip"]').tooltip();

  var height = $(window).innerHeight() - $(".navbar").innerHeight() - $(".access-header-top").innerHeight() - $(".footer").innerHeight() - 16;
  if ( $(window).innerWidth() > ( 1200 - 16 ) ) {
    $(".access-body").css('height', height)
  } else {
    $(".access-body").css('height', 'unset')
  }

  $(window).resize(function() {
    height = $(window).innerHeight() - $(".navbar").innerHeight() - $(".access-header-top").innerHeight() - $(".footer").innerHeight() - 16
    if ( $(window).innerWidth() > ( 1200 - 16 ) ) {
      $(".access-body").css('height', height)
    } else {
      $(".access-body").css('height', 'unset')
    }
  })

  $(".sidebar .sidebar-inner > .nav > .nav-item").not(".brand-logo").attr('toggle-status', 'closed');
  $(".sidebar .sidebar-inner > .nav > .nav-item").on('click', function () {
    $(".sidebar .sidebar-inner > .nav > .nav-item").removeClass("active");
    $(this).addClass("active");
    $(".sidebar .sidebar-inner > .nav > .nav-item").find(".submenu").removeClass("open");
    $(".sidebar .sidebar-inner > .nav > .nav-item").not(this).attr('toggle-status', 'closed');
    var toggleStatus = $(this).attr('toggle-status');
    if (toggleStatus == 'closed') {
      $(this).find(".submenu").addClass("open");
      $(this).attr('toggle-status', 'open');
    } else {
      $(this).find(".submenu").removeClass("open");
      $(this).not(".brand-logo").attr('toggle-status', 'closed');
    }
  });
})(jQuery);
