function postFormRender(){
    if ($('#liberaform').find("span.formbuilder-required, #dataConsent").filter(":visible").length) {
        $("#required_message").show()
    }
    $("#liberaform").find(":checkbox").css("box-shadow", "none")
    $(".marked-up").find("a").prop("target", "_blank")
    {% if form %}
        setLimits();
        {% if form.might_send_confirmation_email() %}
        watchEmail();
        {% endif %}
    {% endif %}
}
$(document).on("wheel", "input[type=number]", function (e) {
    $(this).blur();
});

{% if form %}
function setLimits(){
    {% for field, values in form.expiryConditions.items() %}
        {% if values["type"] == "number" %}
            {% set available = values["condition"] - form.tally_number_field(field) %}
            if ($("#{{field}}").prop("max") && $("#{{field}}").prop("max") > {{available}}){
                    if ({{available}} > 0){
                        var hint=$("<div class='hint'></div>")
                        hint.text("{{ gettext('Note: Maximum is now %(max)s', max=available) }}");
                        hint.insertBefore("#{{field}}");
                        $("#{{field}}").prop("max", {{available}});
                    }
            }
            if (! $("#{{field}}").prop("max")){
                $("#{{field}}").prop("max", {{available}});
            }
        {% endif %}
    {% endfor %}
    return;
}
{% if form.might_send_confirmation_email() %}
function watchEmail(){
    $("input[type='email']").first().on('input', function() {
        if ($(this).val()) {
            $("#confirmation_email").html("{%trans%}to{%endtrans%} "+ $(this).val())
        }else{
            $("#confirmation_email").html("");
        }
        if (isEmailValid($(this).val())) {
            $("#confirmation_checkbox").prop("disabled", false );
        }else{
            $("#confirmation_checkbox").prop("disabled", true );
            $("#confirmation_checkbox").prop("checked", false );
        }
    });
}
// TODO: this code might be better?
/*
is_valid = field.checkVadility()
*/
//var re = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;
//var is_email=re.test(input.val());
function isEmailValid(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}
{% endif %}
{% endif %}
