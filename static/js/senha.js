document.addEventListener("DOMContentLoaded", () => {
  const camposSenha = document.querySelectorAll('input[type="password"]');

  camposSenha.forEach((input) => {
    const wrapper = document.createElement("div");
    wrapper.className = "campo-senha";

    input.parentNode.insertBefore(wrapper, input);
    wrapper.appendChild(input);

    const botao = document.createElement("button");
    botao.type = "button";
    botao.className = "campo-senha__toggle";
    botao.setAttribute("aria-label", "Mostrar senha");

    const iconeOlhoAberto = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
        <circle cx="12" cy="12" r="3"></circle>
      </svg>`;

    const iconeOlhoFechado = `
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
        <line x1="1" y1="1" x2="23" y2="23"></line>
      </svg>`;

    botao.innerHTML = iconeOlhoAberto;

    botao.addEventListener("click", () => {
      const estaOculta = input.type === "password";
      input.type = estaOculta ? "text" : "password";
      botao.innerHTML = estaOculta ? iconeOlhoFechado : iconeOlhoAberto;
      botao.setAttribute("aria-label", estaOculta ? "Ocultar senha" : "Mostrar senha");
    });

    wrapper.appendChild(botao);
  });
});