"""Shared helpers/constants for Analytics NiceGUI pages."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from nicegui import ui

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.ui.repository.analytics_repo import (
    AnalyticsResult,
    query_finds,
    query_finds_archaeology,
    query_q2_layers_fragments_ornaments,
)

LOCALE: dict[str, str] = {
    # --- Navigation ---
    "nav_navigation": "Навигация",
    "nav_layers": "Пластове",
    "nav_fragments": "Фрагменти",
    "nav_ornaments": "Орнаменти",
    "nav_admin": "Админ",
    "nav_finds": "Находки",
    "nav_analytics": "Анализ",
    "nav_welcome_title": "GKR Портал — Вход на Данни",
    "nav_welcome_text": "Използвайте връзките от лявата навигация. Тази фаза реализира CRUD страници.",
    # --- Page titles ---
    "title_layers": "Пластове (tbllayers)",
    "title_fragments": "Фрагменти (tblfragments)",
    "title_ornaments": "Орнаменти (tblornaments)",
    "title_finds": "Находки (finds)",
    "title_admin": "Админ",
    "title_analytics": "Анализ",
    "title_analytics_chart": "Анализ — Графика",
    "title_analytics_chart_fragments": "Анализ — Графика: Фрагменти",
    "title_analytics_chart_finds": "Анализ — Графика: Находки",
    "title_analytics_table": "Анализ — Таблица",
    "title_accept_invite": "Приемане на покана",
    "title_register": "Регистрацията е забранена",
    "title_register_text": "Достъпът е само по покана. Моля, свържете се с администратора.",
    "title_dev_login": "DEV Вход (задава session user_id)",
    "title_dev_login_text": "След като влезете, отворете **/admin** за тестване.",
    # --- Panels ---
    "panel_query_filters": "Запитване и Филтри",
    "panel_chart": "Графика",
    "panel_table": "Таблица (преместване)",
    "panel_fragments": "Фрагменти",
    "panel_ornaments": "Орнаменти",
    # --- Buttons ---
    "btn_chart_view": "Изглед Графика",
    "btn_table_view": "Изглед Таблица",
    "btn_chart_fragments": "Изглед графика — Фрагменти",
    "btn_chart_finds": "Изглед графика — Находки",
    "btn_run_query": "Изпълни запитване",
    "btn_refresh": "Обнови",
    "btn_new_layer": "Нов Пласт",
    "btn_new_fragment": "Нов Фрагмент",
    "btn_new_ornament": "Нов Орнамент",
    "btn_new_find": "Нова Находка",
    "btn_cancel": "Отказ",
    "btn_save": "Запази",
    "btn_create_invite": "Създай покана",
    "btn_close": "Затвори",
    "btn_disable": "Деактивирай",
    "btn_activate": "Активирай",
    "btn_login": "Вход като избран потребител",
    "btn_logout": "Изход (изчистване на сесията)",
    "btn_activate_account": "Активиране на акаунт",
    "btn_download_png": "Изтегли PNG",
    "btn_download_jpg": "Изтегли JPG",
    "btn_print_pdf": "Печат / Запази като PDF",
    # --- Form labels (UI-facing, not internal column names) ---
    "label_predefined_query": "Предварително дефинирано запитване",
    "label_limit": "Лимит",
    "label_site": "Обект",
    "label_sector": "Сектор",
    "label_square": "Квадрат",
    "label_layer": "Пласт",
    "label_layertype": "Вид пласт",
    "label_layername": "Име на пласт",
    "label_stratum": "Стратум",
    "label_level": "Ниво",
    "label_structure": "Структура",
    "label_color1": "Цвят 1",
    "label_color2": "Цвят 2",
    "label_layer_optional": "Пласт (по избор)",
    "label_fragment_optional": "Фрагмент (по избор)",
    "label_email": "Имейл",
    "label_role": "Роля",
    "label_group_by": "Групирай по (x-ос)",
    "label_series": "Серия (групиране)",
    "label_chart_type": "Вид графика",
    "label_select_user": "Изберете потребител за влизане",
    "label_choose_username": "Изберете потребителско име",
    "label_choose_password": "Изберете парола",
    "label_repeat_password": "Повторете паролата",
    "label_invite_link": "Връзка за покана",
    "label_year": "Година",
    "label_inv_no": "Инв. бр.",
    "label_find_type": "Вид",
    "label_material": "Материал",
    "label_description": "Описание",
    "label_coin": "Монета",
    "label_denomination": "Деноминация",
    "label_mint": "Монетня",
    "label_dimensions_cm": "Размери (см)",
    "label_weight_g": "Тегло (г)",
    "label_depth_m": "Дълбочина (м)",
    "label_context": "Контекст",
    "label_coord_north_m": "Коорд. север (м)",
    "label_coord_east_m": "Коорд. изток (м)",
    "label_photo": "Фото",
    "label_drw_link": "Връзка чертеж",
    "label_entered_by": "Записан от",
    # --- Fragment filter labels (display names — internal keys stay as column names) ---
    "frag_piecetype": "Тип Отломък",
    "frag_technology": "Технология",
    "frag_baking": "Печене",
    "frag_color_primary": "Цвят / Основен цвят",
    "frag_covering": "Покритие",
    "frag_surface": "Повърхност",
    "frag_wall_thickness": "Дебелина на стената",
    "frag_handle_type": "Вид дръжка",
    "frag_handle_size": "Размер на дръжката",
    "frag_bottom_type": "Вид дъно",
    "frag_category": "Категория",
    "frag_form": "Форма",
    "frag_type": "Тип",
    "frag_subtype": "Подтип",
    "frag_variant": "Вариант",
    "frag_primary": "Основно",
    "frag_secondary": "Вторично",
    "frag_tertiary": "Третично",
    "frag_quarternary": "Четвъртично",
    "frag_color_color1": "Цвят / color1",
    "frag_encrust_color": "Цвят на инкрустацията",
    # --- Ornament filter labels ---
    "orn_primary": "Основно",
    "orn_secondary": "Вторично",
    "orn_tertiary": "Третично",
    "orn_quarternary": "Четвъртично",
    "orn_color_color1": "Цвят / color1",
    "orn_encrust_color": "Цвят на инкрустацията",
    # --- Table column headers ---
    "col_id": "ИД",
    "col_layer_id": "ИД Пласт",
    "col_piecetype": "Тип Отломък",
    "col_fragmenttype": "Вид фрагмент",
    "col_technology": "Технология",
    "col_baking": "Печене",
    "col_primary": "Основно",
    "col_secondary": "Вторично",
    "col_tertiary": "Третично",
    "col_count": "Брой",
    "col_inventory": "Инвентарен №",
    "col_image_url": "URL Изображение",
    "col_fragment_id": "ИД фрагмент",
    "col_location": "Местоположение",
    "col_primary_": "Основно",
    "col_color1": "Цвят1",
    "col_color2": "Цвят2",
    "col_username": "Потребител",
    "col_invited": "Поканен",
    "col_invite_expires": "Покана изтича",
    "col_year": "Година",
    "col_find_type": "Вид",
    "col_material": "Материал",
    "col_description": "Описание",
    "col_coin": "Монета",
    "col_mint": "Монетня",
    "col_depth_m": "Дълбочина",
    "col_context": "Контекст",
    "col_coord_north_m": "Корд. С",
    "col_coord_east_m": "Корд. И",
    "col_photo": "Фото",
    # --- Dialogs ---
    "dialog_edit_layer": "Редактиране на Пласт",
    "dialog_create_layer": "Създаване на Пласт",
    "dialog_edit_fragment": "Редактиране на фрагмент",
    "dialog_create_fragment": "Създаване на фрагмент",
    "dialog_edit_ornament": "Редактиране на Орнамент",
    "dialog_create_ornament": "Създаване на Орнамент",
    "dialog_edit_find": "Редактиране на находка",
    "dialog_create_find": "Нова находка",
    "dialog_user_actions": "Действия за потребител {uid}",
    "dialog_layer_hint": "Ако **ИД на Пласт** е празно, ще бъде изведено като **най-новият пласт** (паритет с керамичния работен процес).",
    "dialog_fragment_hint": "Ако **ИД на Пласт** е празно, ще бъде изведено като **най-новият пласт** (паритет с керамичния работен процес).",
    "dialog_ornament_hint": "Ако **ИД на фрагмент** е празно, ще бъде изведено като **най-новият фрагмент** (паритет с керамичния работен процес).",
    # --- Queries ---
    "query_filter2": "Филтър #2 (Пластове + Фрагменти + Орнаменти)",
    "query_finds": "Открития (tblfinds)",
    "query_archaeology": "Археологически находки (finds)",
    # --- Chart controls ---
    "chart_type_bar": "Стълб",
    "chart_type_pie": "Кръг",
    "chart_type_donut": "Поничка",
    "chart_help_label": "Упътване",
    "chart_help_close": "Затвори",
    "chart_help_groupby": "Основната размерност, по която графиката е групирана (напр. Обект, Сектор, Квадрат).",
    "chart_help_series": "По избор: разделя стълбовете на групирани следи по втора размерност (напр. Тип Отломък, Технология, Повърхност).",
    "chart_help_chart_type": "Стълб показва групирани стълбове, Кръг/Поничка показват пропорции.",
    "chart_help_groupby_finds": "Основната размерност, по която графиката е групирана.",
    "chart_help_series_finds": "По избор: разделя стълбовете по втора размерност.",
    "chart_help_chart_type_finds": "Стълб/Кръг/Поничка.",
    # --- Help / status messages ---
    "status_no_results": "Няма резултати за текущите филтри.",
    "status_returned": "Върнати {count} реда (общо {total}).",
    "status_no_results_query": "Няма резултати ({query_id})",
    "tip_filter_header": "Съвет: използвайте филтрите в заглавието (падащото меню показва наличните стойности).",
    "chart_fetch_info": "Графиките зареждат до 25 000 реда за изграждане на топ 30 кофи. Това е достатъчно за колони с до ~40 категории; ако филтрирате към малък поднабор (напр. един обект и сектор) лимитът може да изреже редки категории.",
    "limit_max_info": "Използвайте 'max' за зареждане на всички съвпадащи редове (до 100 000).",
    "enable_all_rows": "Активиране на всички редове за малък поднабор",
    "toggle_on": "Вкл",
    "toggle_off": "Изкл",
    # --- Search ---
    "search_layers": "Търсене (обект/сектор/квадрат/пласт)",
    "search_fragments": "Търсене (инвентарен бр./бележка/тип фрагмент/вид фрагмент/технология)",
    "search_ornaments": "Търсене (местоположение/основно/вторично/третично)",
    "search_finds": "Търсене (описание/тип/материал/инв. бр.)",
    # --- Notifications ---
    "notify_email_required": "Имейлът е задължителен",
    "notify_invite_created": "Поканата е създадена. Копирайте и изпратете тази връзка:",
    "notify_invite_email_sent": "Поканата е изпратена чрез SMTP",
    "notify_smtp_not_configured": "SMTP не е конфигуриран; връзката е показана за ръчно изпращане",
    "notify_piecetype_required": "Типът отломък е задължителен",
    "notify_count_required": "Броят е задължителен",
    "notify_passwords_no_match": "Паролите не съвпадат",
    "notify_account_activated": "Акаунтът е активиран. Можете да влезете сега.",
    "notify_select_user": "Изберете потребител",
    "notify_session_set": "Сесията е зададена: user_id={user_id}",
    "notify_session_cleared": "Сесията е изчистена",
    "notify_missing_token": "Липсва токен",
    "notify_invalid_token": "Невалиден токен",
    "notify_invite_expired": "Поканата е изтекла",
    "notify_no_users": "Няма намерени потребители в tblregistered",
    "notify_invalid_invite_link": "Невалидна връзка за покана",
    "notify_invalid_invite": "Невалидна покана",
    "notify_invite_expired_text": "Поканата е изтекла. Моля, поискайте нова от администратора.",
    "notify_username_required": "Потребителското име е задължително",
    # --- Admin user dialog ---
    "admin_email": "Имейл",
    "admin_username": "Потребител",
    "admin_role": "Роля",
    "admin_active": "Активен",
    "admin_users": "Потребители",
    # --- Other ---
    "other_invite_created_text": "Поканата е създадена. Копирайте и изпратете тази връзка:",
    "other_invite_body": "Бяхте поканени.\n\nОтворете тази връзка, за да активирате акаунта си:\n{link}\n\nТази връзка изтича след {ttl} часа.",
    "other_access_by_invite": "Достъпът е само по покана. Моля, свържете се с администратора.",
    "other_create_user_first": "Създайте потребител (или покана) първо, след което се върнете.",
    # --- English translations (EN) ---
    "nav_navigation_en": "Navigation",
    "nav_layers_en": "Layers",
    "nav_fragments_en": "Fragments",
    "nav_ornaments_en": "Ornaments",
    "nav_admin_en": "Admin",
    "nav_finds_en": "Finds",
    "nav_analytics_en": "Analytics",
    "nav_welcome_title_en": "GKR Data Portal — Login",
    "nav_welcome_text_en": "Use the links in the left navigation. This phase implements CRUD pages.",
    "title_layers_en": "Layers (tbllayers)",
    "title_fragments_en": "Fragments (tblfragments)",
    "title_ornaments_en": "Ornaments (tblornaments)",
    "title_finds_en": "Finds (finds)",
    "title_admin_en": "Admin",
    "title_analytics_en": "Analytics",
    "title_analytics_chart_en": "Analytics — Chart",
    "title_analytics_chart_fragments_en": "Analytics — Chart: Fragments",
    "title_analytics_chart_finds_en": "Analytics — Chart: Finds",
    "title_analytics_table_en": "Analytics — Table",
    "title_accept_invite_en": "Accept Invite",
    "title_register_en": "Registration is disabled",
    "title_register_text_en": "Access is by invitation only. Please contact the administrator.",
    "title_dev_login_en": "DEV Login (sets session user_id)",
    "title_dev_login_text_en": "After logging in, open **/admin** for testing.",
    "panel_query_filters_en": "Query & Filters",
    "panel_chart_en": "Chart",
    "panel_table_en": "Table (move)",
    "panel_fragments_en": "Fragments",
    "panel_ornaments_en": "Ornaments",
    "btn_chart_view_en": "Chart View",
    "btn_table_view_en": "Table View",
    "btn_chart_fragments_en": "Chart View — Fragments",
    "btn_chart_finds_en": "Chart View — Finds",
    "btn_run_query_en": "Run Query",
    "btn_refresh_en": "Refresh",
    "btn_new_layer_en": "New Layer",
    "btn_new_fragment_en": "New Fragment",
    "btn_new_ornament_en": "New Ornament",
    "btn_new_find_en": "New Find",
    "btn_cancel_en": "Cancel",
    "btn_save_en": "Save",
    "btn_create_invite_en": "Create Invite",
    "btn_close_en": "Close",
    "btn_disable_en": "Disable",
    "btn_activate_en": "Activate",
    "btn_login_en": "Login as selected user",
    "btn_logout_en": "Logout (clear session)",
    "btn_activate_account_en": "Activate Account",
    "btn_download_png_en": "Download PNG",
    "btn_download_jpg_en": "Download JPG",
    "btn_print_pdf_en": "Print / Save as PDF",
    "label_predefined_query_en": "Predefined Query",
    "label_limit_en": "Limit",
    "label_site_en": "Site",
    "label_sector_en": "Sector",
    "label_square_en": "Square",
    "label_layer_en": "Layer",
    "label_layertype_en": "Layer Type",
    "label_layername_en": "Layer Name",
    "label_stratum_en": "Stratum",
    "label_level_en": "Level",
    "label_structure_en": "Structure",
    "label_color1_en": "Color 1",
    "label_color2_en": "Color 2",
    "label_layer_optional_en": "Layer (optional)",
    "label_fragment_optional_en": "Fragment (optional)",
    "label_email_en": "Email",
    "label_role_en": "Role",
    "label_group_by_en": "Group By (X-axis)",
    "label_series_en": "Series (grouping)",
    "label_chart_type_en": "Chart Type",
    "label_select_user_en": "Select user to login as",
    "label_choose_username_en": "Choose username",
    "label_choose_password_en": "Choose password",
    "label_repeat_password_en": "Repeat password",
    "label_invite_link_en": "Invite link",
    "label_year_en": "Year",
    "label_inv_no_en": "Inv. No.",
    "label_find_type_en": "Type",
    "label_material_en": "Material",
    "label_description_en": "Description",
    "label_coin_en": "Coin",
    "label_denomination_en": "Denomination",
    "label_mint_en": "Mint",
    "label_dimensions_cm_en": "Dimensions (cm)",
    "label_weight_g_en": "Weight (g)",
    "label_depth_m_en": "Depth (m)",
    "label_context_en": "Context",
    "label_coord_north_m_en": "Coord. North (m)",
    "label_coord_east_m_en": "Coord. East (m)",
    "label_photo_en": "Photo",
    "label_drw_link_en": "Drawing link",
    "label_entered_by_en": "Entered by",
    "frag_piecetype_en": "Piece Type",
    "frag_technology_en": "Technology",
    "frag_baking_en": "Baking",
    "frag_color_primary_en": "Color / Primary Color",
    "frag_covering_en": "Covering",
    "frag_surface_en": "Surface",
    "frag_wall_thickness_en": "Wall Thickness",
    "frag_handle_type_en": "Handle Type",
    "frag_handle_size_en": "Handle Size",
    "frag_bottom_type_en": "Bottom Type",
    "frag_category_en": "Category",
    "frag_form_en": "Form",
    "frag_type_en": "Type",
    "frag_subtype_en": "Subtype",
    "frag_variant_en": "Variant",
    "frag_primary_en": "Primary",
    "frag_secondary_en": "Secondary",
    "frag_tertiary_en": "Tertiary",
    "frag_quarternary_en": "Quaternary",
    "frag_color_color1_en": "Color / color1",
    "frag_encrust_color_en": "Encrustation Color",
    "orn_primary_en": "Primary",
    "orn_secondary_en": "Secondary",
    "orn_tertiary_en": "Tertiary",
    "orn_quarternary_en": "Quaternary",
    "orn_color_color1_en": "Color / color1",
    "orn_encrust_color_en": "Encrustation Color",
    "col_id_en": "ID",
    "col_layer_id_en": "Layer ID",
    "col_piecetype_en": "Piece Type",
    "col_fragmenttype_en": "Fragment Type",
    "col_technology_en": "Technology",
    "col_baking_en": "Baking",
    "col_primary_en": "Primary",
    "col_secondary_en": "Secondary",
    "col_tertiary_en": "Tertiary",
    "col_count_en": "Count",
    "col_inventory_en": "Inventory No.",
    "col_image_url_en": "Image URL",
    "col_fragment_id_en": "Fragment ID",
    "col_location_en": "Location",
    "col_primary__en": "Primary",
    "col_color1_en": "Color1",
    "col_color2_en": "Color2",
    "col_username_en": "User",
    "col_invited_en": "Invited",
    "col_invite_expires_en": "Invite Expires",
    "col_year_en": "Year",
    "col_find_type_en": "Type",
    "col_material_en": "Material",
    "col_description_en": "Description",
    "col_coin_en": "Coin",
    "col_mint_en": "Mint",
    "col_depth_m_en": "Depth",
    "col_context_en": "Context",
    "col_coord_north_m_en": "Coord. N",
    "col_coord_east_m_en": "Coord. E",
    "col_photo_en": "Photo",
    "dialog_edit_layer_en": "Edit Layer",
    "dialog_create_layer_en": "Create Layer",
    "dialog_edit_fragment_en": "Edit Fragment",
    "dialog_create_fragment_en": "Create Fragment",
    "dialog_edit_ornament_en": "Edit Ornament",
    "dialog_create_ornament_en": "Create Ornament",
    "dialog_edit_find_en": "Edit Find",
    "dialog_create_find_en": "New Find",
    "dialog_user_actions_en": "Actions for user {uid}",
    "dialog_layer_hint_en": "If **Layer ID** is empty, it will be inferred as the **most recent layer** (parity with ceramic workflow).",
    "dialog_fragment_hint_en": "If **Layer ID** is empty, it will be inferred as the **most recent layer** (parity with ceramic workflow).",
    "dialog_ornament_hint_en": "If **Fragment ID** is empty, it will be inferred as the **most recent fragment** (parity with ceramic workflow).",
    "query_filter2_en": "Filter #2 (Layers + Fragments + Ornaments)",
    "query_finds_en": "Finds (tblfinds)",
    "query_archaeology_en": "Archaeological Finds (finds)",
    "chart_type_bar_en": "Bar",
    "chart_type_pie_en": "Pie",
    "chart_type_donut_en": "Donut",
    "chart_help_label_en": "Help",
    "chart_help_close_en": "Close",
    "chart_help_groupby_en": "The main dimension by which the chart is grouped (e.g. Site, Sector, Square).",
    "chart_help_series_en": "Optional: split bars into grouped traces by a second dimension (e.g. Piece Type, Technology, Surface).",
    "chart_help_chart_type_en": "Bar shows grouped bars, Pie/Donut show proportions.",
    "chart_help_groupby_finds_en": "The main dimension by which the chart is grouped.",
    "chart_help_series_finds_en": "Optional: split bars by a second dimension.",
    "chart_help_chart_type_finds_en": "Bar/Pie/Donut.",
    "status_no_results_en": "No results for current filters.",
    "status_returned_en": "Returned {count} rows (total {total}).",
    "status_no_results_query_en": "No results ({query_id})",
    "tip_filter_header_en": "Tip: use the filters in the header (dropdown shows available values).",
    "chart_fetch_info_en": "Charts load up to 25,000 rows to build top 30 buckets. This is enough for columns with up to ~40 categories; if you filter to a small subset (e.g. one site and sector) the limit may cut rare categories.",
    "limit_max_info_en": "Use 'max' to load all matching rows (up to 100,000).",
    "enable_all_rows_en": "Enable all rows for a small subset",
    "toggle_on_en": "On",
    "toggle_off_en": "Off",
    "search_layers_en": "Search (site/sector/square/layer)",
    "search_fragments_en": "Search (inv. no./note/fragment type/fragment kind/technology)",
    "search_ornaments_en": "Search (location/primary/secondary/tertiary)",
    "search_finds_en": "Search (description/type/material/inv. no.)",
    "notify_email_required_en": "Email is required",
    "notify_invite_created_en": "Invite created. Copy and send this link:",
    "notify_invite_email_sent_en": "Invite sent via SMTP",
    "notify_smtp_not_configured_en": "SMTP not configured; link shown for manual sending",
    "notify_piecetype_required_en": "Piece type is required",
    "notify_count_required_en": "Count is required",
    "notify_passwords_no_match_en": "Passwords do not match",
    "notify_account_activated_en": "Account activated. You can login now.",
    "notify_select_user_en": "Select a user",
    "notify_session_set_en": "Session set: user_id={user_id}",
    "notify_session_cleared_en": "Session cleared",
    "notify_missing_token_en": "Token missing",
    "notify_invalid_token_en": "Invalid token",
    "notify_invite_expired_en": "Invite expired",
    "notify_no_users_en": "No users found in tblregistered",
    "notify_invalid_invite_link_en": "Invalid invite link",
    "notify_invalid_invite_en": "Invalid invite",
    "notify_invite_expired_text_en": "The invite has expired. Please request a new one from the administrator.",
    "notify_username_required_en": "Username is required",
    "admin_email_en": "Email",
    "admin_username_en": "Username",
    "admin_role_en": "Role",
    "admin_active_en": "Active",
    "admin_users_en": "Users",
    "other_invite_created_text_en": "Invite created. Copy and send this link:",
    "other_invite_body_en": "You have been invited.\n\nOpen this link to activate your account:\n{link}\n\nThis link expires in {ttl} hours.",
    "other_access_by_invite_en": "Access is by invitation only. Please contact the administrator.",
    "other_create_user_first_en": "Create a user (or invite) first, then return.",
}


def _query_options() -> dict[str, str]:
    """Build QUERY_OPTIONS respecting the current language."""
    from gkrp_data_portal.ui.lang import t

    return {
        t("query_filter2"): "q2",
        t("query_archaeology"): "finds_arch",
    }


QUERY_OPTIONS: dict[str, str] = _query_options()

# Routes for the split chart pages
CHART_FRAGMENTS_ROUTE = "/analytics/chart_fragments"
CHART_FINDS_ROUTE = "/analytics/chart_finds"

DEFAULT_LIMIT = 500

TABLE_MAX_LIMIT = 100000  # table UI cap
CHART_MAX_FETCH = 25000  # chart safety cap (top-N buckets don't benefit from >25k rows)

# Client-side helpers for Plotly image export / resize.
# NiceGUI loads plotly.js as an ES module ("nicegui-plotly") that is never
# attached to window, and element DOM ids are prefixed with "c".
PLOTLY_EXPORT_JS = """
window.__gkrpPlotly = () =>
  import('nicegui-plotly').then((m) => (window.Plotly = m.Plotly));
window.__gkrpPlotlyEl = (id) => {
  const el = document.getElementById('c' + id);
  return el ? (el.querySelector('.js-plotly-plot') || el) : null;
};
window.__gkrpPlotlyDownload = (id, format, filename) =>
  window.__gkrpPlotly().then((P) => {
    const gd = window.__gkrpPlotlyEl(id);
    if (gd) P.downloadImage(gd, { format, filename, height: 650, width: 1100 });
  }).catch(() => {});
window.__gkrpPlotlyResize = (id) =>
  window.__gkrpPlotly().then((P) => {
    const gd = window.__gkrpPlotlyEl(id);
    if (gd) { P.Plots.resize(gd); P.redraw(gd); }
  }).catch(() => {});
"""


def register_plotly_export_js() -> None:
    """Expose client-side helpers for Plotly chart image export and resize.

    Must run on the same client before the download/resize callbacks fire.
    The module import is cached by the browser, so repeat calls are cheap.
    """
    ui.run_javascript(PLOTLY_EXPORT_JS)


_UI_HIDDEN_COLUMNS = frozenset(
    {
        # --- Audit / internal timestamps ---
        "l_recordenteredon",
        "l_recordenteredby",
        "l_recordcreatedby",
        "l_recordcreatedon",
        "f_recordenteredon",
        "f_recordenteredby",
        "f_recordcreatedby",
        "f_recordcreatedon",
        "o_recordenteredon",
        "fi_recordenteredon",
        "fi_recordenteredby",
        "fi_recordcreatedon",
        "fi_recordcreatedby",
        # --- Layer internal / low-utility ---
        "l_level",
        "l_structure",
        "l_includes",
        "l_color1",
        "l_color2",
        "l_description",
        "l_akb_num",
        "l_layerid",
        "l_layertype",
        "l_stratum",
        "l_parentid",
        "l_photos",
        "l_drawings",
        "l_handfragments",
        "l_wheelfragment",
        "l_layername",
        "l_context",
        # --- Fragment internal / low-utility ---
        "f_fragmentid",
        "f_locationid",
        "f_outline",
        "f_speed",
        "f_recrodenteredby",
        "f_topsize",
        "f_necksize",
        "f_bodysize",
        "f_bottomsize",
        "f_dishheight",
        "f_composition",
        "f_parallels",
        "f_decoration",
        "f_image",
        "f_count",
        "f_fragmenttype",
        "f_fract",
        "f_onepot",
        "f_handlesize",
        "f_img_url",
        "f_image_url",
        "f_inventory",
        "fi_image_url",
        "f_includesconc",
        "f_includessize",
        "f_includestype",
        "f_secondarycolor",
        # --- Ornament low-utility ---
        "o_ornamentid",
        "o_fragmentid",
        "o_relationship",
        "o_onornament",
        "o_color1",
        "o_color2",
        "o_encrustcolor1",
        "o_encrustcolor2",
        # --- tblfinds internal / audit ---
        "fi_layerid",
        "fi_fragmentid",
        "fi_ornamentid",
        # --- finds (archaeology) internal / niche / audit ---
        "fi_year_inv_no",
        "fi_cat_no",
        "fi_museum_inv",
        "fi_reper",
        "fi_drawing",
        "fi_photo",
        "fi_drw_link",
        "fi_extra_field",
        "fi_reper_n_coord",
        "fi_reper_e_coord",
        "fi_reper_baltic",
        "fi_baltic",
        # --- finds coordinates (no layer relationship) ---
        "fi_coord_north_m",
        "fi_coord_east_m",
        # --- finds stratigraphic (no layer relationship) ---
        "fi_stratigraphic_level",
    }
)


def is_ui_hidden_column(name: str) -> bool:
    return (name or "").strip().lower() in _UI_HIDDEN_COLUMNS


def ui_columns(columns: list[str]) -> list[str]:
    """Return columns allowed to appear in UI (preserves original casing)."""
    return [c for c in columns if not is_ui_hidden_column(c)]


def parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


def result_for(query_id: str, **kwargs) -> AnalyticsResult:
    with session_scope() as db:
        if query_id == "q2":
            return query_q2_layers_fragments_ornaments(db, **kwargs)
        if query_id == "finds":
            return query_finds(db, **kwargs)
        if query_id == "finds_arch":
            return query_finds_archaeology(db, **kwargs)
        return query_finds(db, **kwargs)


def _extract_layer_filters(kwargs: dict) -> dict[str, Any] | None:
    """Extract layer_filters from kwargs, falling back to legacy site/sector/square."""
    lf = kwargs.get("layer_filters")
    if lf:
        return lf
    site = kwargs.get("site")
    sector = kwargs.get("sector")
    square = kwargs.get("square")
    if site or sector or square:
        return {
            "Site": [site] if site else [],
            "Sector": [sector] if sector else [],
            "Square": [square] if square else [],
        }
    return None


def norm_bucket(v: Any) -> str:
    """Normalize values into a histogram bucket label (never empty)."""
    if v is None:
        return "(null)"
    if isinstance(v, str):
        s = v.strip()
        return s if s else "(null)"
    return str(v)


_COLUMN_LABEL_KEYS: dict[str, str] = {
    "f_piecetype": "frag_piecetype",
    "f_technology": "frag_technology",
    "f_baking": "frag_baking",
    "f_primarycolor": "frag_color_primary",
    "f_covering": "frag_covering",
    "f_surface": "frag_surface",
    "f_wallthickness": "frag_wall_thickness",
    "f_handletype": "frag_handle_type",
    "f_handlesize": "frag_handle_size",
    "f_bottomtype": "frag_bottom_type",
    "f_category": "frag_category",
    "f_form": "frag_form",
    "f_type": "frag_type",
    "f_subtype": "frag_subtype",
    "f_variant": "frag_variant",
    "o_primary": "frag_primary",
    "o_secondary": "frag_secondary",
    "o_tertiary": "frag_tertiary",
    "o_quarternary": "frag_quarternary",
    "o_color1": "frag_color_color1",
    "o_encrustcolor1": "frag_encrust_color",
    "l_site": "label_site",
    "l_sector": "label_sector",
    "l_square": "label_square",
    "l_layer": "label_layer",
    # finds table location columns
    "fi_sector": "label_sector",
    "fi_square": "label_square",
    "fi_layer_mechanical": "label_layer",
}


def _column_to_label(col: str) -> str:
    """Convert a prefixed column name to a readable label."""
    from gkrp_data_portal.ui.lang import t

    key = _COLUMN_LABEL_KEYS.get(col)
    if key:
        return t(key)
    return col


def build_histogram(
    rows: list[dict], x_key: str, top_n: int = 30,
    pre_aggregated: list[dict[str, Any]] | None = None,
) -> tuple[list[str], list[int]]:
    """Build a top-N histogram for a column.

    If *pre_aggregated* is provided (from SQL aggregation), use it directly.
    Each item should be ``{"bucket": str, "count": int}``.
    Otherwise, fall back to Python-side aggregation from raw rows.
    """
    if pre_aggregated:
        items = sorted(pre_aggregated, key=lambda x: x.get("count", 0), reverse=True)[:top_n]
        return [i["bucket"] for i in items], [i["count"] for i in items]

    if not rows or not x_key:
        return [], []

    use_count = "f_count_deduped" in rows[0] or "f_count" in rows[0]
    bucket_sum: dict[str, int] = {}
    seen_frags: set = set()
    for r in rows:
        bucket = norm_bucket(r.get(x_key))
        if use_count:
            frag_id = r.get("f_fragmentid")
            if frag_id is not None and frag_id in seen_frags:
                continue
            val = r.get("f_count_deduped")
            if val is None:
                val = r.get("f_count")
            bucket_sum[bucket] = bucket_sum.get(bucket, 0) + (
                val if isinstance(val, (int, float)) else 0
            )
            if frag_id is not None:
                seen_frags.add(frag_id)
        else:
            bucket_sum[bucket] = bucket_sum.get(bucket, 0) + 1

    items = sorted(bucket_sum.items(), key=lambda x: x[1], reverse=True)[:top_n]
    xs = [k for k, _ in items]
    ys = [v for _, v in items]
    return xs, ys


def build_histogram_series(
    rows: list[dict], x_key: str, series_key: str, top_n: int = 30,
    pre_aggregated: list[dict[str, Any]] | None = None,
) -> tuple[list[str], dict[str, list[int]]]:
    """Build a top-N histogram grouped by a series dimension.

    If *pre_aggregated* is provided (from SQL aggregation), use it directly.
    Each item should be ``{"x_bucket": str, "series_bucket": str, "count": int}``.
    Otherwise, fall back to Python-side aggregation from raw rows.

    Returns ``(xs, series_data)`` where ``xs`` are the top-N bucket labels and
    ``series_data`` is ``{series_value: [y1, y2, ...]}`` — one list per series
    value, aligned to ``xs``.
    """
    if pre_aggregated:
        # Pivot SQL results: collect all x_buckets and series_values
        x_total: dict[str, int] = {}
        series_vals: dict[str, dict[str, int]] = {}
        for item in pre_aggregated:
            xb = item.get("x_bucket", "")
            sb = item.get("series_bucket", "")
            cnt = int(item.get("count", 0))
            x_total[xb] = x_total.get(xb, 0) + cnt
            if sb not in series_vals:
                series_vals[sb] = {}
            series_vals[sb][xb] = cnt

        # Top-N x_buckets by total
        top_x = sorted(x_total.items(), key=lambda x: x[1], reverse=True)[:top_n]
        xs = [k for k, _ in top_x]

        # Build aligned series data
        result_series: dict[str, list[int]] = {}
        for sv, xb_map in series_vals.items():
            counts = [xb_map.get(xb, 0) for xb in xs]
            if any(c > 0 for c in counts):
                result_series[sv] = counts
        return xs, result_series

    if not rows or not x_key or not series_key:
        return [], {}

    use_count = "f_count_deduped" in rows[0] or "f_count" in rows[0]
    bucket_series: dict[tuple[str, str], int] = {}
    seen_frags: set = set()
    for r in rows:
        x_bucket = norm_bucket(r.get(x_key))
        s_bucket = norm_bucket(r.get(series_key))
        if use_count:
            frag_id = r.get("f_fragmentid")
            if frag_id is not None and frag_id in seen_frags:
                continue
            val = r.get("f_count_deduped")
            if val is None:
                val = r.get("f_count")
            bucket_series[(x_bucket, s_bucket)] = bucket_series.get(
                (x_bucket, s_bucket), 0
            ) + (val if isinstance(val, (int, float)) else 0)
            if frag_id is not None:
                seen_frags.add(frag_id)
        else:
            bucket_series[(x_bucket, s_bucket)] = (
                bucket_series.get((x_bucket, s_bucket), 0) + 1
            )

    # Aggregate per x_bucket (sum across series) to pick top-N
    bucket_total: dict[str, int] = {}
    for (xb, sb), v in bucket_series.items():
        bucket_total[xb] = bucket_total.get(xb, 0) + v

    top_buckets = sorted(bucket_total.items(), key=lambda x: x[1], reverse=True)[:top_n]
    xs = [k for k, _ in top_buckets]

    # Collect all series values seen in the top-N buckets
    all_series: set[str] = set()
    for xb in xs:
        for bx, bs in bucket_series:
            if bx == xb:
                all_series.add(bs)

    # Build aligned series data — trace names are raw values, group title is column label
    # Filter out series values that are all zeros across the top-N buckets
    series_vals: dict[str, list[int]] = {}
    for sv in all_series:
        counts = [bucket_series.get((xb, sv), 0) for xb in xs]
        if any(c > 0 for c in counts):
            series_vals[sv] = counts

    return xs, series_vals


def plotly_bar(xs: list[str], ys: list[int], title: str) -> dict:
    return {
        "data": [
            {
                "type": "bar",
                "x": xs,
                "y": ys,
                "textposition": "outside",
                "texttemplate": "%{y}",
                "textfont": {"size": 12},
                "hovertemplate": "<b>%{x}</b><br>Count: %{y}<extra></extra>",
            }
        ],
        "layout": {
            "title": {"text": title},
            "margin": {"l": 50, "r": 20, "t": 50, "b": 90},
            "xaxis": {"automargin": True, "tickangle": -30},
            "yaxis": {"automargin": True},
        },
    }


def plotly_pie(labels: list[str], values: list[int], title: str) -> dict:
    return {
        "data": [
            {
                "type": "pie",
                "labels": labels,
                "values": values,
                "hole": 0.0,
                "textinfo": "label+percent",
                "textposition": "outside",
                "automargin": True,
            }
        ],
        "layout": {
            "title": {"text": title},
            "margin": {"l": 20, "r": 20, "t": 50, "b": 20},
            "showlegend": True,
        },
    }


def plotly_donut(labels: list[str], values: list[int], title: str) -> dict:
    return {
        "data": [
            {
                "type": "pie",
                "labels": labels,
                "values": values,
                "hole": 0.4,
                "textinfo": "label+percent",
                "textposition": "outside",
                "automargin": True,
            }
        ],
        "layout": {
            "title": {"text": title},
            "margin": {"l": 20, "r": 20, "t": 50, "b": 20},
            "showlegend": True,
        },
    }


def plotly_grouped_bar(
    xs: list[str],
    series_data: dict[str, list[int]],
    title: str,
    series_label: str = "Series",
) -> dict:
    """Build a grouped (clustered) bar chart with one trace per series value."""
    if not xs or not series_data:
        return plotly_bar([], [], title)

    data_traces: list[dict] = []
    for series_name, ys in series_data.items():
        # Hide traces that are all zeros
        show_trace = any(v > 0 for v in ys)
        # Use explicit text array: only show label for positive values
        texts: list[str | None] = [str(y) if y > 0 else None for y in ys]
        data_traces.append(
            {
                "type": "bar",
                "name": series_name,
                "x": xs,
                "y": ys,
                "text": texts,
                "legendgroup": series_label,
                "showlegend": show_trace,
                "textposition": "outside",
                "textfont": {"size": 14},
                "hovertemplate": f"<b>%{{x}}</b><br>{series_name}: %{{y}}<extra></extra>",
                "legendgrouptitle_text": series_label,
                "visible": show_trace,
            }
        )

    return {
        "data": data_traces,
        "layout": {
            "title": {"text": title},
            "barmode": "group",
            "margin": {"l": 50, "r": 20, "t": 50, "b": 90},
            "xaxis": {"automargin": True, "tickangle": -30},
            "yaxis": {"automargin": True},
            "showlegend": True,
            "legend": {
                "title": {"text": series_label},
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
        },
    }
