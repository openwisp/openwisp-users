(function ($) {
  "use strict";
  $(document).ready(function () {
    // The select2 library requires data in a specific format
    // https://select2.org/data-sources/formats.
    // select2 does not render option with blank "id" (i.e. id='').
    // Therefore, the backend uses "null" id for Systemwide shared
    // objects. This causes issues on submitting forms because
    // Django expects an empty string (for None) or a UUID string.
    // Hence, we need to update the value of the selected option before
    // submission of the form.
    //
    // Find the organization fields at submit time so dynamically added
    // inlines are included too.
    $("form").on("submit", function () {
      $(this)
        .find("select[data-field-name='organization'] option:selected")
        .each(function () {
          var selected = $(this);
          if (selected.val() === "null") {
            selected.val("");
          }
        });
    });

    // Auto-selection only applies to the single top-level organization field
    // when it is still empty (e.g. add forms or systemwide-shared objects). Skip
    // inline organization selects and forms where an organization is already set.
    var orgField = $("select#id_organization");
    if (!orgField.length || orgField.val()) {
      return;
    }

    var pathName = window.location.pathname.split("/");
    // If the field is rendered empty on a change form, then the
    // object is shared systemwide (no organization).
    if (pathName[pathName.length - 2] == "change") {
      orgField.val("null");
      orgField.trigger("change");
      return;
    }

    // If only one organization option is available, then select that
    // organization automatically.
    $.ajax({
      url: orgField.data("ajax--url"),
      data: {
        app_label: orgField.data("app-label"),
        model_name: orgField.data("model-name"),
        field_name: orgField.data("field-name"),
      },
      success: function (data) {
        if (data.results.length === 1) {
          var option = new Option(data.results[0].text, data.results[0].id, true, true);
          orgField.append(option).trigger("change");
          // manually trigger the `select2:select` event
          orgField.trigger({
            type: "select2:select",
            params: {
              data: data.results[0],
            },
          });
        }
      },
    });
  });
})(django.jQuery);
