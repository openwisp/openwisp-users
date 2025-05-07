"use strict";
{
  const $ = django.jQuery;

  $.fn.djangoAdminSelect2 = function () {
    $.each(this, function (i, element) {
      $(element).select2({
        ajax: {
          data: (params) => {
            console.log("params", element.dataset);
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
