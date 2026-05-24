# TESTING MANUAL — GKR Data Portal

Manual testing protocol for the GKRP archaeology data portal. Designed for repeated use by multiple testers.

---

## English Version

### 1. Pre-flight Checklist

Before every test session:

1. **Verify the app is running** — open `http://localhost:8080` (or the deployed URL). The home page should show the left navigation panel.
2. **Confirm database connectivity** — the Layers page should load rows without errors.
3. **Note the current language** — the language toggle button (top-right, "EN"/"BG") sets the session language. Record which language you are testing in.
4. **Ensure a fresh session** — open the page in an incognito/private window or clear browser storage before starting.

---

### 2. Authentication & Authorization

| # | Step | Expected Result |
|---|------|-----------------|
| 2.1 | Open `/dev-login` | User list loads. Each row shows `id | email | username | role=… | active=…`. |
| 2.2 | Select an **admin** user, click **Login** | Positive notification: "Session set: user_id=X". Navigate to `/admin`. |
| 2.3 | Open `/admin` | Users table loads. Invite section visible. |
| 2.4 | Click a user row | Dialog opens showing user details (email, username, role, active). |
| 2.5 | Click **Disable** / **Activate** in the dialog | User `is_active` toggles. Table refreshes. |
| 2.6 | Create an invite: enter email, pick role, click **Create Invite** | Link displayed. If SMTP configured: green "sent" notification. If not: yellow "not configured" warning. |
| 2.7 | Open the invite link in a new tab | `/accept-invite` page renders. |
| 2.8 | Enter username + password (twice, matching), click **Activate Account** | Account activated. Redirect to home page. |
| 2.9 | Log in as the newly activated user | User can access data pages but **not** `/admin`. |
| 2.10 | Click **Logout** | Session cleared. Redirect to login. |

**Negative tests:**
- Select no user, click Login → "Select a user" warning.
- Enter non-matching passwords on invite page → "Passwords do not match" warning.
- Use an expired/invalid invite link → "Invalid invite" / "Invite expired" message.

---

### 3. Language Toggle

| # | Step | Expected Result |
|---|------|-----------------|
| 3.1 | On any page, click the language button (top-right) | Page reloads. All labels switch to the alternate language. |
| 3.2 | Toggle back | All labels switch back. |

---

### 4. Data Entry Pages (Layers, Fragments, Ornaments, Finds)

Each data page follows the same pattern: search bar, filter dropdowns, data table, "New" button, row-click editor.

#### 4.1 Layers (`/layers`)

| # | Step | Expected Result |
|---|------|-----------------|
| 4.1.1 | Page loads | Table shows rows (paginated at 25). |
| 4.1.2 | Type text in search bar | Table filters in real-time by site/sector/square/layer. Clear button resets. |
| 4.1.3 | Open any filter dropdown (e.g., Site) | Dropdown lists distinct values from the database. Multi-select with chips. |
| 4.1.4 | Select one or more filter values, then click **Refresh** | Table updates to show only matching rows. |
| 4.1.5 | Clear all filters, click **Refresh** | All rows visible again. |
| 4.1.6 | Click **New Layer** | Dialog opens. "Layer (optional)" select + free-text fields. |
| 4.1.7 | Leave Layer ID empty, fill site/sector/square, click **Save** | Row created. Layer ID auto-inferred from most recent layer. Table refreshes. |
| 4.1.8 | Click a table row | Dialog opens pre-filled with that row's data. |
| 4.1.9 | Edit fields, click **Save** | Changes persisted. Table refreshes. |
| 4.1.10 | Click **Cancel** in the dialog | Dialog closes. No changes. |

#### 4.2 Fragments (`/fragments`)

| # | Step | Expected Result |
|---|------|-----------------|
| 4.2.1 | Page loads | Table shows rows (paginated at 25). |
| 4.2.2 | Search + filter | Same pattern as Layers. |
| 4.2.3 | Click **New Fragment** | Dialog opens with ~30 fields across a 4-column grid. |
| 4.2.4 | Leave required fields (Piece Type, Count) empty, click **Save** | Red notification: "Piece type is required" or "Count is required". No save. |
| 4.2.5 | Fill Piece Type + Count, fill other fields, click **Save** | Row created. Table refreshes. |
| 4.2.6 | Click a row to edit | Dialog opens pre-filled. Edit and save. |

#### 4.3 Ornaments (`/ornaments`)

| # | Step | Expected Result |
|---|------|-----------------|
| 4.3.1 | Page loads | Table shows rows (paginated at 25). |
| 4.3.2 | Search + filter | Same pattern as Layers. |
| 4.3.3 | Click **New Ornament** | Dialog opens. Fragment ID optional (auto-inferred). |
| 4.3.4 | Save with minimal data | Row created. Table refreshes. |
| 4.3.5 | Edit via row click | Dialog opens pre-filled. Edit and save. |

#### 4.4 Finds (`/finds`)

| # | Step | Expected Result |
|---|------|-----------------|
| 4.4.1 | Page loads | Table shows rows (paginated at 25). |
| 4.4.2 | Search + filter | Same pattern as Layers. |
| 4.4.3 | Click **New Find** | Dialog opens. Layer ID optional (auto-inferred). |
| 4.4.4 | Save with minimal data | Row created. Table refreshes. |
| 4.4.5 | Edit via row click | Dialog opens pre-filled. Edit and save. |

---

### 5. Analytics — Table (`/analytics/table`)

| # | Step | Expected Result |
|---|------|-----------------|
| 5.1 | Page loads | Left panel shows query selector, layer filters, limit selector. Center shows empty AG Grid. |
| 5.2 | Click **Run Query** | Grid populates. Status bar shows "Returned X rows (total Y)". |
| 5.3 | Change query selector (q2 / Archaeology) | Layer filter panel visibility toggles. q2 shows filters; finds_arch hides them. |
| 5.4 | Select Site → Sector → Square → Layer (cascade) | Each level filters the next. Invalid selections auto-clear. |
| 5.5 | Apply layer filters, click **Run Query** | Grid reflects filtered results. |
| 5.6 | Change limit (100, 500, 1000, max) | Grid row count changes accordingly. |
| 5.7 | Use column header filters (dropdown) | Filter shows distinct values for that column. Select values to narrow results. |
| 5.8 | Click **Help** button | Help dialog opens with formatted guide content. Close button works. |
| 5.9 | Resize browser window | Grid scrolls horizontally. Column widths preserved. |

---

### 6. Analytics — Chart: Fragments (`/analytics/chart_fragments`)

| # | Step | Expected Result |
|---|------|-----------------|
| 6.1 | Page loads | Three-column layout: filters (left), chart (center), fragment/ornament filters (right). |
| 6.2 | Click **Run Query** | Chart renders (default: Pie chart, grouped by Site). |
| 6.3 | Change **Group By (X-axis)** | Chart re-renders with new x-axis dimension. |
| 6.4 | Select a **Series** dimension | Chart shows grouped bars (one trace per series value). |
| 6.5 | Change **Chart Type** (Bar / Pie / Donut) | Chart re-renders in the selected style. |
| 6.6 | Apply layer filters (Site → Sector → Square → Layer) | Chart re-renders with filtered data. |
| 6.7 | Apply fragment filters (Piecetype, Technology, etc.) | Chart re-renders with filtered data. |
| 6.8 | Apply ornament filters (Primary, Secondary, etc.) | Chart re-renders with filtered data. |
| 6.9 | Click **Download PNG** | Browser downloads `analytics_chart_fragments.png`. |
| 6.10 | Click **Download JPG** | Browser downloads `analytics_chart_fragments.jpg`. |
| 6.11 | Click **Print / Save as PDF** | New tab opens with a printable chart view. |
| 6.12 | Toggle "Enable all rows" | Chart refetches with higher row limit. |
| 6.13 | Click **Help** button | Help dialog opens with chart guide. |

---

### 7. Analytics — Chart: Finds (`/analytics/chart_finds`)

| # | Step | Expected Result |
|---|------|-----------------|
| 7.1 | Page loads | Left panel shows Finds filters. Center shows chart. |
| 7.2 | Click **Run Query** | Chart renders (default: Pie, grouped by Find Type). |
| 7.3 | Change **Group By (X-axis)** | Chart re-renders. |
| 7.4 | Select a **Series** dimension | Grouped bars appear. |
| 7.5 | Change **Chart Type** | Chart re-renders. |
| 7.6 | Apply Finds filters (Find Type, Material, Coin, etc.) | Chart re-renders with filtered data. |
| 7.7 | Download PNG / JPG / PDF | Same behavior as Fragments chart. |
| 7.8 | Toggle "Enable all rows" | Chart refetches with higher row limit. |

---

### 8. Cross-cutting Checks

| # | Check | Expected |
|---|-------|----------|
| 8.1 | Navigate to every page via left sidebar | All pages load without console errors. |
| 8.2 | Refresh any page (F5) | Page re-renders correctly with filters reset to defaults. |
| 8.3 | Open two tabs on different pages | Both tabs remain independent. Language toggle in one tab reloads that tab only. |
| 8.4 | Test on different browsers (Chrome, Firefox) | Layout and functionality consistent. |
| 8.5 | Resize browser to mobile width | Layout degrades gracefully (scrolling, stacking). No broken elements. |
| 8.6 | Check browser console for errors | No red errors. Warnings about missing assets are acceptable. |

---

### 9. Reporting Bugs

When a defect is found:

1. **Record the URL** (e.g., `/analytics/table`).
2. **Record the language** (BG or EN).
3. **Describe the steps** to reproduce (numbered list).
4. **Record expected vs. actual result.**
5. **Screenshot** the page and browser console (F12 → Console tab).
6. **Note the data state** — e.g., "30 layers, 120 fragments in DB."

---

### 10. Session-end Checklist

1. Log out (if logged in).
2. Close the browser.
3. Record test results: pages tested, issues found, data changes made.

---

## Българска версия

### 1. Предварителна проверка

Преди всяка тестова сесия:

1. **Проверете дали приложението работи** — отворете `http://localhost:8080` (или деплойнатия URL). Домашната страница трябва да показва лявото навигационно меню.
2. **Потвърдете връзката с базата данни** — страницата Пластове трябва да зарежда редове без грешки.
3. **Запишете текущия език** — бутонът за превключване (горен десен ъгъл, "EN"/"BG") задава езика на сесията. Запишете на кой език тествате.
4. **Уверете се в чиста сесия** — отворете страницата в режим "инкогнито" или изчистете браузърското съхранение преди началото.

---

### 2. Удостоверяване и оторизация

| # | Стъпка | Очакван резултат |
|---|--------|------------------|
| 2.1 | Отворете `/dev-login` | Зарежда се списък с потребители. Всеки ред показва `id | email | username | role=… | active=…`. |
| 2.2 | Изберете **админ** потребител, кликнете **Вход** | Положително известие: "Session set: user_id=X". Навигация към `/admin`. |
| 2.3 | Отворете `/admin` | Таблица с потребители се зарежда. Секцията за покани е видима. |
| 2.4 | Кликнете върху ред на потребител | Отваря се диалог с детайли (имейл, потребител, роля, активен). |
| 2.5 | Кликнете **Деактивирай** / **Активирай** в диалога | `is_active` на потребителя се превключва. Таблицата се обновява. |
| 2.6 | Създайте покана: въведете имейл, изберете роля, кликнете **Създай покана** | Показва се връзка. Ако SMTP е конфигуриран: зелено известие "изпратен". Ако не: жълто предупреждение. |
| 2.7 | Отворете връзката за покана в нов таб | Страница `/accept-invite` се рендира. |
| 2.8 | Въведете потребителско име + парола (два пъти, съвпадащи), кликнете **Активиране на акаунт** | Акаунтът е активиран. Пренасочване към домашната страница. |
| 2.9 | Влезте като новия потребител | Потребителят може да достъпва данни, но **не и** `/admin`. |
| 2.10 | Кликнете **Изход** | Сесията е изчистена. Пренасочване към входа. |

**Отрицателни тестове:**
- Не изберете потребител, кликнете Вход → предупреждение "Изберете потребител".
- Въведете несъвпадащи пароли на страницата за покана → предупреждение "Паролите не съвпадат".
- Използвайте изтекла/невалидна връзка за покана → съобщение "Невалидна покана" / "Поканата е изтекла".

---

### 3. Превключване на езика

| # | Стъпка | Очакван резултат |
|---|--------|------------------|
| 3.1 | На която и да е страница, кликнете бутона за език (горен десен ъгъл) | Страницата се презарежда. Всички етикети преминават към алтернативния език. |
| 3.2 | Превключете обратно | Всички етикати се връщат. |

---

### 4. Страници за въвеждане на данни (Пластове, Фрагменти, Орнаменти, Находки)

Всяка страница за данни следва един и същ модел: лента за търсене, падащи филтри, таблица с данни, бутон "Нов", редактор при клик върху ред.

#### 4.1 Пластове (`/layers`)

| # | Стъпка | Очакван резултат |
|---|--------|------------------|
| 4.1.1 | Страницата се зарежда | Таблицата показва редове (пагинация 25). |
| 4.1.2 | Въведете текст в лентата за търсене | Таблицата филтрира в реално време. Бутонът за изчистване нулира. |
| 4.1.3 | Отворете всеки филтър (напр. Обект) | Падащото меню показва уникални стойности от базата данни. Мулти-избор с чипсове. |
| 4.1.4 | Изберете стойности, кликнете **Обнови** | Таблицата се актуализира само с съвпадащи редове. |
| 4.1.5 | Изчистете всички филтри, кликнете **Обнови** | Всички редове отново видими. |
| 4.1.6 | Кликнете **Нов Пласт** | Диалог се отваря. "Пласт (по избор)" + полета за свободен текст. |
| 4.1.7 | Оставете ИД на Пласт празно, попълнете обект/сектор/квадрат, кликнете **Запази** | Редът е създаден. ИД-то се извежда автоматично. Таблицата се обновява. |
| 4.1.8 | Кликнете върху ред в таблицата | Диалог се отваря с данните на реда. |
| 4.1.9 | Редактирайте полета, кликнете **Запази** | Промените са запазени. Таблицата се обновява. |
| 4.1.10 | Кликнете **Отказ** в диалога | Диалогът се затваря. Без промени. |

#### 4.2 Фрагменти (`/fragments`)

| # | Стъпка | Очакван резултат |
|---|--------|------------------|
| 4.2.1 | Страницата се зарежда | Таблицата показва редове (пагинация 25). |
| 4.2.2 | Търсене + филтри | Същият модел като Пластове. |
| 4.2.3 | Кликнете **Нов Фрагмент** | Диалог се отваря с ~30 полета в 4-колоночна мрежа. |
| 4.2.4 | Оставете задължителните полета (Тип отломък, Брой) празни, кликнете **Запази** | Червено известие: "Типът отломък е задължителен" или "Броят е задължителен". Запазването не става. |
| 4.2.5 | Попълете Тип отломък + Брой, попълнете други полета, кликнете **Запази** | Редът е създаден. Таблицата се обновява. |
| 4.2.6 | Кликнете върху ред за редактиране | Диалог се отваря с попълнени данни. Редактирайте и запазете. |

#### 4.3 Орнаменти (`/ornaments`)

| # | Стъпка | Очакван резултат |
|---|--------|------------------|
| 4.3.1 | Страницата се зарежда | Таблицата показва редове (пагинация 25). |
| 4.3.2 | Търсене + филтри | Същият модел като Пластове. |
| 4.3.3 | Кликнете **Нов Орнамент** | Диалог се отваря. ИД на фрагмент по избор (автоматично). |
| 4.3.4 | Запазете с минимални данни | Редът е създаден. Таблицата се обновява. |
| 4.3.5 | Редактирайте чрез клик върху ред | Диалог се отваря с попълнени данни. Редактирайте и запазете. |

#### 4.4 Находки (`/finds`)

| # | Стъпка | Очакван резултат |
|---|--------|------------------|
| 4.4.1 | Страницата се зарежда | Таблицата показва редове (пагинация 25). |
| 4.4.2 | Търсене + филтри | Същият модел като Пластове. |
| 4.4.3 | Кликнете **Нова Находка** | Диалог се отваря. ИД на пласт по избор (автоматично). |
| 4.4.4 | Запазете с минимални данни | Редът е създаден. Таблицата се обновява. |
| 4.4.5 | Редактирайте чрез клик върху ред | Диалог се отваря с попълнени данни. Редактирайте и запазете. |

---

### 5. Анализ — Таблица (`/analytics/table`)

| # | Стъпка | Очакван резултат |
|---|--------|------------------|
| 5.1 | Страницата се зарежда | Ляв панел: селектор на запитване, филтри за пластове, лимит. Център: празна AG Grid. |
| 5.2 | Кликнете **Изпълни запитване** | Grid се попълва. Статус барът показва "Върнати X реда (общо Y)". |
| 5.3 | Променете селектора на запитване (q2 / Археология) | Видимостта на панела с филтри за пластове се превключва. q2 показва филтри; finds_arch ги скрива. |
| 5.4 | Изберете Обект → Сектор → Квадрат → Пласт (каскада) | Ниво по ниво филтрира следващото. Невалидни избори се изчистват автоматично. |
| 5.5 | Приложете филтри за пластове, кликнете **Изпълни запитване** | Grid отразява филтрираните резултати. |
| 5.6 | Променете лимита (100, 500, 1000, max) | Броят редове в грида се променя. |
| 5.7 | Използвайте филтрите в заглавието на колона (падащо меню) | Филтърът показва уникални стойности за колоната. Изберете стойности за съкращаване на резултатите. |
| 5.8 | Кликнете бутона **Помощ** | Отваря се диалог с упътване. Бутонът Затвори работи. |
| 5.9 | Оразмерете прозореца на браузъра | Grid-ът се скролира хоризонтално. Ширините на колоните са запазени. |

---

### 6. Анализ — Графика: Фрагменти (`/analytics/chart_fragments`)

| # | Стъпка | Очакван резултат |
|---|--------|------------------|
| 6.1 | Страницата се зарежда | Триколоночен изглед: филтри (ляво), графика (център), филтри за фрагменти/орнаменти (дясно). |
| 6.2 | Кликнете **Изпълни запитване** | Графиката се рендира (по подразбиране: Кръгова, групирана по Обект). |
| 6.3 | Променете **Групирай по (x-ос)** | Графиката се рендира отново с нова x-ос. |
| 6.4 | Изберете **Серия** | Графиката показва групирани стълбове (по един трайс за всяка серия). |
| 6.5 | Променете **Вид графика** (Стълб / Кръг / Поничка) | Графиката се рендира в избрания стил. |
| 6.6 | Приложете филтри за пластове (Обект → Сектор → Квадрат → Пласт) | Графиката се рендира с филтрирани данни. |
| 6.7 | Приложете филтри за фрагменти (Тип отломък, Технология и др.) | Графиката се рендира с филтрирани данни. |
| 6.8 | Приложете филтри за орнаменти (Основно, Вторично и др.) | Графиката се рендира с филтрирани данни. |
| 6.9 | Кликнете **Изтегли PNG** | Браузърът изтегля `analytics_chart_fragments.png`. |
| 6.10 | Кликнете **Изтегли JPG** | Браузърът изтегля `analytics_chart_fragments.jpg`. |
| 6.11 | Кликнете **Печат / Запази като PDF** | Нов таб отваря печатен изглед на графиката. |
| 6.12 | Превключете "Активиране на всички редове" | Графиката презарежда с по-висок лимит. |
| 6.13 | Кликнете бутона **Помощ** | Отваря се диалог с упътване за графиките. |

---

### 7. Анализ — Графика: Находки (`/analytics/chart_finds`)

| # | Стъпка | Очакван резултат |
|---|--------|------------------|
| 7.1 | Страницата се зарежда | Ляв панел: филтри за находки. Център: графика. |
| 7.2 | Кликнете **Изпълни запитване** | Графиката се рендира (по подразбиране: Кръгова, по Вид). |
| 7.3 | Променете **Групирай по (x-ос)** | Графиката се рендира отново. |
| 7.4 | Изберете **Серия** | Появяват се групирани стълбове. |
| 7.5 | Променете **Вид графика** | Графиката се рендира отново. |
| 7.6 | Приложете филтри за находки (Вид, Материал, Монета и др.) | Графиката се рендира с филтрирани данни. |
| 7.7 | Изтеглете PNG / JPG / PDF | Същото поведение като при графиката с фрагменти. |
| 7.8 | Превключете "Активиране на всички редове" | Графиката презарежда с по-висок лимит. |

---

### 8. Общи проверки

| # | Проверка | Очакван резултат |
|---|----------|------------------|
| 8.1 | Навигирайте към всяка страница чрез лявото меню | Всички страници се зареждат без грешки в конзолата. |
| 8.2 | Презаредете която и да е страница (F5) | Страницата се рендира правилно с филтрите нулирани. |
| 8.3 | Отворете два таба на различни страници | И двата таба са независими. Превключването на език в един таб презарежда само този таб. |
| 8.4 | Тествайте в различни браузъри (Chrome, Firefox) | Изгледът и функционалността са последователни. |
| 8.5 | Оразмерете браузъра до мобилен размер | Изгледът се адаптира (скролиране, наслагване). Няма счупени елементи. |
| 8.6 | Проверете конзолата на браузъра за грешки | Няма червени грешки. Предупреждения за липсващи ресурси са допустими. |

---

### 9. Докладване на грешки

Когато откриете дефект:

1. **Запишете URL-а** (напр. `/analytics/table`).
2. **Запишете езика** (BG или EN).
3. **Опишете стъпките** за възпроизвеждане (наброяван списък).
4. **Запишете очакван vs. реален резултат.**
5. **Направете скрийншот** на страницата и конзолата на браузъра (F12 → таб Конзола).
6. **Запишете състоянието на данните** — напр. "30 пласта, 120 фрагмента в базата данни."

---

### 10. Проверка в края на сесията

1. Излезте (ако сте влезли).
2. Затворете браузъра.
3. Запишете резултатите от тестовете: тествани страници, открити проблеми, направени промени в данните.
