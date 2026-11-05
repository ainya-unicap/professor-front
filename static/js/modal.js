document.addEventListener("DOMContentLoaded", () => {
  const abrir = (modal) => {
    if (!modal || modal.open) return;
    modal.showModal();
    const primeiroErro = modal.querySelector(".campo--erro input");
    (primeiroErro || modal.querySelector("input:not([type=hidden])"))?.focus();
  };

  document.querySelectorAll("[data-abrir-modal]").forEach((gatilho) => {
    gatilho.addEventListener("click", (evento) => {
      const modal = document.getElementById(gatilho.dataset.abrirModal);
      if (!modal || typeof modal.showModal !== "function") return;
      evento.preventDefault();
      abrir(modal);
    });
  });

  document.querySelectorAll("dialog.modal").forEach((modal) => {
    if (modal.hasAttribute("data-abrir")) abrir(modal);

    modal.querySelectorAll("[data-fechar-modal]").forEach((botao) => {
      botao.addEventListener("click", (evento) => {
        evento.preventDefault();
        modal.close();
      });
    });

    modal.addEventListener("click", (evento) => {
      if (evento.target === modal) modal.close();
    });

    modal.addEventListener("close", () => {
      if (window.location.pathname !== modal.dataset.voltarPara && modal.dataset.voltarPara) {
        window.history.replaceState(null, "", modal.dataset.voltarPara);
      }
    });
  });

  document.querySelectorAll("[aria-disabled=true]").forEach((link) => {
    link.addEventListener("click", (evento) => evento.preventDefault());
  });
});
