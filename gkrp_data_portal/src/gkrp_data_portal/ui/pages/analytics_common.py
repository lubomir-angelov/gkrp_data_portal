"""Shared helpers/constants for Analytics NiceGUI pages."""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from gkrp_data_portal.db.session import session_scope
from gkrp_data_portal.ui.repository.analytics_repo import (
    AnalyticsResult,
    query_finds,
    query_q2_layers_fragments_ornaments,
)

LOCALE: dict[str, str] = {
    # --- Navigation ---
    "nav_navigation": "Навигация",
    "nav_layers": "Пластове",
    "nav_fragments": "Отломъци",
    "nav_ornaments": "Орнаменти",
    "nav_admin": "Админ",
    "nav_analytics": "Аналитика",
    "nav_welcome_title": "GKR Портал — Вход на Данни",
    "nav_welcome_text": "Използвайте връзките от лявата навигация. Тази фаза реализира CRUD страници.",

    # --- Page titles ---
    "title_layers": "Пластове (tbllayers)",
    "title_fragments": "Отломъци (tblfragments)",
    "title_ornaments": "Орнаменти (tblornaments)",
    "title_admin": "Админ",
    "title_analytics": "Аналитика",
    "title_analytics_chart": "Аналитика — Графика",
    "title_analytics_table": "Аналитика — Таблица",
    "title_accept_invite": "Приемане на покана",
    "title_register": "Регистрацията е забранена",
    "title_register_text": "Достъпът е само по покана. Моля, свържете се с администратора.",
    "title_dev_login": "DEV Вход (задава session user_id)",
    "title_dev_login_text": "След като влезете, отворете **/admin** за тестване.",

    # --- Panels ---
    "panel_query_filters": "Запитване и Филтри",
    "panel_chart": "Графика",
    "panel_table": "Таблица (преместване)",
    "panel_fragments": "Отломъци",
    "panel_ornaments": "Орнаменти",

    # --- Buttons ---
    "btn_chart_view": "Изглед Графика",
    "btn_table_view": "Изглед Таблица",
    "btn_run_query": "Изпълни запитване",
    "btn_refresh": "Обнови",
    "btn_new_layer": "Нов Пласт",
    "btn_new_fragment": "Нов Отломък",
    "btn_new_ornament": "Нов Орнамент",
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
    "label_layer_optional": "Пласт (по избор)",
    "label_fragment_optional": "Отломък (по избор)",
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
    "col_fragmenttype": "Вид Отломък",
    "col_technology": "Технология",
    "col_baking": "Печене",
    "col_primary": "Основно",
    "col_secondary": "Вторично",
    "col_tertiary": "Третично",
    "col_count": "Брой",
    "col_inventory": "Инвентарен №",
    "col_image_url": "URL Изображение",
    "col_fragment_id": "ИД Отломък",
    "col_location": "Местоположение",
    "col_primary_": "Основно",
    "col_color1": "Цвят1",
    "col_color2": "Цвят2",
    "col_username": "Потребител",
    "col_invited": "Поканен",
    "col_invite_expires": "Покана изтича",

    # --- Dialogs ---
    "dialog_edit_layer": "Редактиране на Пласт",
    "dialog_create_layer": "Създаване на Пласт",
    "dialog_edit_fragment": "Редактиране на Отломък",
    "dialog_create_fragment": "Създаване на Отломък",
    "dialog_edit_ornament": "Редактиране на Орнамент",
    "dialog_create_ornament": "Създаване на Орнамент",
    "dialog_user_actions": "Действия за потребител {uid}",
    "dialog_layer_hint": "Ако **ИД на Пласт** е празно, ще бъде изведено като **най-новият пласт** (паритет с керамичния работен процес).",
    "dialog_fragment_hint": "Ако **ИД на Пласт** е празно, ще бъде изведено като **най-новият пласт** (паритет с керамичния работен процес).",
    "dialog_ornament_hint": "Ако **ИД на Отломък** е празно, ще бъде изведено като **най-новият отломък** (паритет с керамичния работен процес).",

    # --- Queries ---
    "query_filter2": "Филтър #2 (Пластове + Отломъци + Орнаменти)",
    "query_finds": "Открития (tblfinds)",

    # --- Chart controls ---
    "chart_type_bar": "Стълб",
    "chart_type_pie": "Кръг",
    "chart_type_donut": "Поничка",
    "chart_help_label": "Упътване",
    "chart_help_close": "Затвори",

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
    "search_fragments": "Търсене (инвентарен бр./бележка/тип отломък/вид отломък/технология)",
    "search_ornaments": "Търсене (местоположение/основно/вторично/третично)",

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

    # --- Other ---
    "other_invite_created_text": "Поканата е създадена. Копирайте и изпратете тази връзка:",
    "other_invite_body": "Бяхте поканени.\n\nОтворете тази връзка, за да активирате акаунта си:\n{link}\n\nТази връзка изтича след {ttl} часа.",
    "other_access_by_invite": "Достъпът е само по покана. Моля, свържете се с администратора.",
    "other_create_user_first": "Създайте потребител (или покана) първо, след което се върнете.",
}

QUERY_OPTIONS: dict[str, str] = {
    LOCALE["query_filter2"]: "q2",
    LOCALE["query_finds"]: "finds",
}

DEFAULT_LIMIT = 500

TABLE_MAX_LIMIT = 100000  # table UI cap
CHART_MAX_FETCH = 25000  # chart safety cap (top-N buckets don't benefit from >25k rows)


_UI_HIDDEN_COLUMNS = frozenset(
    {
        "l_recordenteredon",
        "l_recordenteredby",
        "l_recordcreatedby",
        "l_recordcreatedon",
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
        "f_fragmentid",
        "f_locationid",
        "f_outline",
        "f_speed",
        "f_recrodenteredby",
        "f_recrodenteredon",
        "f_topsize",
        "f_necksize",
        "f_bodysize",
        "f_bottomsize",
        "f_dishheight",
        "f_composition",
        "f_parallels",
        "f_decoration",
        "f_recordcreatedby",
        "f_recordcreatedon",
        "f_recordenteredby",
        "f_recordenteredon",
        "f_image",
        "f_count",
        "l_layername",
        "f_fragmenttype",
        "f_fract",
        "f_onepot",
        "f_handlesize",
        "f_img_url",
        "o_ornamentid",
        "o_fragmentid",
        "o_relationship",
        "o_onornament",
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


_COLUMN_LABELS: dict[str, str] = {
    "f_piecetype": LOCALE["frag_piecetype"],
    "f_technology": LOCALE["frag_technology"],
    "f_baking": LOCALE["frag_baking"],
    "f_primarycolor": LOCALE["frag_color_primary"],
    "f_covering": LOCALE["frag_covering"],
    "f_surface": LOCALE["frag_surface"],
    "f_wallthickness": LOCALE["frag_wall_thickness"],
    "f_handletype": LOCALE["frag_handle_type"],
    "f_handlesize": LOCALE["frag_handle_size"],
    "f_bottomtype": LOCALE["frag_bottom_type"],
    "f_category": LOCALE["frag_category"],
    "f_form": LOCALE["frag_form"],
    "f_type": LOCALE["frag_type"],
    "f_subtype": LOCALE["frag_subtype"],
    "f_variant": LOCALE["frag_variant"],
    "o_primary": LOCALE["frag_primary"],
    "o_secondary": LOCALE["frag_secondary"],
    "o_tertiary": LOCALE["frag_tertiary"],
    "o_quarternary": LOCALE["frag_quarternary"],
    "o_color1": LOCALE["frag_color_color1"],
    "o_encrustcolor1": LOCALE["frag_encrust_color"],
    "l_site": LOCALE["label_site"],
    "l_sector": LOCALE["label_sector"],
    "l_square": LOCALE["label_square"],
    "l_layer": LOCALE["label_layer"],
}


def _column_to_label(col: str) -> str:
    """Convert a prefixed column name to a readable label."""
    return _COLUMN_LABELS.get(col, col)


def build_histogram(
    rows: list[dict], x_key: str, top_n: int = 30
) -> tuple[list[str], list[int]]:
    """Build a top-N histogram for a column from dict rows.

    The y-values always sum ``f_count`` instead of counting rows, because each
    row represents *count* physical fragments.
    """
    if not rows or not x_key:
        return [], []

    bucket_sum: dict[str, int] = {}
    for r in rows:
        bucket = norm_bucket(r.get(x_key))
        val = r.get("f_count")
        bucket_sum[bucket] = bucket_sum.get(bucket, 0) + (
            val if isinstance(val, (int, float)) else 0
        )

    items = sorted(bucket_sum.items(), key=lambda x: x[1], reverse=True)[:top_n]
    xs = [k for k, _ in items]
    ys = [v for _, v in items]
    return xs, ys


def build_histogram_series(
    rows: list[dict], x_key: str, series_key: str, top_n: int = 30
) -> tuple[list[str], dict[str, list[int]]]:
    """Build a top-N histogram grouped by a series dimension.

    Returns ``(xs, series_data)`` where ``xs`` are the top-N bucket labels and
    ``series_data`` is ``{series_value: [y1, y2, ...]}`` — one list per series
    value, aligned to ``xs``.
    """
    if not rows or not x_key or not series_key:
        return [], {}

    bucket_series: dict[tuple[str, str], int] = {}
    for r in rows:
        x_bucket = norm_bucket(r.get(x_key))
        s_bucket = norm_bucket(r.get(series_key))
        val = r.get("f_count")
        bucket_series[(x_bucket, s_bucket)] = bucket_series.get(
            (x_bucket, s_bucket), 0
        ) + (val if isinstance(val, (int, float)) else 0)

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
    series_vals: dict[str, list[int]] = {}
    for sv in all_series:
        key = sv
        series_vals[key] = []
        for xb in xs:
            series_vals[key].append(bucket_series.get((xb, sv), 0))

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
        data_traces.append(
            {
                "type": "bar",
                "name": series_name,
                "x": xs,
                "y": ys,
                "legendgroup": series_label,
                "showlegend": True,
                "textposition": "outside",
                "texttemplate": "%{y}",
                "textfont": {"size": 12},
                "hovertemplate": f"<b>%{{x}}</b><br>{series_name}: %{{y}}<extra></extra>",
                "legendgrouptitle_text": series_label,
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
