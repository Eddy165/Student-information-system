document.addEventListener('submit', function (event) {
  if (event.target.matches('[data-confirm]') && !confirm(event.target.dataset.confirm)) event.preventDefault();
});
document.addEventListener('change', function (event) {
  if (event.target.matches('[data-submit-on-change]')) event.target.form.requestSubmit();
});
