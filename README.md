# Forrageia · Professor (front-end)

Telas da área do professor do app Forrageia (Meu Canteiro), feitas a partir do Figma. Este projeto não guarda dados próprios: tudo vem da API do repositório [nest-api](https://github.com/ainya-unicap/nest-api).

Feito com Django: as páginas são montadas no servidor com templates e CSS próprio, sem framework JavaScript (só um pouco de JS simples nas telas de turma, pra abrir o modal e mostrar/esconder campos).

Mais detalhes (sessão, API, formulários, deploy) ficam em [`doc/`](doc/README.md).

## Estrutura

```
config/              configurações do projeto e rotas principais
core/                login, cadastro, sessão e cliente da API
  api.py             funções que chamam a API do backend (auth, cadastro, períodos, instituições)
  forms.py           formulários e validações de login e cadastro
  sessao.py          sessão (cookie assinado), decorator professor_obrigatorio, renovação de token
  views.py           telas de login, cadastro e logout
professor/           área do professor
  api.py             funções que chamam a API do backend (turmas, códigos, alunos/entregas)
  forms.py           formulário de criação de turma (com período/instituição novos, se precisar)
  views.py           painel, turma (detalhe), código de entrada
  urls.py            rotas da área do professor
templates/
  base/              estrutura HTML comum a todas as páginas (inclui mensagens e bloco de JS)
  auth/              login e cadastro
  professor/         painel (lista de turmas + modal de criar turma) e detalhe da turma
static/
  css/base.css       cores, fonte e botões usados em todo o projeto
  css/auth.css       layout das telas de login, cadastro e dos formulários em geral
  css/professor.css  painel, modal de criar turma, listas de turmas/códigos/alunos
doc/                 documentação do projeto (ver doc/README.md)
```

## Como funciona

```
Navegador  →  frontend (Django)  →  API do backend (nest-api)
```

1. O navegador sempre conversa com o frontend, que devolve o HTML pronto.
2. Quando uma tela precisa de dados (login, cadastro, turmas, alunos), a view chama uma função de `core/api.py` ou `professor/api.py`, que faz a requisição HTTP para o backend via `core/api.requisicao`.
3. Se a API devolve erro de validação (`400`), cada mensagem aparece embaixo do campo do formulário correspondente (`ErroAPI.campos`/`codigo`). Se a API está fora do ar, a tela mostra um aviso geral.
4. Um token expirado (`401`) é renovado automaticamente por `core/sessao.com_renovacao`, que usa o refresh token guardado na sessão e tenta a chamada de novo uma única vez.

### Login e sessão

- Depois do login ou do cadastro, o frontend guarda na **sessão do Django** os tokens e os dados do usuário (nome, e-mail, papel). O token nunca vai para o JavaScript da página.
- A sessão é **assinada no cookie** (`SESSION_ENGINE = signed_cookies`), não fica em banco — necessário porque o Vercel roda em funções serverless sem disco persistente.
- Só usuários com papel `professor` entram na área do professor. Uma conta de aluno vê a mensagem "Este acesso é exclusivo para professores."
- Para exigir login numa view, use o decorator `professor_obrigatorio` de `core/sessao.py`. Ele também coloca os dados do usuário em `request.usuario`.
- O logout é um `POST` em `/logout/`, avisa a API (`POST /users/logout`) e apaga a sessão.

### reCAPTCHA

- Se `RECAPTCHA_SITE_KEY` estiver preenchida, o widget aparece nas telas de login/cadastro e manda o token real pra API.
- Em dev, sem site key, dá pra usar `RECAPTCHA_BYPASS_TOKEN` — o mesmo valor configurado no backend — que o front manda como `recaptchaToken` sem precisar do widget. **Nunca usar em produção.**

### Turmas, período e instituição

- A professora cria a turma num modal (botão "Criar turma" no painel). Período e instituição são campos de texto com sugestão (`<datalist>`) das opções já cadastradas.
- Se o período/instituição digitado não está na lista, ela marca um checkbox ("não encontrei X, quero cadastrar um novo") que revela os campos extras necessários (semestre + datas, ou sigla).
- O front resolve o nome digitado pro ID existente ou cria um novo via `POST /academic-periods` / `POST /institutions` antes de criar a turma — ver `professor/forms.py` (`TurmaForm.clean`) e `professor/views.py` (`turma_criar`).

### Alunos e entregas

- A tela de detalhe da turma (`/painel/turmas/<id>/`) lista **todo aluno vinculado à turma**, entregue ou não — usa `GET /professores/turmas/:id/alunos` (endpoint adicionado no `nest-api` especificamente pra isso; antes só existia `/entregas`, que mostrava só quem já tinha entregado).
- Quem entregou tem um link "Baixar"; quem não entregou aparece com "Não entregou".

## Telas

| Rota | Tela | Situação |
|---|---|---|
| `/login/` | Fazer login | Pronta |
| `/cadastro/` | Criar conta | Pronta |
| `/painel/` | Painel do professor (lista de turmas + modal de criar turma) | Pronta |
| `/painel/turmas/<id>/` | Detalhe da turma (códigos de entrada, alunos e entregas, apagar turma) | Pronta |

A rota `/` redireciona para `/login/`. Quem já está logado e abre o login ou o cadastro vai direto para o painel.

## Padrões de layout

- As cores ficam como variáveis em `static/css/base.css` (`--verde-900`, `--verde-700`, `--superficie` etc.). Use as variáveis, e não os códigos das cores.
- A fonte é a Manrope, carregada do Google Fonts no `base.html`.
- Novas telas de autenticação estendem `auth/base_auth.html` e reaproveitam `auth/_campos.html` para os campos do formulário.
- As classes seguem o padrão BEM, por exemplo `form__campo` e `form__campo--erro`.
- As telas se adaptam a notebooks menores e ao celular (formulários quebram linha, modal vira tela cheia no mobile etc.).

## Variáveis de ambiente

Preencha o `.env` a partir do `.env.example` (o `.env` não vai para o git):

| Variável | Para quê |
|---|---|
| `SECRET_KEY` | Chave do Django (assinatura de sessão/CSRF). Gere uma própria, não reaproveite entre ambientes. |
| `DEBUG` | `True` em dev, `False` em produção. |
| `ALLOWED_HOSTS` | Hosts aceitos, separados por vírgula. Em produção, incluir o domínio do Vercel (pode usar `.vercel.app` pra cobrir os deploys de preview). |
| `API_BASE_URL` | Endereço da API (`nest-api`). Local: `http://localhost:3000/api`. Produção: a URL do backend no Vercel. |
| `RECAPTCHA_SITE_KEY` | Site key pública do reCAPTCHA. Vazia = widget não aparece. |
| `RECAPTCHA_BYPASS_TOKEN` | Token de bypass pra testar sem o widget (precisa estar configurado igual no backend). Só para dev. |

## Rodando localmente

O backend (`nest-api`) precisa estar rodando ao mesmo tempo, em outro terminal.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 8001
```

Preencha o `.env` conforme a tabela acima.

Depois, acesse http://localhost:8001.

## Testes

```bash
python manage.py test
```

Os testes simulam as respostas da API, então não precisam do backend rodando.

## Deploy (Vercel)

O projeto usa o suporte "zero-config" do Vercel para Django: não precisa de `vercel.json` nem WhiteNoise, só configurar as variáveis de ambiente (ver tabela acima) no painel do projeto — e marcar cada uma para os três ambientes (Production, Preview e Development), já que o Vercel trata isso separadamente por deploy.

## Fluxo de trabalho

- Uma branch por tela, criada a partir da `main`, por exemplo `feat/cadastro`.
- Um PR por tela, contra a `main`.
- Quando a tela também mexer no backend, a branch tem o mesmo nome nos dois repositórios.
