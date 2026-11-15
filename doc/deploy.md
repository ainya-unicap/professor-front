# Deploy no Vercel

O Vercel tem suporte "zero-config" pra Django: detecta o `manage.py`, lê `WSGI_APPLICATION` e usa a
variável `application` do `config/wsgi.py`, roda `collectstatic` automaticamente (por `STATIC_ROOT`
estar definido) e serve os estáticos pela CDN. Não precisa de `vercel.json`, WhiteNoise nem
entrypoint customizado pra este projeto.

## O que foi preciso ajustar no `config/settings.py`

- **Sessão em cookie assinado** (`SESSION_ENGINE = signed_cookies`): o filesystem das funções
  serverless é efêmero/somente leitura, então sessão em SQLite não funcionaria. Ver
  [`sessao-e-login.md`](sessao-e-login.md).
- **`SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`**: o Vercel termina o HTTPS antes
  da função chegar no Django; sem isso, `request.is_secure()` nunca seria `True` e os cookies
  `secure` (sessão/CSRF) quebrariam o login em produção.
- **`CSRF_TRUSTED_ORIGINS`**: gerado a partir de `ALLOWED_HOSTS`, excluindo `localhost`/`127.0.0.1`.

## Variáveis de ambiente

Configurar no painel do projeto (Settings → Environment Variables) — ver a tabela completa no
[README](../README.md#variáveis-de-ambiente).

**Importante**: o Vercel trata variáveis de ambiente por ambiente (Production / Preview /
Development) **separadamente**. Marcar uma variável só pra Production não vale pra Preview (link
tipo `seu-app-<hash>-<time>.vercel.app`, gerado em todo push/PR) nem pra Development. Pra evitar
surpresa, marque as três caixinhas ao criar cada variável, a não ser que você realmente queira um
valor diferente por ambiente.

## `SECRET_KEY`

É a chave usada pelo Django pra assinar sessão e CSRF (entre outras coisas). Não existe valor
"correto" pré-definido — cada ambiente deve ter o seu, gerado uma vez e mantido estável (trocar a
chave em produção invalida todas as sessões e cookies ativos). Pra gerar um valor novo:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Problema comum: `DisallowedHost` num link de Preview

Sintoma: a aplicação funciona ao configurar `ALLOWED_HOSTS`, mas um deploy de **Preview**
(URL com hash aleatório, tipo `app-82ewqp0wm-time.vercel.app`) continua dando

```
django.core.exceptions.DisallowedHost: Invalid HTTP_HOST header: '...vercel.app'.
```

Causa mais comum: a variável `ALLOWED_HOSTS` foi marcada só para o ambiente **Production** no
painel, e o link testado é de **Preview**. Solução: editar a variável, marcar também Preview (e
Development, se for usar), e gerar um novo deploy — o "Redeploy" de um deploy já existente costuma
pegar as variáveis atuais, mas o mais garantido é um novo `git push` ou `vercel` pela CLI.

Usar `.vercel.app` (com o ponto, cobrindo qualquer subdomínio) em vez do domínio exato de cada deploy
evita ter que atualizar `ALLOWED_HOSTS` a cada novo link de Preview.
