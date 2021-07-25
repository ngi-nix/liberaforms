// This is included with the Parsley library itself,
// thus there is no use in adding it to your project.


Parsley.addMessages('en', {
  defaultMessage: "This field seems to be invalid.",
  type: {
    email:        "This field should be a valid email.",
    url:          "This field should be a valid url.",
    number:       "This field should be a valid number.",
    integer:      "This field should be a valid integer.",
    digits:       "This field should be digits.",
    alphanum:     "This field should be alphanumeric."
  },
  notblank:       "This field should not be blank.",
  required:       "This field is required.",
  pattern:        "This field seems to be invalid.",
  min:            "This field should be greater than or equal to %s.",
  max:            "This field should be lower than or equal to %s.",
  range:          "This field should be between %s and %s.",
  minlength:      "This field is too short. It should have %s characters or more.",
  maxlength:      "This field is too long. It should have %s characters or fewer.",
  length:         "This field length is invalid. It should be between %s and %s characters long.",
  mincheck:       "You must select at least %s choices.",
  maxcheck:       "You must select %s choices or fewer.",
  check:          "You must select between %s and %s choices.",
  equalto:        "This field should be the same.",
  euvatin:        "It's not a valid VAT Identification Number.",
});

Parsley.setLocale('en');
