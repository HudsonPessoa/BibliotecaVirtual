# Entre Páginas — Biblioteca Virtual

Sistema web MVC para gerenciar um acervo de livros. Permite cadastrar, consultar, editar e remover livros, pesquisar por título, autor ou gênero e filtrar títulos disponíveis ou em leitura.

## Requisitos

- Python 3.9 ou superior.
- Não são necessárias dependências externas: o servidor HTTP, a API e a persistência usam a biblioteca padrão do Python e SQLite.

## Como executar

Na pasta do projeto, execute:

```powershell
py app.py
```

Abra <http://127.0.0.1:8000>. O banco SQLite é criado automaticamente em `data/biblioteca.db`, com alguns livros de exemplo. Para encerrar o servidor, pressione `Ctrl+C`.

Para mudar a porta ou o endereço:

```powershell
$env:BIBLIOTECA_PORT = "8080"
$env:BIBLIOTECA_HOST = "127.0.0.1"
py app.py
```

Para escolher outro caminho para o arquivo do banco de dados, defina `BIBLIOTECA_DB_PATH`.

## Arquitetura MVC

- **Model** (`models/book.py` e `models/book_repository.py`): representa os livros e gerencia a persistência em SQLite.
- **Controller** (`controllers/book_controller.py`): valida entradas, aplica filtros e conecta as rotas às operações do modelo.
- **View** (`static/pagina-inicial.html`, `static/estilos.css` e `static/aplicacao.js`): interface responsiva para o catálogo e os formulários de cadastro, edição e remoção.
- **Servidor** (`app.py`): entrega a interface estática e expõe a API HTTP.

## API

Todas as respostas da API usam JSON. Os campos do livro são `title`, `author`, `genre`, `year`, `isbn`, `description` e `status`; a disponibilidade aceita `available` ou `borrowed`.

| Método | Rota | Operação |
|---|---|---|
| `GET` | `/api/books` | Consulta o acervo |
| `GET` | `/api/books?search=termo&genre=Romance&status=available` | Pesquisa e filtra livros |
| `GET` | `/api/books/{id}` | Consulta um livro |
| `POST` | `/api/books` | Cadastra um livro |
| `PUT` | `/api/books/{id}` | Edita um livro |
| `DELETE` | `/api/books/{id}` | Remove um livro |

O ISBN é opcional, mas não pode se repetir. Título, autor, gênero, ano e disponibilidade são obrigatórios.

## Testes

```powershell
py -m unittest discover -s tests -v
```
