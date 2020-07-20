function postFormRender(){
    if ($('#gngform').find("span.formbuilder-required").filter(":visible").length) {
        $("#required_message").show()
    }
    $("#gngform").find(":checkbox").css("box-shadow", "none")
    $(".marked-up").find("a").prop("target", "_blank")
    {% if form %}
        setLimits();
        {% if form.mightSendConfirmationEmail() %}
        watchEmail();
        {% endif %}
    {% endif %}
}
$(document).on("wheel", "input[type=number]", function (e) {
    $(this).blur();
});

{% if form %}
function setLimits(){
    {% for field, values in form.fieldConditions.items() %}
        {% if values["type"] == "number" %}
            {% set available = values["condition"] - form.tallyNumberField(field) %}
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
{% if form.mightSendConfirmationEmail() %}
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
function isEmailValid(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}
{% endif %}
{% endif %}
