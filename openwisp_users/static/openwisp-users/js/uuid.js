django.jQuery(function ($) {
  "use strict";
  var container = $('.field-uuid .readonly'),
      value = container.text();
  container.html('<input readonly id="id_id" type="text" class="vTextField readonly" value="' + value + '">');
  var id = $('#id_id');
  id.click(function () {
    $(this).select();
  });
});
