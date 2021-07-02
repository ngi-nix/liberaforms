// Validation errors messages for Parsley
// Load this after Parsley

Parsley.addMessages('ca', {
  defaultMessage: "Aquest camp sembla ser invàlid.",
  type: {
    email:        "Aquest camp ha de ser una adreça de correu electrònic vàlida.",
    url:          "Aquest camp ha de ser una URL vàlida.",
    number:       "Aquest camp ha de ser un nombre vàlid.",
    integer:      "Aquest camp ha de ser un nombre enter vàlid.",
    digits:       "Aquest camp només pot contenir dígits.",
    alphanum:     "Aquest camp ha de ser alfanumèric."
  },
  notblank:       "Aquest camp no pot ser buit.",
  required:       "Aquest camp és obligatori.",
  pattern:        "Aquest camp és incorrecte.",
  min:            "Aquest camp no pot ser menor que %s.",
  max:            "Aquest camp no pot ser major que %s.",
  range:          "Aquest camp ha d'estar entre %s i %s.",
  minlength:      "Aquest camp és massa curt. La longitud mínima és de %s caràcters.",
  maxlength:      "Aquest camp és massa llarg. La longitud màxima és de %s caràcters.",
  length:         "La longitud d'aquest camp ha de ser d'entre %s i %s caràcters.",
  mincheck:       "Has de marcar un mínim de %s opcions.",
  maxcheck:       "Has de marcar un màxim de %s opcions.",
  check:          "Has de marcar entre %s i %s opcions.",
  equalto:        "Aquest camp ha de ser el mateix."
});

Parsley.setLocale('ca');
