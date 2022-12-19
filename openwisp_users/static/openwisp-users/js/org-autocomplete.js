(function ($) {
    'use strict';
    $(document).ready(function () {
        $('select#id_organization').on('change', function () {
            var target = $('select#id_organization option:selected');
            if (target.val() === 'null') {
                // The select2 library requires data in a specific format
                // https://select2.org/data-sources/formats.
                // select2 does not render option with blank "id" (i.e. id='').
                // Therefore, the backend uses "null" id for Systemwide shared
                // objects. This causes issues on submitting forms because
                // Django expects an empty string (for None) or a UUID string.
                // Hence, we need to update the value of selected option here.
                target.val('');
            }
        });
    });
}(django.jQuery));
