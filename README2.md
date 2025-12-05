
# **  Sistema de Gestão Almoxarifado **

<div align="center">
  <img src="static/imagens/banner-projeto.png" alt="Banner do Projeto" style="object-fit:cover;height:180px;">
</div>

<p align="center">
  <img src="https://img.shields.io/badge/license-BSD-blue?style=for-the-badge" alt="Licença BSD">
  <img src="https://img.shields.io/badge/status-em%20desenvolvimento-yellow?style=for-the-badge" alt="Status de desenvolvimento">
</p>

# ** Descrição do Projeto **

Projeto de extensão universitária desenvolvido pelos alunos do 5º semestre do IFMT Campus Cuiabá, na disciplina Oficina de Prática Extensionista II.

O sistema visa informatizar e otimizar os processos de gestão do almoxarifado da FUNAC, instituição pública do Governo do Estado de Mato Grosso, trazendo benefícios tanto para o fluxo administrativo quanto para o desenvolvimento acadêmico dos alunos envolvidos.

---

# ** Contexto Institucional **

- **Instituição:** IFMT – Campus Cel. Octayde Jorge da Silva  
- **Disciplina:** Oficina de Prática Extensionista II  
- **Parceria:** FUNAC/SEJUS/MT (Fundação Nova Chance – Governo do Estado de Mato Grosso)  
- **Área Impactada:** Gestão de materiais e logística  
- **Público Beneficiado:** Servidores administrativos da FUNAC e comunidade acadêmica

---

# ** Índice **

1. [Objetivos](#--objetivos--)
2. [Equipe](#--equipe--)
3. [Tecnologias Utilizadas](#--tecnologias-utilizadas--)
4. [Funcionalidades](#--funcionalidades--)
5. [Instalação e Configuração](#--instalação-e-configuração--)
6. [Estrutura do Projeto](#--estrutura-do-projeto--)
7. [Cronograma](#--cronograma--)
8. [Documentação](#--documentação--)
9. [Como Contribuir](#--como-contribuir--)
10. [Licença](#--licença--)
11. [Autores e Agradecimentos](#--autores-e-agradecimentos--)

---

# ** Objetivos **

## ** Objetivo Geral **

Desenvolver um sistema web que otimize e modernize a gestão do almoxarifado da FUNAC.

## ** Objetivos Específicos **

- Implementar controle de entrada e saída de produtos.  
- Registrar movimentações de forma automática e organizada.  
- Centralizar informações em dashboards gerenciais.  
- Reduzir inconsistências comuns em processos manuais.  
- Auxiliar na tomada de decisão com relatórios.  
- Facilitar auditorias internas.

---

# ** Equipe **

| Nome             | Função                   |
|------------------|--------------------------|
| Larissa Vitória  | Desenvolvedora Front-End |
| Naquizia Paulo   | Desenvolvedora Front-End |
| Gabriel Santana  | Desenvolvedor Front-End  |
| Ingrid Morio     | Desenvolvedora Front-End |
| Mateus Silva     | Desenvolvedor Back-End   |
| João Laureano    | Desenvolvedor Back-End   |
| Luiz Henrique    | Desenvolvedor Back-End   |
| Luís Felipe      | Desenvolvedor Back-End   |

---

# ** Tecnologias Utilizadas **

## ** Frontend **
- HTML5  
- CSS3  
- JavaScript  
- Bootstrap 5

## ** Backend **
- Python  
- Django

## ** Banco de Dados **
- SQLite3

## ** Ferramentas **
- Git e GitHub  
- VSCode  

---

# ** Funcionalidades **

- Cadastro de produtos  
- Controle de estoque  
- Registro de entradas e saídas  
- Histórico completo de movimentações  
- Dashboard informativo  
- Relatórios gerenciais  
- Sistema de login e controle de permissões  
- Interface responsiva

---

# ** Instalação e Configuração **

## ** 1. Clone o repositório **
```bash
git clone https://github.com/seu-usuario/seu-repo.git
cd seu-repo
````

## ** 2. Crie o ambiente virtual **

```bash
python -m venv venv
source venv/bin/activate  # Linux / macOS
venv\Scripts\activate     # Windows
```

## ** 3. Instale as dependências **

```bash
pip install -r requirements.txt
```

## ** 4. Execute as migrações **

```bash
python manage.py migrate
```

## ** 5. Crie superusuário (opcional) **

```bash
python manage.py createsuperuser
```

## ** 6. Inicie o servidor **

```bash
python manage.py runserver
```

---

# ** Estrutura do Projeto **

```text
almoxarifado-sistema/
├── almoxarifado/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── estoque/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   ├── validators.py
│   ├── tests.py
│   ├── migrations/
│   ├── static/
│   └── templates/
│
├── static/
├── templates/
├── requirements.txt
└── manage.py
```

---

# ** Cronograma **

| Etapa                      | Status    |
| -------------------------- | --------- |
| Levantamento de Requisitos | Concluído |
| Prototipação               | Concluído |
| Desenvolvimento            | Concluído |
| Testes                     | Concluído |
| Entrega                    | Concluído |

---


---

# ** Licença **

Este projeto está licenciado sob a BSD License.

---

# ** Autores e Agradecimentos **

Agradecimentos à FUNAC, ao IFMT e aos professores orientadores pelo suporte institucional e pela oportunidade de desenvolvimento do projeto.

---

