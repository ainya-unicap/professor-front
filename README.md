# Forrageia · Professor (front-end)

Telas da área do professor do app Forrageia (Meu Canteiro), feitas a partir do Figma. Este projeto não guarda dados próprios: tudo vem da API do repositório [professor-back-end](https://github.com/ainya-unicap/professor-back-end).

Feito com Django: as páginas são montadas no servidor com templates e CSS próprio, sem framework JavaScript.

## Estrutura

```
config/              configurações do projeto e rotas principais
core/                login, cadastro, sessão e cliente da API
  api.py             funções que chamam a API do backend
  forms.py           formulários e validações das telas
  sessao.py          como o login fica guardado na sessão e quais páginas exigem login
  views.py           telas de login, cadastro e logout
professor/           telas da área do professor (painel, turmas, correções)
templates/
  base/              estrutura HTML comum a todas as páginas
  auth/              login e cadastro (base_auth.html é o layout com o painel verde)
  professor/         telas internas
static/
  css/base.css       cores, fonte e botões usados em todo o projeto
  css/auth.css       layout das telas de login e cadastro
  img/               ícones
```

## Como funciona

```
Navegador  →  frontend (Django)  →  API do backend
```

1. O navegador sempre conversa com o frontend, que devolve o HTML pronto.
2. Quando uma tela precisa de dados (login, cadastro, turmas), a view chama uma função de `core/api.py`, que faz a requisição HTTP para o backend.
3. Se a API devolve erro de validação (`400`), cada mensagem aparece embaixo do campo do formulário correspondente. Se a API está fora do ar, a tela mostra um aviso geral.

### Login e sessão

- Depois do login ou do cadastro, o frontend guarda na **sessão do Django** os tokens e os dados do usuário (nome, e-mail, matrícula, papel). O token nunca vai para o JavaScript da página.
- Só usuários com papel `professor` entram na área do professor. Uma conta de aluno vê a mensagem "Este acesso é exclusivo para professores."
- Para exigir login numa view, use o decorator `professor_obrigatorio` de `core/sessao.py`. Ele também coloca os dados do usuário em `request.usuario`.
- O logout é um `POST` em `/logout/` e apaga a sessão.

## Telas

| Rota | Tela | Situação |
|---|---|---|
| `/login/` | Fazer login | Pronta |
| `/cadastro/` | Criar conta | Pronta |
| `/painel/` | Painel do professor | Provisória: só mostra o nome e o botão Sair |

A rota `/` redireciona para `/login/`. Quem já está logado e abre o login ou o cadastro vai direto para o painel.

## Padrões de layout

- As cores ficam como variáveis em `static/css/base.css` (`--verde-900`, `--verde-700`, `--superficie` etc.). Use as variáveis, e não os códigos das cores.
- A fonte é a Manrope, carregada do Google Fonts no `base.html`.
- Novas telas de autenticação estendem `auth/base_auth.html` e reaproveitam `auth/_campos.html` para os campos do formulário.
- As classes seguem o padrão BEM, por exemplo `form__campo` e `form__campo--erro`.
- As telas se adaptam a notebooks menores e ao celular.

## Rodando localmente

O backend precisa estar rodando ao mesmo tempo, em outro terminal.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 8001
```

Preencha o `.env` a partir do `.env.example`. É nele que fica o endereço da API. O `.env` não vai para o git.

Depois, acesse http://localhost:8001.

## Testes

```bash
python manage.py test
```

Os testes simulam as respostas da API, então não precisam do backend rodando.

## Fluxo de trabalho

- Uma branch por tela, criada a partir da `main`, por exemplo `feat/cadastro`.
- Um PR por tela, contra a `main`.
- Quando a tela também mexer no backend, a branch tem o mesmo nome nos dois repositórios.
