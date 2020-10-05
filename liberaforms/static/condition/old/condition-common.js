

function getSelectedValues(group, field_name, field_type) {
    var values = []
    if (field_type == "checkbox") {
        var field_name=field_name+"[]"
        group.find('[name="'+field_name+'"]').each(function(){
            if ($(this).prop('checked') == true) {
                values.push($(this).val())
            }
        });
        return values
    }
    if (field_type == "radio") {
        return this.group.find('input[name="'+field_name+'"]').val()
    }
    if (field_type == "select") {
        return this.group.find('select[name="'+field_name+'"]').val()
    }
}
