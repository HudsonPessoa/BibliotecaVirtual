const grid = document.querySelector("#book-grid");
const searchInput = document.querySelector("#search-input");
const statusFilter = document.querySelector("#status-filter");
const resultsLabel = document.querySelector("#results-label");
const emptyState = document.querySelector("#empty-state");
const errorBanner = document.querySelector("#error-banner");
const bookDialog = document.querySelector("#book-dialog");
const bookForm = document.querySelector("#book-form");
const formError = document.querySelector("#form-error");
const confirmDialog = document.querySelector("#confirm-dialog");

let books = [];
let editingId = null;
let deletingId = null;

const genreClasses = {
  ficção: "cover-fiction",
  fantasia: "cover-fantasy",
  romance: "cover-romance",
  biografia: "cover-biography",
  história: "cover-history",
  tecnologia: "cover-technology",
};

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Não foi possível concluir a operação.");
  return result;
}

async function loadBooks() {
  errorBanner.hidden = true;
  try {
    const result = await request("/api/books");
    books = result.books;
    render();
  } catch (error) {
    errorBanner.textContent = error.message;
    errorBanner.hidden = false;
  }
}

function createElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function render() {
  const search = searchInput.value.trim().toLocaleLowerCase("pt-BR");
  const status = statusFilter.value;
  const filtered = books.filter((book) => {
    const matchesSearch = !search || [book.title, book.author, book.genre]
      .some((value) => value.toLocaleLowerCase("pt-BR").includes(search));
    return matchesSearch && (!status || book.status === status);
  });

  document.querySelector("#total-count").textContent = books.length;
  document.querySelector("#available-count").textContent =
    books.filter((book) => book.status === "available").length;
  document.querySelector("#borrowed-count").textContent =
    books.filter((book) => book.status === "borrowed").length;

  resultsLabel.textContent = `${filtered.length} ${filtered.length === 1 ? "livro encontrado" : "livros encontrados"}`;
  grid.replaceChildren(...filtered.map(createBookCard));
  emptyState.hidden = filtered.length !== 0;
  if (books.length === 0) {
    document.querySelector("#empty-title").textContent = "Sua estante está esperando";
    document.querySelector("#empty-description").textContent = "Adicione o primeiro livro e comece a montar seu acervo.";
  } else {
    document.querySelector("#empty-title").textContent = "Nenhum livro encontrado";
    document.querySelector("#empty-description").textContent = "Experimente buscar por outro título ou autor.";
  }
}

function createBookCard(book) {
  const card = createElement("article", "book-card");
  const cover = createElement("div", `cover ${genreClasses[book.genre.toLocaleLowerCase("pt-BR")] || "cover-default"}`);
  cover.setAttribute("aria-label", `Capa ilustrativa de ${book.title}`);
  const coverContent = createElement("div", "cover-content");
  coverContent.append(
    createElement("span", "cover-label", book.genre),
    createElement("span", "cover-title", book.title),
    createElement("span", "cover-author", book.author),
  );
  cover.append(coverContent);

  const info = createElement("div", "book-info");
  info.append(
    createElement("span", "genre-badge", book.genre),
    createElement("h3", "book-title", book.title),
    createElement("p", "book-author", book.author),
  );

  const meta = createElement("div", "book-meta");
  meta.append(createElement("span", "", String(book.year)));
  meta.append(createElement(
    "span",
    `availability${book.status === "borrowed" ? " borrowed" : ""}`,
    book.status === "available" ? "Disponível" : "Em leitura",
  ));
  const actions = createElement("div", "card-actions");
  const editButton = createElement("button", "icon-button", "✎");
  editButton.type = "button";
  editButton.setAttribute("aria-label", `Editar ${book.title}`);
  editButton.addEventListener("click", () => openEditDialog(book));
  const deleteButton = createElement("button", "icon-button delete-book", "×");
  deleteButton.type = "button";
  deleteButton.setAttribute("aria-label", `Remover ${book.title}`);
  deleteButton.addEventListener("click", () => openDeleteDialog(book));
  actions.append(editButton, deleteButton);
  meta.append(actions);
  info.append(meta);
  card.append(cover, info);
  return card;
}

function openCreateDialog() {
  editingId = null;
  bookForm.reset();
  formError.hidden = true;
  document.querySelector("#dialog-title").textContent = "Adicionar livro";
  document.querySelector("#save-book-button").textContent = "Salvar livro";
  bookDialog.showModal();
  bookForm.elements.title.focus();
}

function openEditDialog(book) {
  editingId = book.id;
  bookForm.reset();
  formError.hidden = true;
  document.querySelector("#dialog-title").textContent = "Editar livro";
  document.querySelector("#save-book-button").textContent = "Salvar alterações";
  for (const [field, value] of Object.entries(book)) {
    if (bookForm.elements[field]) bookForm.elements[field].value = value ?? "";
  }
  bookDialog.showModal();
  bookForm.elements.title.focus();
}

function openDeleteDialog(book) {
  deletingId = book.id;
  document.querySelector("#confirm-description").textContent =
    `“${book.title}” será removido permanentemente do acervo.`;
  confirmDialog.showModal();
}

document.querySelector("#add-book-button").addEventListener("click", openCreateDialog);
document.querySelectorAll(".close-dialog").forEach((button) => {
  button.addEventListener("click", () => bookDialog.close());
});
document.querySelector("#clear-filters-button").addEventListener("click", () => {
  searchInput.value = "";
  statusFilter.value = "";
  render();
});
searchInput.addEventListener("input", render);
statusFilter.addEventListener("change", render);

document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    searchInput.focus();
  }
});

bookForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  formError.hidden = true;
  const formData = new FormData(bookForm);
  const payload = Object.fromEntries(formData.entries());
  payload.year = Number(payload.year);
  const path = editingId === null ? "/api/books" : `/api/books/${editingId}`;
  const method = editingId === null ? "POST" : "PUT";
  const saveButton = document.querySelector("#save-book-button");
  saveButton.disabled = true;
  try {
    await request(path, { method, body: JSON.stringify(payload) });
    bookDialog.close();
    await loadBooks();
  } catch (error) {
    formError.textContent = error.message;
    formError.hidden = false;
  } finally {
    saveButton.disabled = false;
  }
});

document.querySelector("#confirm-delete-button").addEventListener("click", async (event) => {
  event.preventDefault();
  const button = event.currentTarget;
  button.disabled = true;
  try {
    await request(`/api/books/${deletingId}`, { method: "DELETE" });
    confirmDialog.close();
    await loadBooks();
  } catch (error) {
    confirmDialog.close();
    errorBanner.textContent = error.message;
    errorBanner.hidden = false;
  } finally {
    button.disabled = false;
    deletingId = null;
  }
});

loadBooks();
