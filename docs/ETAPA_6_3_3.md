# ETAPA 6.3.3 — Edição e exclusão de usuários

Complemento da gestão de usuários e perfis.

## Implementado
- Administrador pode editar nome completo e nome de usuário.
- Administrador pode alterar o perfil (Operador, Supervisor ou Administrador).
- Administrador pode ativar/desativar contas.
- Administrador pode redefinir senha.
- Administrador pode excluir definitivamente outro usuário.
- Exclusão exige confirmação explícita no frontend.
- O administrador autenticado não pode excluir a própria conta, retirar o próprio perfil ADMIN ou desativar a si mesmo.
- O backend protege contra exclusão do último administrador ativo.
- Histórico de auditoria é preservado mesmo após a exclusão: referências `user_id` antigas são anuladas, mantendo `username`, ação e data/hora.
- Exclusões geram evento de auditoria `USER_DELETED`.

Nenhuma migration adicional é necessária.
