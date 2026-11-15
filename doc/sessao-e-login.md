# Sessão, login e reCAPTCHA

## Login

1. `core/views.login_view` valida o formulário (`LoginForm`) e chama `autenticar(email, senha, recaptcha_token)` → `POST /users/login`.
2. A API devolve os tokens (`accessToken`, `refreshToken`) e `role`/`id`. Se `role != "professor"`, mostra "Este acesso é exclusivo para professores." — contas de aluno não entram aqui.
3. Com o token em mãos, busca o perfil (`buscar_usuario`) pra pegar nome/e-mail e salva tudo na sessão (`salvar_login`, em `core/sessao.py`).
4. Redireciona pro painel (`professor:painel`).

## Sessão

- `SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"` (`config/settings.py`): a sessão
  inteira vai **assinada no cookie**, não fica salva em banco/arquivo. Isso é necessário pro Vercel,
  onde o filesystem das funções é efêmero/somente leitura — sessão em SQLite não sobreviveria entre
  requisições.
- Dado guardado em `request.session["auth"]`: `id`, `role`, `accessToken`, `refreshToken`, `name`,
  `email`.
- O **token de acesso nunca é exposto no HTML/JS** — ele só circula entre a view e a API, do lado do
  servidor.
- `core.sessao.professor_obrigatorio` é o decorator usado em toda view que exige login de professora.
  Ele lê a sessão, confere `role == "professor"` e expõe os dados em `request.usuario`; senão,
  redireciona pro login.

## Renovação de token

O access token expira em 15 minutos; o refresh token dura 7 dias e é rotacionado a cada uso.

`core.sessao.com_renovacao(request, chamada, *args, **kwargs)` é o helper usado por toda chamada
autenticada às turmas/códigos/alunos:

1. Tenta `chamada(token_atual, *args, **kwargs)`.
2. Se vier `ErroAPI` com `status == 401`, chama `POST /users/refresh` com o refresh token da sessão.
3. Se o refresh também falhar, encerra a sessão (`encerrar_login`) e repropaga o erro — o usuário cai
   pro login.
4. Se o refresh funcionar, atualiza os tokens na sessão e tenta a chamada original de novo, uma
   única vez.

Qualquer view nova que precise chamar a API autenticada deve passar pelo `com_renovacao` em vez de
chamar a função de API direto — é o que garante a renovação automática.

## Logout

`POST /logout/` (`core.views.logout_view`): avisa a API (`POST /users/logout`, pra invalidar o
refresh token no banco — erro aqui é ignorado, o logout sempre limpa a sessão local) e chama
`request.session.flush()`.

## reCAPTCHA

- Se `RECAPTCHA_SITE_KEY` (`.env`) estiver preenchida, o widget aparece no login/cadastro
  (`recaptcha_site_key` é passado pro template) e o JS da página popula um campo oculto
  (`recaptcha_token`) que vai no `POST`.
- `core.views._recaptcha_token(form)`: usa o token do widget se existir; senão, cai pro
  `RECAPTCHA_BYPASS_TOKEN` (também do `.env`), se configurado.
- O bypass só funciona se o **mesmo valor** estiver configurado como `RECAPTCHA_BYPASS_TOKEN` no
  backend (`nest-api`) — é um mecanismo próprio do backend pra pular a verificação do Google em
  dev/teste, não tem relação com a secret key do reCAPTCHA (que é do backend, nunca do front).
- **Nunca** usar o bypass em produção — lá, configure a `RECAPTCHA_SITE_KEY` real e deixe o widget
  aparecer de verdade.
