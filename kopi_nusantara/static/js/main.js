document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll('input[type="number"]').forEach((input) => {
    input.addEventListener("change", () => {
      const min = Number(input.min || 1);
      const max = Number(input.max || 999);
      let value = Number(input.value || min);
      input.value = Math.min(max, Math.max(min, value));
    });
  });
});