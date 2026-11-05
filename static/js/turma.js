document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-copiar]").forEach((botao) => {
    const textoOriginal = botao.textContent;
    botao.addEventListener("click", async () => {
      const campo = document.getElementById(botao.dataset.copiar);
      if (!campo) return;
      try {
        await navigator.clipboard.writeText(campo.value);
      } catch {
        campo.select();
        document.execCommand("copy");
      }
      botao.textContent = "Copiado!";
      setTimeout(() => {
        botao.textContent = textoOriginal;
      }, 2000);
    });
  });

  document.querySelectorAll("[data-mostrar-todos]").forEach((botao) => {
    const lista = document.getElementById(botao.dataset.mostrarTodos);
    if (!lista) return;
    const ocultos = [...lista.querySelectorAll("[hidden]")];
    const textoOriginal = botao.textContent;
    let aberto = false;
    botao.setAttribute("aria-expanded", "false");
    botao.setAttribute("aria-controls", lista.id);
    botao.addEventListener("click", () => {
      aberto = !aberto;
      ocultos.forEach((item) => {
        item.hidden = !aberto;
      });
      botao.textContent = aberto ? botao.dataset.textoMenos : textoOriginal;
      botao.setAttribute("aria-expanded", String(aberto));
    });
  });

  document.querySelectorAll("form[data-confirmar]").forEach((form) => {
    form.addEventListener("submit", (evento) => {
      if (!window.confirm(form.dataset.confirmar)) evento.preventDefault();
    });
  });
});
