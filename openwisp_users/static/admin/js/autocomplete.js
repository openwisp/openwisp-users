// Custom override of Django's autocomplete.js to add the "is_filter" parameter
// to AJAX requests. This parameter enables the backend autocomplete view to
// determine if the request is for filtering, allowing it to include the shared
// option when appropriate (e.g., for filtering shared objects in the admin).

"use strict";
{
  const $ = django.jQuery;

  $.fn.djangoAdminSelect2 = function () {
    $.each(this, function (i, element) {
      $(element).select2({
        ajax: {
          data: (params) => {
            return {
              term: params.term,
              page: params.page,
              app_label: element.dataset.appLabel,
              model_name: element.dataset.modelName,
              field_name: element.dataset.fieldName,
              is_filter: element.dataset.isFilter,
            };
          },
        },
      });
    });
    return this;
  };

  $(function () {
    // Initialize all autocomplete widgets except the one in the template
    // form used when a new formset is added.
    $(".admin-autocomplete").not("[name*=__prefix__]").djangoAdminSelect2();
  });

  document.addEventListener("formset:added", (event) => {
    $(event.target).find(".admin-autocomplete").djangoAdminSelect2();
  });
}
