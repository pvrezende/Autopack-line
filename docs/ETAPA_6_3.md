# ETAPA 6.3 — Gestão de usuários e perfis

## Perfis

- **OPERATOR**: Dashboard e Operação (leitura/paletização).
- **SUPERVISOR**: Dashboard, Operação e Rastreabilidade/relatórios.
- **ADMIN**: acesso total, incluindo Configurações, Usuários e Auditoria.

As permissões são aplicadas no frontend e, principalmente, na API. Ocultar uma tela não substitui a validação do backend.

## Autenticação

A API usa JWT Bearer com validade padrão de 8 horas (`JWT_EXP_MINUTES=480`). A senha é armazenada apenas como hash bcrypt.

Na primeira subida após a migration `0004`, o backend cria um administrador somente se a tabela de usuários estiver vazia:

- usuário: `admin`
- senha inicial: `Autopack@2026`

Os valores podem e devem ser alterados no `.env` através de `INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_NAME` e `INITIAL_ADMIN_PASSWORD`. Após o primeiro acesso, use **Alterar senha**.

## Gestão

O administrador pode cadastrar usuários, escolher perfil, ativar/desativar contas e redefinir senhas. O sistema impede que o administrador logado desative a própria conta ou remova o próprio perfil ADMIN.

## Auditoria

A tabela `audit_logs` registra ações relevantes, incluindo login, falha de login, alterações de usuários/senhas, leituras, confirmação de paletização e alterações operacionais/configurações. A tela **Usuários** mostra a auditoria recente.

## Atualização sem perder os dados

Execute:

```powershell
docker compose down
docker compose up --build
```

Não use `docker compose down -v`, pois o volume contém o MySQL existente. A migration `0004` adiciona as tabelas de segurança sem remover dados produtivos.
