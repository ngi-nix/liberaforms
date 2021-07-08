// Validation errors messages for Parsley
// Load this after Parsley

Parsley.addMessages('eu', {
  defaultMessage: "Eremu hau ez da baliozkoa.",
  type: {
    email:        "Eremu honek baliozko eposta izan behar du.",
    url:          "Eremu honek baliozko URLs izan behar du.",
    number:       "Eremu honek baliozko zenbakia izan behar du.",
    integer:      "Eremu honek baliozko zenbakia izan behar du.",
    digits:       "Eremu honek baliozko digitua izan behar du.",
    alphanum:     "Eremu honek alfanumerikoa izan behar du."
  },
  notblank:       "Eremu honek ezin du hutsik egon.",
  required:       "Eremu hau nahitaezkoa da.",
  pattern:        "Eremu hau ez da zuzena.",
  min:            "Eremu honek %s edo altuagoa izan behar du.",
  max:            "Eremu honek %s edo baxuagoa izan behar du.",
  range:          "Eremu honek %s eta %s artean egon behar du.",
  minlength:      "Eremu hau motzegia da. Gutxieneko luzera %s karakteretakoa da.",
  maxlength:      "Eremu hau luzeegia da. Gehieneko luzera %s karakteretakoa da.",
  length:         "Eremu honen luzera %s eta %s karaketere artean egon behar du.",
  mincheck:       "%s aukera hautatu behar dituzu gutxienez.",
  maxcheck:       "%s aukera edo gutxiago hautatu behar dituzu.",
  check:          "%s eta %s aukeren artean hautatu behar duzu.",
  equalto:        "Eremu honek berbera izan behar du.",
  euvatin:        "Hau ez da baliozko BEZaren identifikazio zenbaki bat.",
});

Parsley.setLocale('eu');
