(function (document) {
  document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form');
    if (!form) {
      return;
    }
    const inputs = form.querySelectorAll('input, select');
    inputs.forEach((input) => {
      input.addEventListener('change', () => {
        form.requestSubmit();
      });
    });
  });
})(document);
