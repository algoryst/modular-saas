// Alpine components. The CSP build cannot evaluate inline expressions, so every
// x-data component is registered here and templates reference it by name.
// This file must load before Alpine so the alpine:init listener is in place.
document.addEventListener("alpine:init", () => {
  // Wraps a password <input> rendered by Django; flips its type on click.
  window.Alpine.data("passwordToggle", () => ({
    shown: false,
    get hidden() {
      return !this.shown;
    },
    get pressed() {
      return String(this.shown);
    },
    toggle() {
      this.shown = !this.shown;
      this.$root.querySelector("input").type = this.shown ? "text" : "password";
    },
  }));
});
