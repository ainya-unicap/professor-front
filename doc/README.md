# Documentação · Forrageia Professor (front-end)

Documentação de apoio pra quem for dar manutenção neste projeto. O [README](../README.md) na raiz
tem a visão geral; aqui vai o detalhe de cada parte.

- [`api.md`](api.md) — endpoints da API (`nest-api`) usados por este front, o que cada um espera e devolve, e como os erros são tratados.
- [`sessao-e-login.md`](sessao-e-login.md) — como login, sessão e renovação de token funcionam, e o bypass de reCAPTCHA pra dev.
- [`turmas.md`](turmas.md) — como funciona a criação de turma (período/instituição), e a tela de alunos/entregas.
- [`deploy.md`](deploy.md) — como fazer deploy no Vercel, variáveis de ambiente e um problema comum (`DisallowedHost`).

## Visão rápida do projeto

```
Navegador  →  frontend (Django, este repo)  →  API (nest-api)
```

Este projeto não tem modelos de domínio nem banco de dados próprio (só a tabela de sessão do
Django, que nem é usada — a sessão vai inteira, assinada, no cookie). Toda view de página que
precisa de dado chama uma função em `core/api.py` ou `professor/api.py`, que faz a requisição HTTP
pra API e devolve JSON já decodificado (ou levanta `ErroAPI`).
