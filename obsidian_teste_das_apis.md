# Guia de Testes das APIs de Alertas de Estoque

## Índice

1.  [Pré-requisitos](#pré-requisitos)\
2.  [Autenticação](#autenticação)\
3.  [Endpoints Disponíveis](#endpoints-disponíveis)\
4.  [Testes com cURL](#testes-com-curl)\
5.  [Respostas Esperadas](#respostas-esperadas)\
6.  [Códigos de Erro](#códigos-de-erro)\
7.  [Verificar Logs](#verificar-logs)\

------------------------------------------------------------------------

## 1. Pré-requisitos

### 1.1 Servidor Django em execução

``` bash
./anotacoes/executar_projeto.sh
python manage.py runserver
```

### 1. 2. Usuário autenticado

Crie usuário com:

``` bash
python manage.py createsuperuser
```

Login: `http://localhost:8000/admin`

------------------------------------------------------------------------

## 2. Autenticação

### Obter Cookie de Sessão

**Via navegador:**\
Acesse admin → DevTools → Cookies → `sessionid`.

**Via cURL:**

``` bash
curl -c cookies.txt -d "username=SEU_USUARIO&password=SUA_SENHA" http://localhost:8000/accounts/login/
```

------------------------------------------------------------------------

## 3. Endpoints Disponíveis

  Método   Endpoint                   Descrição
  -------- -------------------------- ----------------------
  GET      `/api/alertas/`            Lista alertas
  GET      `/api/item/<id>/status/`   Status do item
  GET      `/api/itens/criticos/`     Itens críticos
  GET      `/api/itens/reposicao/`    Itens para reposição

------------------------------------------------------------------------

## 4. Testes com cURL


``` bash
curl -b "sessionid=SEU_SESSION_ID" http://localhost:8000/api/alertas/ | python -m json.tool
```

### Status de item específico

``` bash
curl -b "sessionid=SEU_SESSION_ID" http://localhost:8000/api/item/1/status/ | python -m json.tool
  ```

### Itens críticos

```bash
curl -b "sessionid=SEU_SESSION_ID" http://localhost:8000/api/itens/criticos/ | python -m json.tool
```

### Itens para reposição

```bash
curl -b "sessionid=SEU_SESSION_ID"  http://localhost:8000/api/itens/reposicao/ | python -m json.tool
```

### Teste completo com login automático

```bash
#!/bin/bash

curl -c cookies.txt -d "username=admin&password=senha123" \
  http://localhost:8000/accounts/login/

echo "=== Teste 1: Todos os Alertas ==="
curl -b cookies.txt http://localhost:8000/api/alertas/ | python -m json.tool

echo -e "\n=== Teste 2: Itens Críticos ==="
curl -b cookies.txt http://localhost:8000/api/itens/criticos/ | python -m json.tool

echo -e "\n=== Teste 3: Itens para Reposição ==="
curl -b cookies.txt http://localhost:8000/api/itens/reposicao/ | python -m json.tool

echo -e "\n=== Teste 4: Status do Item 1 ==="
curl -b cookies.txt http://localhost:8000/api/item/1/status/ | python -m json.tool

```


------------------------------------------------------------------------

## 5. Respostas Esperadas

Exemplo:

``` json
{
  "resumo": {
    "total_alertas": 2
  }
}
```

------------------------------------------------------------------------

## 6. Códigos de Erro

  Código   Descrição
  -------- ------------------
 
  302      Login necessário
  401      Não autorizado
  403      Sem permissão
  404      Não encontrado
  500      Erro interno

------------------------------------------------------------------------

## 7. Verificar Logs

No terminal do Django:

    "GET /api/alertas/ HTTP/1.1" 200

------------------------------------------------------------------------