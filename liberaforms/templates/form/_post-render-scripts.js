function postFormRender(){
  if ($('#liberaform').find("span.formbuilder-required").length ||
      $('#liberaform').find("input[name=DPL]").filter(":visible").length ) {
    $("#required_message").show()
  }
  $("#liberaform").find(":checkbox").css("box-shadow", "none")
  $(".marked-up").find("a").prop("target", "_blank")
  {% if form %}
    setLimits();
    {% if form.might_send_confirmation_email() %}
    watchEmail();
    {% endif %}
    {% if form.has_file_field() %}
    var allowed_extensions = "{{ ', '.join(g.site.mimetypes['extensions']).upper() }}";
    $('input[type=file]').each(function() {
      $(this).attr('data-parsley-max-file-size',
                   {{ config['MAX_ATTACHMENT_SIZE']/1024 }}
      );
      $(this).attr('data-parsley-filemimetypes',
                  "{{ ', '.join(g.site.mimetypes['mimetypes']) }}"
      );
      var hints = $('<div class="file_hints hint">')
      var hint = $('<span>');
      hint.html('{%trans%}Valid file types{%endtrans%}'+': '+allowed_extensions)
      $(hints).append(hint).append('<br />')
      var hint = $('<span>');
      hint.html('{%trans size=max_attachment_size_for_humans%}The file should be no larger than {{size}}{%endtrans%}')
      $(hints).append(hint)
      $(this).after(hints)
    });
    {% endif %}
  {% endif %}
}
$(document).on("wheel", "input[type=number]", function (e) {
    $(this).blur();
});

{% if form %}
  function setLimits(){
    {% for field, values in form.expiryConditions['fields'].items() %}
      {% if values["type"] == "number" %}
        {% set available = values["condition"] - form.tally_number_field(field) %}
        if ($("#{{field}}").prop("max") && $("#{{field}}").prop("max") > {{available}}){
          if ({{available}} > 0){
              var hint=$("<div class='hint'>")
              hint.text("{%trans max=available%}Note: Maximum is now {{max}}{%endtrans%}");
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
        var msg = "{%trans%}Send me confirmation by mail to {email}{%endtrans%}"
        msg = msg.replace('{email}', $(this).val());
      }else{
        var msg = "{%trans%}Send me confirmation by mail{%endtrans%}"
      }
      $("#confirmation_email").html(msg);
      if (isEmailValid($(this).val())) {
        $("#confirmation_checkbox").prop("disabled", false );
        $("label.send-confirmation").css("cursor", "pointer");
      }else{
        $("#confirmation_checkbox").prop("disabled", true );
        $("label.send-confirmation").css("cursor", "initial");
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
