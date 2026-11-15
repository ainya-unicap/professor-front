# Turmas

## Painel (`/painel/`)

Mostra a lista de turmas da professora logada (`GET /professores/turmas`) e um botão **"Criar
turma"** que abre um modal (`<dialog>` nativo do HTML — `templates/professor/painel.html`).

## Criar turma

O modal tem:

- **Nome da turma** (texto livre).
- **Período letivo**: texto com sugestão (`<datalist>`) dos períodos já cadastrados
  (`GET /academic-periods`). Um checkbox "Não encontrei o período letivo na lista — quero cadastrar
  um novo" revela campos de semestre + data de início/fim, só quando marcado.
- **Instituição**: mesma ideia, com sugestão de `GET /institutions` e um checkbox que revela o campo
  de sigla.

Por quê checkbox em vez de só detectar automaticamente se o texto bate com algo da lista: fica
explícito pra professora quando ela está criando um cadastro novo (que exige dados extras) e evita
mostrar campos desnecessários o tempo todo — eles só aparecem quando realmente precisa.

### Validação (`professor/forms.py`, `TurmaForm`)

- Checkbox **desmarcado**: o nome digitado precisa bater (sem diferenciar maiúscula/minúscula) com
  o `name` ou `abbreviation` de algum item já carregado; senão, erro orientando marcar o checkbox.
- Checkbox **marcado**: exige os campos extras (semestre+datas, ou sigla) e guarda os dados em
  `form.periodo_novo` / `form.instituicao_nova` pra view criar depois.

### Criação (`professor/views.turma_criar`)

1. Se o form já resolveu um `period_id`/`institution_id` existente, usa direto.
2. Senão, chama `criar_periodo`/`criar_instituicao` (`core/api.py`) pra criar o registro na API e usa
   o `id` devolvido.
3. Chama `turmas_api.criar_turma(nome, period_id, institution_id)`.

Se o modal foi reaberto depois de um erro de validação do backend (ex.: sigla duplicada), o template
já sobe o `<dialog>` aberto (atributo `open`) pra professora ver o erro sem precisar clicar de novo
em "Criar turma".

> Nota: o backend (`nest-api`) hoje também sabe resolver período/instituição por nome e criar na hora
> num único `POST /professores/turmas` (mandando `period`/`institution` como objeto). Este front
> ainda faz essa resolução em dois passos (criar período/instituição, depois criar turma) — funciona,
> mas dá pra simplificar enviando tudo de uma vez pro backend, se for fazer uma limpeza depois.

## Detalhe da turma (`/painel/turmas/<id>/`)

Três seções:

1. **Códigos de entrada**: lista os códigos ativos (`GET /professores/turmas/:id/codigos`), com
   botão pra gerar um novo e apagar um existente. Vários códigos podem coexistir.
2. **Alunos na turma**: lista **todo aluno vinculado à turma**, usando
   `GET /professores/turmas/:id/alunos`. Quem já entregou o relatório tem um link "Baixar"; quem não
   entregou aparece com "Não entregou" — o aluno aparece de qualquer jeito, entregando ou não.
3. **Apagar turma**: remove a turma (e em cascata os vínculos, códigos e entregas, no backend).

### Alunos e entregas

O endpoint antigo, `GET /professores/turmas/:id/entregas`, só devolve quem **já entregou** o PDF —
não tem como saber quem está na turma e ainda não entregou só com esse dado. Pra atender o pedido de
sempre mostrar todo aluno (entregou ou não), foi adicionado um endpoint novo no `nest-api`:

- `TurmaRepository.findAlunosByTurma` (`src/repositories/turma.repository.ts`): lista os vínculos
  `AlunoTurma` da turma, com os dados do aluno.
- `ProfessorService.listarAlunos` (`src/services/professor.service.ts`): junta esse roster com as
  entregas da turma, devolvendo cada aluno com `entrega: {...}` ou `entrega: null`.
- `GET /professores/turmas/:id/alunos` (`src/modules/professores/professores.controller.ts`): mesma
  proteção dos outros endpoints de turma (`role = professor` + dona da turma).

`professor/api.listar_alunos` chama esse endpoint, e `turma_detalhe` usa o resultado direto no
template — sem precisar cruzar duas listas no front.
