# Documentação das Rotas do Projeto

## Rotas principais (`almoxarifado/urls.py`)

| Rota                        | Nome           | Descrição                                                        |
|-----------------------------|----------------|------------------------------------------------------------------|
| `/admin/`                   | -              | Admin do Django                                                  |
| `/accounts/login/`          | login          | Tela de login                                                    |
| `/accounts/logout/`         | logout         | Logout do usuário                                                |
| `/estoque`                  | -              | Inclui todas as rotas do app `estoque`                           |
| `/`                         | home           | Página inicial (index)                                           |
| `/item/lista`               | item_list      | Lista de itens (template)                                        |
| `/item/formulario`          | item_form      | Formulário de item (template)                                    |
| `/movimentacao/formulario`  | movimentacao_form | Formulário de movimentação (template)                        |
| `/relatorio/cmv`            | relatorio_cmv  | Relatório de CMV (template)                                      |

---

## Rotas do app Estoque (`estoque/urls.py`)

### Itens
| Rota                           | Nome           | Descrição                        |
|--------------------------------|----------------|----------------------------------|
| `/estoque/`                    | index          | Página inicial do estoque        |
| `/estoque/item/novo/`          | item_create    | Cadastro de novo item            |
| `/estoque/item/<int:pk>/editar/` | item_edit   | Editar item                      |
| `/estoque/item/<int:pk>/excluir/`| item_delete  | Excluir item                     |
| `/estoque/item/<int:pk>/`      | item_detail    | Detalhes do item                 |
| `/estoque/buscar/item/`        | buscar_item    | Buscar item                      |

### Movimentação
| Rota                           | Nome                  | Descrição                |
|--------------------------------|-----------------------|--------------------------|
| `/estoque/movimentacao/novo/`  | movimentacao_create   | Nova movimentação        |

### Fornecedores
| Rota                                 | Nome                | Descrição                |
|--------------------------------------|---------------------|--------------------------|
| `/estoque/fornecedores/`             | fornecedor_list     | Lista de fornecedores    |
| `/estoque/fornecedor/novo/`          | fornecedor_create   | Novo fornecedor          |
| `/estoque/fornecedor/<int:pk>/editar/` | fornecedor_edit  | Editar fornecedor        |
| `/estoque/fornecedor/<int:pk>/excluir/`| fornecedor_delete | Excluir fornecedor       |
| `/estoque/buscar/fornecedor/`        | buscar_fornecedor   | Buscar fornecedor        |

### Inventário
| Rota                                 | Nome                        | Descrição                        |
|--------------------------------------|-----------------------------|----------------------------------|
| `/estoque/inventario/periodico/`     | relatorio_inventario_periodico | Relatório de inventário periódico |

### APIs de Estoque
| Rota                                         | Nome                  | Descrição                        |
|----------------------------------------------|-----------------------|----------------------------------|
| `/estoque/api/alertas/`                      | api_alertas_estoque   | API de alertas de estoque        |
| `/estoque/api/item/<int:item_id>/status/`    | api_status_item       | API de status de item            |
| `/estoque/api/itens/criticos/`               | api_itens_criticos    | API de itens críticos            |
| `/estoque/api/itens/reposicao/`              | api_itens_reposicao   | API de itens para reposição      |

---

> **Observação:**
> - As rotas do app `estoque` são acessadas a partir do prefixo `/estoque`.
> - Para detalhes de parâmetros, respostas das APIs ou exemplos de uso, consulte a documentação interna do projeto ou solicite detalhamento.
