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
professor/           telas da área do professor
  forms.py           formulários de nova turma, prazos e avaliação
  painel.py          prepara os textos e números do painel a partir da resposta da API
  apresentacao.py    rótulos de status, seções do relatório e formatação da nota
  views.py           painel, turma e correção
templates/
  base/              estrutura HTML comum a todas as páginas
  auth/              login e cadastro (base_auth.html é o layout com o painel verde)
  professor/         telas internas (base_professor.html é o layout com o menu lateral)
  icones/            ícones SVG incluídos direto no HTML
static/
  css/base.css       cores, fonte e botões usados em todo o projeto
  css/auth.css       layout das telas de login e cadastro
  css/professor.css  menu lateral, painel, cartões e modal
  js/modal.js        abre e fecha os modais
  js/turma.js        copiar link/código, mostrar todos os alunos e confirmar novo link
  img/               imagens
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
- Chamadas que exigem login passam por `chamar()` em `core/api.py`, que envia o token. Se o token expirou, ela pede um novo à API usando o `refresh` e repete a chamada. Se não conseguir, o usuário volta para o login com o aviso "Sua sessão expirou".

## Telas

| Rota | Tela | Situação |
|---|---|---|
| `/login/` | Fazer login | Pronta |
| `/cadastro/` | Criar conta | Pronta |
| `/painel/` | Painel do professor | Pronta |
| `/turmas/` | Lista de turmas | Pronta |
| `/turmas/nova/` | Modal Nova Turma | Pronta |
| `/turmas/<id>/` | Detalhe da turma (prazos, convite e alunos) | Pronta |
| `/turmas/<id>/correcoes/` | Relatórios entregues da turma | Pronta |
| `/correcoes/` | Atalho do menu: abre os relatórios da turma com mais pendências | Pronta |
| `/correcoes/<id>/` | Detalhe da correção (relatório e avaliação) | Pronta |

A rota `/` redireciona para `/login/`. Quem já está logado e abre o login ou o cadastro vai direto para o painel.

### Painel e Nova Turma

- O painel busca tudo em uma única chamada à API e mostra: o resumo do semestre, os indicadores, as turmas (com o progresso de entregas), os relatórios aguardando correção e os atalhos.
- O botão **Nova Turma** abre um modal (`<dialog>`) por cima do painel. O formulário envia para `/turmas/nova/`. Se houver erro, o painel é exibido de novo com o modal aberto e as mensagens nos campos. Se der certo, volta para o painel com um aviso mostrando o código de convite da turma.
- Sem JavaScript, o botão leva para `/turmas/nova/`, que mostra o mesmo modal já aberto.
- Depois de criar a turma, o professor vai direto para o detalhe dela, onde já encontra o link e o código de convite.
- As turmas da lista e os relatórios aguardando correção levam para as telas de detalhe. "Definir prazos" e "Convidar alunos" abrem a primeira turma da lista.
- O menu lateral leva para Painel, Turmas e Correções. "Ver todas" abre a lista de turmas e "Abrir caixa de entrada" abre as correções.
- Itens que levam a telas ainda não feitas (Checklists e Semestres anteriores) aparecem desativados, com a dica "Em breve".

### Turmas e Correções

- **Turmas**: lista todas as turmas com o progresso de entregas e o botão Abrir. O botão Nova Turma abre o mesmo modal do painel; se houver erro, o modal reaparece nesta tela.
- **Correções**: tabela com os relatórios entregues da turma (aluno, planta, data e PDF), com os que aguardam correção primeiro. O nome do aluno leva à correção. Quando o professor tem mais de uma turma, links no topo permitem trocar de turma. "Copiar Link da Turma" copia o link de convite.

### Detalhe da turma

- **Prazos**: quatro datas em ordem (início e encerramento dos registros, limite de entrega e prazo de correção) e a opção de aceitar entregas atrasadas. A ordem das datas é conferida no front e na API.
- **Convite**: link e código com botões de copiar. "Gerar novo link" pede confirmação e invalida o anterior.
- **Alunos**: mostra os 4 primeiros e o botão "Ver os N" para o resto. O status de quem já entregou leva para a correção.

### Detalhe da correção

- Mostra as cinco seções do relatório e as fotos do desenvolvimento. O PDF e as fotos passam pelo front (`/correcoes/<id>/pdf/` e `/correcoes/<id>/fotos/<foto_id>/`), que busca na API com o token do professor; nada fica público.
- A nota aceita vírgula (`8,5`). "Salvar e marcar como corrigido" exige a nota; "Salvar sem concluir" guarda o que foi escrito e mantém o relatório aguardando correção.
- "Anterior" e "Próximo" navegam entre os relatórios entregues da mesma turma.

## Padrões de layout

- As cores ficam como variáveis em `static/css/base.css` (`--verde-900`, `--verde-700`, `--superficie` etc.). Use as variáveis, e não os códigos das cores.
- A fonte é a Manrope, carregada do Google Fonts no `base.html`.
- Novas telas de autenticação estendem `auth/base_auth.html` e reaproveitam `auth/_campos.html` para os campos do formulário.
- Novas telas internas estendem `professor/base_professor.html` e informam a seção ativa do menu na variável `secao` (`painel`, `turmas` ou `correcoes`). A função `_contexto_base` em `professor/views.py` já monta isso e busca o contador de pendentes do menu.
- Se a API responde 404, a página mostra o 404 do Django (tratado em `professor_obrigatorio`).
- Os ícones são SVGs em `templates/icones/`, incluídos com `{% include %}`. Eles usam `currentColor`, então herdam a cor do texto.
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
