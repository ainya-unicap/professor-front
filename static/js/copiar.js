document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("[data-copiar]").forEach((botao) => {
    const textoOriginal = botao.textContent;
    botao.addEventListener("click", async () => {
      const campo = document.getElementById(botao.dataset.copiar);
      if (!campo) return;
      try {
        await navigator.clipboard.writeText(campo.value);
        botao.textContent = "Link copiado!";
      } catch {
        botao.textContent = "Não foi possível copiar";
      }
      setTimeout(() => {
        botao.textContent = textoOriginal;
      }, 2000);
    });
  });
});
