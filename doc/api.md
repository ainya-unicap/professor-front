# API (nest-api)

Base: `API_BASE_URL` (`.env`) — local, geralmente `http://localhost:3000/api`; em produção, a URL do
backend publicado.

Todo acesso à API passa por `core.api.requisicao(metodo, caminho, token=None, **kwargs)`
(`core/api.py`). Essa função:

- Manda `Authorization: Bearer <token>` quando `token` é passado.
- Se a resposta não for `2xx`, levanta `ErroAPI(mensagem, status, codigo, campos)` — lido do corpo
  `{ error, codigo?, campos? }` que a API devolve.
- Se não conseguir conectar (rede, timeout), levanta `ErroAPI` com uma mensagem genérica.
- `204`/corpo vazio devolve `None`; senão devolve o JSON decodificado.

## Erros

O backend usa um filtro de erro padronizado (`HttpErrorFilter`) que sempre devolve:

```json
{ "error": "mensagem pra mostrar", "codigo": "CODIGO_OPCIONAL", "campos": { "campo": "mensagem" } }
```

- Quando `campos` vem preenchido, os formulários (`aplicar_erro_api`) colocam cada mensagem embaixo
  do campo correspondente.
- Quando só vem `codigo`, cada formulário tem um mapa `CODIGO_PARA_CAMPO` pra saber em qual campo
  mostrar o erro (ex.: `PERIODO_INVALIDO` → `period_nome`).
- `401` é tratado separado: ver [renovação de token](sessao-e-login.md#renovação-de-token).

## Endpoints usados

### Autenticação e cadastro (`core/api.py`)

| Função | Método/rota | Observação |
|---|---|---|
| `autenticar` | `POST /users/login` | Compartilhado com o app do aluno. Aceita `recaptchaToken`. |
| `cadastrar` | `POST /professores` | Cadastro de professora — `role` sempre `professor`, nunca vem do front. |
| `buscar_usuario` | `GET /users/:id` | Busca o perfil (nome, e-mail) depois do login. |
| `trocar_token` | `POST /users/refresh` | Troca o refresh token por um access token novo. |
| `encerrar_sessao_api` | `POST /users/logout` | Invalida o refresh token no backend. Erros são ignorados (logout sempre limpa a sessão local). |
| `listar_periodos` | `GET /academic-periods` | Autenticado — precisa de token. |
| `criar_periodo` | `POST /academic-periods` | `{ name, semester, start_date, end_date }`. |
| `listar_instituicoes` | `GET /institutions` | Público (usado até na tela de cadastro). |
| `criar_instituicao` | `POST /institutions` | `{ name, abbreviation }` — `abbreviation` é única no banco. |

### Turmas (`professor/api.py`)

| Função | Método/rota |
|---|---|
| `listar_turmas` | `GET /professores/turmas` |
| `criar_turma` | `POST /professores/turmas` — `{ name, period_id, institution_id? }` |
| `apagar_turma` | `DELETE /professores/turmas/:id` |
| `listar_codigos` | `GET /professores/turmas/:id/codigos` |
| `gerar_codigo` | `POST /professores/turmas/:id/codigos` |
| `apagar_codigo` | `DELETE /professores/turmas/:id/codigos/:codigoId` |
| `listar_alunos` | `GET /professores/turmas/:id/alunos` |
| `listar_entregas` | `GET /professores/turmas/:id/entregas` (não usado mais pela tela — ver abaixo) |

> `listar_alunos` foi adicionado ao `nest-api` junto com este front (não existia antes). Antes só
> existia `/entregas`, que só retorna quem já entregou — não dava pra mostrar os alunos sem entrega.
> Detalhes em [`turmas.md`](turmas.md#alunos-e-entregas).

Todas as rotas de `/professores/turmas/*` (exceto a própria criação de conta) exigem token de uma
conta com `role = professor` e, pra turma/código/aluno, que a turma pertença a quem está logado
(`validarDonaDaTurma` no backend — devolve `403` senão).

## Observação sobre período/instituição na criação de turma

O backend (`professor.service.ts`, método `criarTurma`) já sabe resolver período e instituição por
nome, criando na hora se não existir — aceita tanto `period_id`/`institution_id` quanto
`period: { name, semester, start_date, end_date }` / `institution: { name, abbreviation }` no corpo
do `POST /professores/turmas`.

Este front, por enquanto, resolve isso **antes** de chamar `criar_turma`: busca o nome na lista já
carregada e, se não achar, chama `criar_periodo`/`criar_instituicao` separadamente (ver
[`turmas.md`](turmas.md)). Funciona, mas duplica uma lógica que a API já faz num só request — dá pra
simplificar mandando `period`/`institution` como objeto direto no `criar_turma`, se for fazer uma
limpeza futura.
