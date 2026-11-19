import streamlit as st
import pandas as pd
import random
import os
from datetime import date, timedelta
from streamlit_local_storage import LocalStorage
import streamlit.components.v1 as components
from sqlalchemy import create_engine, text

# --- НАСТРОЙКА БАЗЫ ДАННЫХ (SUPABASE) ---
DB_URL = os.environ.get("DATABASE_URL")
if not DB_URL:
    st.error("Ошибка: Переменная окружения DATABASE_URL не настроена.")
    st.stop()

if DB_URL.startswith("postgres://"):
    DB_URL = DB_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DB_URL, pool_pre_ping=True)

@st.cache_resource
def init_db():
    with engine.begin() as conn:
        conn.execute(text('''CREATE TABLE IF NOT EXISTS users
                     (name TEXT PRIMARY KEY, streak INTEGER, last_login TEXT, xp INTEGER, crystals INTEGER, 
                      last_xp_date TEXT, theme TEXT, quest_calc INTEGER, quest_read INTEGER, level INTEGER, shared INTEGER,
                      max_streak INTEGER, max_level INTEGER, avatar TEXT, chest_claimed INTEGER, last_bonus_date TEXT, 
                      last_challenge_date TEXT, feedback TEXT, streak_freeze INTEGER DEFAULT 0,
                      daily_quest_calc BOOLEAN DEFAULT FALSE, daily_quest_read BOOLEAN DEFAULT FALSE, last_daily_reset TEXT DEFAULT '', promo_used TEXT DEFAULT '')'''))
        conn.execute(text('''CREATE TABLE IF NOT EXISTS leaderboard
                     (name TEXT PRIMARY KEY, xp INTEGER)'''))
        conn.execute(text('''CREATE TABLE IF NOT EXISTS saved_goals
                     (id SERIAL PRIMARY KEY, user_name TEXT, goal_name TEXT, target_amount REAL, saved_amount REAL)'''))

        conn.execute(text("DELETE FROM leaderboard WHERE name IN ('Alex', 'Max', 'Sophie', 'Ivan', 'Kate')"))
        conn.execute(text("DELETE FROM users WHERE name IN ('Alex', 'Max', 'Sophie', 'Ivan', 'Kate')"))


init_db()


# --- ФУНКЦИИ (С КЭШЕМ) ---
@st.cache_data(ttl=60)
def get_user_stats(name):
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT streak, last_login, xp, crystals, last_xp_date, theme, quest_calc, quest_read, level, shared, max_streak, max_level, avatar, chest_claimed, streak_freeze, daily_quest_calc, daily_quest_read, last_daily_reset FROM users WHERE name = :name"),
                              {"name": name}).fetchone()
        return result


def create_user(name):
    with engine.begin() as conn:
        conn.execute(text(
            "INSERT INTO users (name, streak, last_login, xp, crystals, last_xp_date, theme, quest_calc, quest_read, level, shared, max_streak, max_level, avatar, chest_claimed, last_bonus_date, last_challenge_date, feedback, streak_freeze, daily_quest_calc, daily_quest_read, last_daily_reset, promo_used) VALUES (:name, 0, '', 0, 0, '', 'default', 0, 0, 1, 0, 0, 1, '🦉', 0, '', '', '', 0, FALSE, FALSE, '', '') ON CONFLICT DO NOTHING"),
                     {"name": name})
        conn.execute(text("INSERT INTO leaderboard (name, xp) VALUES (:name, 0) ON CONFLICT DO NOTHING"),
                     {"name": name})
    st.cache_data.clear()


def save_goal_to_db(user_name, goal_name, target, current):
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO saved_goals (user_name, goal_name, target_amount, saved_amount) VALUES (:u, :g, :t, :c)"),
            {"u": user_name, "g": goal_name, "t": target, "c": current})


def get_saved_goals(user_name):
    with engine.connect() as conn:
        return conn.execute(
            text("SELECT id, goal_name, target_amount, saved_amount FROM saved_goals WHERE user_name = :u"),
            {"u": user_name}).fetchall()


def delete_goal(goal_id):
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM saved_goals WHERE id = :id"), {"id": goal_id})


def buy_avatar(name, avatar_emoji, cost):
    with engine.begin() as conn:
        crystals = conn.execute(text("SELECT crystals FROM users WHERE name = :name"), {"name": name}).fetchone()[0]
        if crystals >= cost:
            conn.execute(text("UPDATE users SET crystals = crystals - :cost, avatar = :av WHERE name = :name"),
                         {"cost": cost, "av": avatar_emoji, "name": name})
            st.cache_data.clear()
            return True
        return False


def buy_streak_freeze(name):
    with engine.begin() as conn:
        crystals = conn.execute(text("SELECT crystals FROM users WHERE name = :name"), {"name": name}).fetchone()[0]
        if crystals >= 50:
            conn.execute(
                text("UPDATE users SET crystals = crystals - 50, streak_freeze = streak_freeze + 1 WHERE name = :name"),
                {"name": name})
            st.cache_data.clear()
            return True
        return False


def apply_promo(name, code):
    with engine.begin() as conn:
        if code == "START2026":
            promo_used = \
            conn.execute(text("SELECT promo_used FROM users WHERE name = :name"), {"name": name}).fetchone()[0]
            if promo_used != "START2026":
                conn.execute(
                    text("UPDATE users SET crystals = crystals + 100, promo_used = 'START2026' WHERE name = :name"),
                    {"name": name})
                st.cache_data.clear()
                return True
        return False


def update_streak_and_xp(name):
    with engine.begin() as conn:
        user = conn.execute(text(
            "SELECT streak, last_login, xp, level, max_streak, max_level, streak_freeze FROM users WHERE name = :name"),
                            {"name": name}).fetchone()
        streak, last_login, xp, current_level, max_streak, max_level, freeze = user
        streak = streak if streak is not None else 0
        last_login = last_login if last_login is not None else ""
        xp = xp if xp is not None else 0
        current_level = current_level if current_level is not None else 1
        max_streak = max_streak if max_streak is not None else 0
        max_level = max_level if max_level is not None else 1
        freeze = freeze if freeze is not None else 0

        now = date.today()
        if last_login:
            last_date = date.fromisoformat(last_login)
            delta = (now - last_date).days
            if delta == 1:
                streak += 1
            elif delta > 1:
                if freeze > 0:
                    conn.execute(text("UPDATE users SET streak_freeze = streak_freeze - 1 WHERE name = :name"),
                                 {"name": name})
                    streak += 1
                else:
                    streak = 1
        else:
            streak = 1

        today_str = now.isoformat()
        if last_login != today_str:
            xp += 10
            if streak % 7 == 0:
                xp += 50
            elif streak % 3 == 0:
                xp += 20

        new_level = (xp // 100) + 1
        if new_level > current_level:
            conn.execute(text("UPDATE users SET crystals = crystals + 50 WHERE name = :name"), {"name": name})

        if streak > max_streak: max_streak = streak
        if new_level > max_level: max_level = new_level

        conn.execute(text(
            "UPDATE users SET streak = :st, last_login = :ll, xp = :xp, level = :lv, max_streak = :ms, max_level = :ml WHERE name = :name"),
                     {"st": streak, "ll": today_str, "xp": xp, "lv": new_level, "ms": max_streak, "ml": max_level,
                      "name": name})
        conn.execute(text("UPDATE leaderboard SET xp = :xp WHERE name = :name"), {"xp": xp, "name": name})


def claim_daily_challenge(name):
    with engine.begin() as conn:
        today_str = date.today().isoformat()
        conn.execute(text(
            "UPDATE users SET xp = xp + 30, crystals = crystals + 30, last_challenge_date = :d WHERE name = :name"),
                     {"d": today_str, "name": name})
        new_xp = conn.execute(text("SELECT xp FROM users WHERE name = :name"), {"name": name}).fetchone()[0]
        conn.execute(text("UPDATE leaderboard SET xp = :xp WHERE name = :name"), {"xp": new_xp, "name": name})
    st.cache_data.clear()


def complete_quest(name, quest_name, reward_xp, reward_crystals):
    with engine.begin() as conn:
        if quest_name == "calc":
            conn.execute(text(
                "UPDATE users SET quest_calc = 1, xp = xp + :rx, crystals = crystals + :rc, daily_quest_calc = TRUE WHERE name = :name"),
                         {"rx": reward_xp, "rc": reward_crystals, "name": name})
        elif quest_name == "read":
            conn.execute(text(
                "UPDATE users SET quest_read = 1, xp = xp + :rx, crystals = crystals + :rc, daily_quest_read = TRUE WHERE name = :name"),
                         {"rx": reward_xp, "rc": reward_crystals, "name": name})
        elif quest_name == "share":
            conn.execute(text("UPDATE users SET shared = 1, crystals = crystals + :rc WHERE name = :name"),
                         {"rc": reward_crystals, "name": name})
        new_xp = conn.execute(text("SELECT xp FROM users WHERE name = :name"), {"name": name}).fetchone()[0]
        conn.execute(text("UPDATE leaderboard SET xp = :xp WHERE name = :name"), {"xp": new_xp, "name": name})
    st.cache_data.clear()


def save_feedback(name, feedback_text):
    with engine.begin() as conn:
        conn.execute(text("UPDATE users SET feedback = :fb WHERE name = :name"), {"fb": feedback_text, "name": name})


def buy_theme(name, theme_id, cost):
    with engine.begin() as conn:
        crystals = conn.execute(text("SELECT crystals FROM users WHERE name = :name"), {"name": name}).fetchone()[0]
        if crystals >= cost:
            conn.execute(text("UPDATE users SET crystals = crystals - :cost, theme = :theme WHERE name = :name"),
                         {"cost": cost, "theme": theme_id, "name": name})
            st.cache_data.clear()
            return True
        return False


@st.cache_data(ttl=30)
def get_leaderboard():
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT leaderboard.name, leaderboard.xp, users.avatar FROM leaderboard LEFT JOIN users ON leaderboard.name = users.name ORDER BY leaderboard.xp DESC")).fetchall()
        return [(row[0], row[1], row[2] if row[2] else "🦉") for row in result]


def get_opponent_stats(name):
    with engine.connect() as conn:
        return conn.execute(text("SELECT xp, crystals, streak, avatar FROM users WHERE name = :name"),
                            {"name": name}).fetchone()


def calc_compound(principal, monthly, annual_rate, years):
    months = int(years * 12)
    r = annual_rate / 100 / 12
    balances = []
    total = principal
    for m in range(1, months + 1):
        total = total * (1 + r) + monthly
        if m % 12 == 0 or m == months: balances.append((m / 12, total))
    contributed = principal + monthly * months
    return total, contributed, balances


# --- СЛОВАРИ (ОСТАВЛЯЕМ КАК ЕСТЬ) ---
texts = {
    "Русский": {
        "title": "💰 Questalism", "subtitle": "Твоя мечта. Твой путь. Твои деньги.",
        "nav_home": "🏠 Главная", "nav_game": "🎮 Квест", "nav_league": "🏆 Рейтинг", "nav_shop": "🛒 Магазин",
        "nav_knowledge": "📚 База", "nav_dictionary": "📖 Словарь",
        "who": "Кто ты?", "teen": "Подросток", "adult": "Взрослый", "age": "Сколько тебе лет?",
        "goal_header": "1. Твоя цель", "goal_input": "На что копишь?", "currency": "Валюта",
        "rub": "Рубли (₽)", "usd": "Доллары ($)", "target": "Сколько стоит?",
        "data_header": "2. Твои данные", "current": "Сколько есть сейчас?",
        "monthly": "Сколько можешь откладывать в месяц?", "custom": "Своё", "custom_input": "Введи сумму:",
        "jobs_header": "3. Твоя подработка", "choose": "Выбери", "no": "Нет", "own_job": "Своя подработка",
        "salary": "Сколько ты зарабатываешь?", "result": "🏆 Твой результат",
        "target_label": "Цель", "term_label": "Срок", "inflation_label": "С инфляцией",
        "inflation_info": "Инфляция — это подорожание денег в будущем.", "months": "мес.",
        "chart_month": "Месяц", "chart_balance": "Баланс", "you_at": "Ты на", "to_goal": "% к цели",
        "achievements": "🎖️ Твои ачивки", "quest_levels": "🛡️ Твои вехи (Этапы)",
        "speed_up": "🚀 Как ускорить цель", "if_more": "Если откладывать на", "more": "больше → срок:",
        "need_daily": "Нужно откладывать в день:", "wish": "Удачи! Ты справишься. 💪",
        "warning": "Введи сумму больше 0.", "goal_reached": "Ты уже накопил на эту цель! 🎉",
        "status_green": "🟢 Реально! Ты достигнешь цели быстро.", "status_yellow": "🟡 Средне. Придется постараться.",
        "status_red": "🔴 Долго. Подумай, как увеличить доход.", "next_step": "👉 Следующий шаг:",
        "next_step_1": "Попробуй добавить подработку, чтобы сократить срок.",
        "next_step_2": "Отлично! Теперь просто придерживайся плана.",
        "share_text": "Я накоплю на {goal} за {months} месяцев с Questalism! А ты сможешь? Проверь свои финансы: questalism-7uln.onrender.com",
        "hustle_btn": "Сгенерировать идею",
        "hustle_result": "Тебе подойдет: {idea}. Примерный доход: {income} {symbol}.",
        "hustles": [("Выгул собак", 5000), ("Помощь с уроками", 6000), ("Курьер", 8000), ("Стриминг", 3000),
                    ("Продажа вещей", 4000), ("Репетиторство", 10000), ("Компьютеры", 7000), ("Документы", 6000)],
        "ach1": "🎯 Первый шаг — ты начал копить.", "ach2": "💎 Сберегатель — откладываешь больше 1000 в месяц.",
        "ach3": "🥇 Четверть пути — ты прошёл 25% к цели.", "ach4": "🔥 Половина — ты на середине пути.",
        "ach5": "⭐ Почти у цели — осталось 25%.", "ach6": "🏆 Марафонец — твоя цель на год и больше.",
        "ach7": "🚀 Спринтер — ты добьешься цели меньше чем за 6 месяцев.",
        "ach8": "💪 Работяга — у тебя есть дополнительный доход.",
        "ach9": "👑 Высокий доход — ты зарабатываешь больше 10K.",
        "ach10": "🎓 Школьник — ты учишься и копишь одновременно.",
        "milestone_10": "10% — Первый шаг", "milestone_25": "25% — Четверть пути", "milestone_50": "50% — Экватор",
        "milestone_75": "75% — Финиш близко", "milestone_100": "100% — Покупка!", "milestone_done": "✅ Пройдено",
        "milestone_wait": "🔒 Впереди", "why_save": "Почему важно копить",
        "why1": "• Финансовая свобода: ты не зависишь от родителей в мелочах.",
        "why2": "• Мечты сбываются: покупка того, что давно хотел.",
        "why3": "• Уверенность: ты знаешь, что у тебя есть запас.",
        "why4": "• Будущее: привычка копить останется с тобой навсегда.",
        "spend_less": "Как меньше тратить",
        "spend1": "• Правило 24 часов: если хочешь импульсивную покупку — подожди день. Если желание не пропало — бери.",
        "spend2": "• Список покупок: иди в магазин только с готовым списком.",
        "spend3": "• Кофе дома: делай напитки сам.",
        "spend4": "• Подписки: проверь, какими сервисами ты реально пользуешься.",
        "spend5": "• Импульс: не покупай, когда злишься.",
        "psychology": "Психология накоплений", "psy1": "• Автоматизация: откладывай деньги сразу.",
        "psy2": "• Визуализация: повесь картинку цели.",
        "psy3": "• Маленькие шаги: лучше отложить 100 рублей, чем 0.", "psy4": "• Поддержка: расскажи другу о цели.",
        "psy5": "• Прощение: если потратил лишнее — не ругай себя.",
        "feature": "💡 Совет дня", "feature_btn": "Получить совет",
        "tips": ["Начни с 100 рублей.", "Запиши цель.", "Сравни себя с собой вчерашним.", "Отложи 10%.",
                 "Не жди понедельника."],
        "dash_hello": "Привет, {name}!", "dash_level": "Уровень", "dash_xp": "⭐ Опыт", "dash_daily": "📅 Задания дня",
        "streak_label": "Стрик", "days": "дней", "crystals_label": "Кристаллы", "league_title": "🏆 Рейтинг",
        "league_desc": "Соревнуйся с другими!",
        "shop_title": "🛒 Магазин", "shop_desc": "Трать кристаллы на улучшение профиля.", "theme_default": "Классика",
        "theme_neon": "Неон",
        "theme_light": "Светлая", "theme_space": "Космос", "theme_dark": "Ночная", "cost_label": "Стоимость: {cost} 💎",
        "buy_btn": "Купить за {cost} 💎", "owned_btn": "Уже куплено ✅", "not_enough": "Не хватает кристаллов!",
        "btn_next_game": "Идём к цели ➡️", "btn_next_knowledge": "Идём в Базу знаний ➡️",
        "btn_next_league": "Идём в Рейтинг ➡️",
        "btn_next_shop": "Идём в Магазин ➡️", "btn_next_home": "Идём на Главную ➡️",
        "btn_next_dict": "Идём в Словарь ➡️",
        "quest_calc_done": "Квест 'Рассчитать цель' выполнен! +50 XP, +10 💎",
        "quest_read_done": "Квест 'Прочитать совет' выполнен! +20 XP, +5 💎",
        "btn_claim_calc": "🎯 Завершить квест", "btn_claim_read": "💡 Получить совет",
        "btn_share_reward": "📲 Скопировать и получить 20 💎",
        "share_reward_done": "✅ Награда за рекламу получена!", "records_title": "🏅 Личные рекорды",
        "rec_streak": "Максимальный стрик",
        "rec_level": "Максимальный уровень", "ad_text": "Скопируй текст ниже и отправь другу:",
        "level_progress": "Прогресс до следующего уровня",
        "copy_btn": "📋 Скопировать текст", "copied": "✅ Скопировано!", "view_profile": "Профиль соперника",
        "avatar_shop": "🦉 Аватарки", "avatar_desc": "Смени своего совенка!", "theme_shop": "🎨 Темы оформления",
        "theme_desc": "Смени цвета сайта!",
        "quest_map": "🗺️ Твой путь", "q_step1": "Поставить цель", "q_step2": "Рассчитать срок",
        "q_step3": "Прочитать совет", "q_step4": "Поделиться",
        "dict_title": "📖 Финансовый словарь", "dict_desc": "Базовые термины, которые пригодятся в жизни.",
        "dict_terms": {
            "Бюджет": "План доходов и расходов.", "Активы и пассивы": "Активы приносят деньги, пассивы забирают.",
            "Доход": "Активный (работа) и пассивный (проценты).", "Подушка безопасности": "Резерв на 3-6 месяцев.",
            "Инфляция": "Обесценивание денег.", "Дебетовая и кредитная карты": "Свои деньги vs деньги банка.",
            "Банковский вклад": "Даешь деньги банку под процент.", "Сложный процент": "Проценты на проценты.",
            "Инвестиции": "Вложение ради дохода.", "Кэшбэк": "Возврат части денег."
        },
        "save_goal_btn": "💾 Сохранить эту цель", "my_goals": "📂 Мои цели",
        "no_goals": "У тебя пока нет сохраненных целей.",
        "share_league_btn": "📢 Похвастаться местом в Рейтинге",
        "share_league_text": "Я на {rank} месте в Рейтинге Questalism! Попробуй обыграть меня: questalism-7uln.onrender.com",
        "safety_title": "🛡️ Подушка безопасности", "safety_desc": "Сколько денег тебе нужно для безопасности?",
        "safety_expenses": "Твои месячные расходы:", "safety_months": "На сколько месяцев нужна подушка?",
        "safety_result": "Твоя подушка безопасности:",
        "safety_btn": "Рассчитать",
        "achievements_earned": "Посмотреть, за что ты получил ачивку, можно в разделе 'Квест'.",
        "safety_hint": "Рекомендуем копить на 3-6 месяцев жизни.", "made_with_love": "Сделано с ❤️ для всех. v1.0",
        "hide_btn": "🙈 Скрыть цифры", "show_btn": "👁️ Показать цифры", "hide_mode_info": "Режим скрытия цифр включён.",
        "compound_title": "✨ Сила сложного процента", "compound_desc": "Посмотри, как работают деньги.",
        "compound_principal": "Начальная сумма",
        "compound_monthly": "Ежемесячный взнос", "compound_rate": "Ставка, % годовых", "compound_years": "Срок, лет",
        "compound_calc": "Рассчитать", "compound_with": "Со сложным процентом",
        "compound_without": "Без процентов (только взносы)",
        "compound_contributed": "Всего вложено", "compound_profit": "Заработано на процентах",
        "compound_magic": "Магия сложного процента дала тебе +{diff} сверху!",
        "compound_chart": "Рост капитала по годам", "privacy_title": "🔒 Политика конфиденциальности",
        "privacy_text": "Твоя приватность важна. Мы собираем только имя и цели. Не передаем третьим лицам.",
        "privacy_btn": "🔒 Политика конфиденциальности",
        "challenge_title": "🔥 Челлендж дня",
        "challenge_desc": "Отложи сегодня 100 ₽ на свою цель. Это формирует привычку!",
        "challenge_btn": "✅ Я отложил 100 ₽ (+30 XP, +30 💎)",
        "challenge_done": "✅ Ты выполнил челлендж дня! Возвращайся завтра.",
        "feedback_title": "💬 Обратная связь",
        "feedback_desc": "Насколько тебе удобно пользоваться сайтом? Есть что улучшить?",
        "feedback_placeholder": "Напиши свои мысли...", "feedback_btn": "Отправить отзыв",
        "feedback_done": "✅ Спасибо за твой отзыв!",
        "streak_freeze_title": "🧊 Заморозка стрика", "streak_freeze_desc": "Пропустил день? Сохрани свой стрик за 50 💎",
        "streak_freeze_btn": "Купить за 50 💎", "streak_freeze_owned": "Куплено: {count} шт.",
        "daily_quests_title": "📅 Ежедневные задания", "quest_login": "Зайти на сайт",
        "quest_calc_task": "Рассчитать цель", "quest_read_task": "Прочитать совет",
        "quest_done": "✅ Выполнено", "quest_not_done": "❌ Не выполнено", "promo_title": "🎁 Промокод",
        "promo_input": "Введи промокод", "promo_btn": "Активировать",
        "promo_success": "✅ Промокод активирован! +100 💎", "promo_error": "❌ Неверный промокод или уже использован."
    },
    "English": {
        "title": "💰 Questalism", "subtitle": "Your dream. Your path. Your money.",
        "nav_home": "🏠 Home", "nav_game": "🎮 Quest", "nav_league": "🏆 Rating", "nav_shop": "🛒 Shop",
        "nav_knowledge": "📚 Knowledge", "nav_dictionary": "📖 Dictionary",
        "who": "Who are you?", "teen": "Teenager", "adult": "Adult", "age": "Age?",
        "goal_header": "1. Goal", "goal_input": "Saving for?", "currency": "Currency",
        "rub": "Rubles (₽)", "usd": "Dollars ($)", "target": "Cost?",
        "data_header": "2. Data", "current": "Current savings?",
        "monthly": "How much can you save per month?", "custom": "Custom", "custom_input": "Amount:",
        "jobs_header": "3. Job", "choose": "Choose", "no": "None", "own_job": "Own",
        "salary": "Earn?", "result": "🏆 Result",
        "target_label": "Goal", "term_label": "Term", "inflation_label": "Inflation",
        "inflation_info": "Inflation is price rise.", "months": "mo.",
        "chart_month": "Month", "chart_balance": "Balance", "you_at": "You at", "to_goal": "%",
        "achievements": "🎖️ Achievements", "quest_levels": "🛡️ Milestones",
        "speed_up": "🚀 Speed up", "if_more": "Save", "more": "more → term:",
        "need_daily": "Daily:", "wish": "Good luck!",
        "warning": "Enter > 0.", "goal_reached": "Goal reached! 🎉",
        "status_green": "🟢 Realistic!", "status_yellow": "🟡 Medium.", "status_red": "🔴 Long. Increase income.",
        "next_step": "👉 Next:", "next_step_1": "Add a job to speed up.",
        "next_step_2": "Great! Just stick to the plan.",
        "share_text": "I'll save for {goal} in {months} months with Questalism! Check: questalism-7uln.onrender.com",
        "hustle_btn": "Generate idea", "hustle_result": "Try: {idea}. Income: {income} {symbol}.",
        "hustles": [("Dog walking", 5000), ("Homework", 6000), ("Courier", 8000), ("Streaming", 3000),
                    ("Selling", 4000), ("Tutor", 10000), ("PC help", 7000), ("Docs", 6000)],
        "ach1": "🎯 First step.", "ach2": "💎 Saver.", "ach3": "🥇 Quarter.", "ach4": "🔥 Halfway.", "ach5": "⭐ Almost.",
        "ach6": "🏆 Marathoner.", "ach7": "🚀 Sprinter.", "ach8": "💪 Worker.", "ach9": "👑 High income.",
        "ach10": "🎓 Student.",
        "milestone_10": "10%", "milestone_25": "25%", "milestone_50": "50%", "milestone_75": "75%",
        "milestone_100": "100%",
        "milestone_done": "✅ Done", "milestone_wait": "🔒 Ahead",
        "why_save": "Why save", "why1": "• Financial freedom.", "why2": "• Dreams come true.", "why3": "• Confidence.",
        "why4": "• Future habit.",
        "spend_less": "Spend less", "spend1": "• 24-hour rule.", "spend2": "• Shopping list.",
        "spend3": "• Coffee at home.", "spend4": "• Subscriptions.", "spend5": "• Impulse.",
        "psychology": "Psychology", "psy1": "• Automation.", "psy2": "• Visualization.", "psy3": "• Small steps.",
        "psy4": "• Support.", "psy5": "• Forgiveness.",
        "feature": "💡 Tip", "feature_btn": "Get tip",
        "tips": ["Start with $1.", "Write goal.", "Compare to self.", "Save 10%.", "Start today."],
        "dash_hello": "Hello, {name}!", "dash_level": "Level", "dash_xp": "⭐ XP", "dash_daily": "📅 Daily Quests",
        "streak_label": "Streak", "days": "days", "crystals_label": "Crystals", "league_title": "🏆 Rating",
        "league_desc": "Compete with others!",
        "shop_title": "🛒 Shop", "shop_desc": "Spend crystals to upgrade profile.", "theme_default": "Classic",
        "theme_neon": "Neon",
        "theme_light": "Light", "theme_space": "Space", "theme_dark": "Night", "cost_label": "Cost: {cost} 💎",
        "buy_btn": "Buy for {cost} 💎", "owned_btn": "Owned ✅", "not_enough": "Not enough crystals!",
        "btn_next_game": "Go to Quest ➡️", "btn_next_knowledge": "Go to Knowledge ➡️",
        "btn_next_league": "Go to Rating ➡️",
        "btn_next_shop": "Go to Shop ➡️", "btn_next_home": "Go to Home ➡️", "btn_next_dict": "Go to Dictionary ➡️",
        "quest_calc_done": "Quest completed! +50 XP, +10 💎", "quest_read_done": "Read completed! +20 XP, +5 💎",
        "btn_claim_calc": "🎯 Complete quest", "btn_claim_read": "💡 Get tip", "btn_share_reward": "📲 Copy and get 20 💎",
        "share_reward_done": "✅ Ad reward received!", "records_title": "🏅 Records", "rec_streak": "Max Streak",
        "rec_level": "Max Level",
        "ad_text": "Copy the text below:", "level_progress": "Progress to next level", "copy_btn": "📋 Copy text",
        "copied": "✅ Copied!",
        "view_profile": "Rival's profile", "avatar_shop": "🦉 Avatars", "avatar_desc": "Change your owl!",
        "theme_shop": "🎨 Themes", "theme_desc": "Change colors!",
        "quest_map": "🗺️ Your Path", "q_step1": "Set a goal", "q_step2": "Calculate term", "q_step3": "Read a tip",
        "q_step4": "Share result",
        "dict_title": "📖 Dictionary", "dict_desc": "Basic terms you need in life.",
        "dict_terms": {
            "Budget": "Income/expense plan.", "Assets & Liabilities": "Assets bring money, liabilities take.",
            "Income": "Active (work) and passive (interest).", "Emergency Fund": "Reserve for 3-6 months.",
            "Inflation": "Money loses value.", "Debit vs Credit Card": "Your money vs bank's money.",
            "Deposit": "Give money to bank for interest.", "Compound Interest": "Interest on interest.",
            "Investments": "Putting money to work.", "Cashback": "Returning a percentage."
        },
        "save_goal_btn": "💾 Save this goal", "my_goals": "📂 My Goals", "no_goals": "No saved goals yet.",
        "share_league_btn": "📢 Brag about your rank",
        "share_league_text": "I'm #{rank} in the Questalism Rating! Try to beat me: questalism-7uln.onrender.com",
        "safety_title": "🛡️ Emergency Fund", "safety_desc": "How much money do you need to feel safe?",
        "safety_expenses": "Monthly expenses:", "safety_months": "How many months?", "safety_result": "Your fund:",
        "safety_btn": "Calculate", "achievements_earned": "See achievements in 'Quest' section.",
        "safety_hint": "We recommend 3-6 months of living.", "made_with_love": "Made with ❤️. v1.0",
        "hide_btn": "🙈 Hide numbers", "show_btn": "👁️ Show numbers", "hide_mode_info": "Hide mode is ON.",
        "compound_title": "✨ Power of compound interest", "compound_desc": "See how money works.",
        "compound_principal": "Starting amount",
        "compound_monthly": "Monthly contribution", "compound_rate": "Annual rate, %", "compound_years": "Years",
        "compound_calc": "Calculate", "compound_with": "With compound interest", "compound_without": "Without interest",
        "compound_contributed": "Total contributed", "compound_profit": "Earned on interest",
        "compound_magic": "Magic gave you +{diff} extra!",
        "compound_chart": "Capital growth", "privacy_title": "🔒 Privacy Policy",
        "privacy_text": "Your privacy matters. We collect only name and goals. Not shared with third parties.",
        "privacy_btn": "🔒 Privacy Policy",
        "challenge_title": "🔥 Daily Challenge", "challenge_desc": "Save 100 ₽ today for your goal. It builds a habit!",
        "challenge_btn": "✅ I saved 100 ₽ (+30 XP, +30 💎)", "challenge_done": "✅ You completed today's challenge!",
        "feedback_title": "💬 Feedback", "feedback_desc": "How convenient is the site? Anything to improve?",
        "feedback_placeholder": "Write your thoughts...", "feedback_btn": "Send feedback",
        "feedback_done": "✅ Thanks for your feedback!",
        "streak_freeze_title": "🧊 Streak Freeze", "streak_freeze_desc": "Missed a day? Save your streak for 50 💎",
        "streak_freeze_btn": "Buy for 50 💎", "streak_freeze_owned": "Owned: {count} pcs.",
        "daily_quests_title": "📅 Daily Quests", "quest_login": "Log in", "quest_calc_task": "Calculate goal",
        "quest_read_task": "Read a tip",
        "quest_done": "✅ Done", "quest_not_done": "❌ Not done", "promo_title": "🎁 Promo Code",
        "promo_input": "Enter promo code", "promo_btn": "Activate",
        "promo_success": "✅ Promo activated! +100 💎", "promo_error": "❌ Invalid or already used promo code."
    }
}

# --- ПАМЯТЬ БРАУЗЕРА ---
localS = LocalStorage()
saved_name = localS.getItem("questalism_user")
saved_lang = localS.getItem("questalism_lang")

user_name = saved_name if saved_name else ""
lang_index = 1 if saved_lang == "English" else 0

# --- ОНБОРДИНГ ---
if "show_onboarding" not in st.session_state: st.session_state.show_onboarding = False
if "ob_lang" not in st.session_state: st.session_state.ob_lang = "Русский"

if not user_name:
    st.set_page_config(page_title="Questalism", page_icon="💰", layout="centered")
    st.session_state.ob_lang = st.radio("Язык / Language", ["Русский", "English"], horizontal=True)
    ob_lang = st.session_state.ob_lang

    if not st.session_state.show_onboarding:
        if ob_lang == "Русский":
            st.markdown("<h1 style='text-align: center; font-size: 50px;'>💰 Questalism</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; color: gray;'>Твоя мечта. Твой путь. Твои деньги.</h3>",
                        unsafe_allow_html=True)
            st.write("---")
            st.write("### 🎯 Что это?")
            st.write(
                "Твой личный финансовый симулятор. Узнай, как накопить на мечту, прокачай уровень и обгони друзей.")
            st.write("---")
            if st.button("Начать бесплатно 🚀", use_container_width=True, type="primary"):
                st.session_state.show_onboarding = True
                st.rerun()
        else:
            st.markdown("<h1 style='text-align: center; font-size: 50px;'>💰 Questalism</h1>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align: center; color: gray;'>Your dream. Your path. Your money.</h3>",
                        unsafe_allow_html=True)
            st.write("---")
            st.write("### 🎯 What is it?")
            st.write(
                "Your personal financial simulator. Learn how to save for a dream, level up, and beat your friends.")
            st.write("---")
            if st.button("Start for free 🚀", use_container_width=True, type="primary"):
                st.session_state.show_onboarding = True
                st.rerun()
    else:
        if ob_lang == "Русский":
            st.title("Давай познакомимся!")
            new_name = st.text_input("Введи своё имя:")
            if st.button("Начать путь 🚀", use_container_width=True):
                if new_name.strip():
                    create_user(new_name.strip())
                    localS.setItem("questalism_user", new_name.strip(), key="save_user_1")
                    localS.setItem("questalism_lang", ob_lang, key="save_lang_1")
                    st.rerun()
                else:
                    st.error("Введи имя!")
        else:
            st.title("Let's get acquainted!")
            new_name = st.text_input("Enter your name:")
            if st.button("Start 🚀", use_container_width=True):
                if new_name.strip():
                    create_user(new_name.strip())
                    localS.setItem("questalism_user", new_name.strip(), key="save_user_1")
                    localS.setItem("questalism_lang", ob_lang, key="save_lang_1")
                    st.rerun()
                else:
                    st.error("Enter name!")
    st.stop()

# Данные
stats = get_user_stats(user_name)
if stats is None:
    create_user(user_name)
    stats = get_user_stats(user_name)

(streak, last_login, xp, crystals, last_xp_date, current_theme, quest_calc, quest_read,
 level, shared, max_streak, max_level, current_avatar, chest_claimed, streak_freeze,
 daily_quest_calc, daily_quest_read, last_daily_reset) = stats

update_streak_and_xp(user_name)
(streak, last_login, xp, crystals, last_xp_date, current_theme, quest_calc, quest_read,
 level, shared, max_streak, max_level, current_avatar, chest_claimed, streak_freeze,
 daily_quest_calc, daily_quest_read, last_daily_reset) = get_user_stats(user_name)

st.set_page_config(page_title="Questalism", page_icon="💰", layout="wide")
# --- ДИЗАЙН ---
if current_theme == "neon":
    bg_css = "linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)"
    btn_color = "#ff007f"
elif current_theme == "light":
    bg_css = "linear-gradient(135deg, #e0eafc 0%, #cfdef3 100%)"
    btn_color = "#4a90e2"
elif current_theme == "space":
    bg_css = "radial-gradient(circle, #1a2a6c 0%, #b21f1f 50%, #fdbb2d 100%)"
    btn_color = "#2a2a72"
elif current_theme == "dark":
    bg_css = "linear-gradient(135deg, #232526 0%, #414345 100%)"
    btn_color = "#e0e0e0"
else:
    bg_css = "radial-gradient(circle at 10% 20%, #2b1055 0%, #000000 90%)"
    btn_color = "#6c5ce7"

text_color = "#000000" if current_theme == "light" else "#ffffff"

# --- GOOGLE ANALYTICS ---
if "localhost" not in st.context.headers.get("Host", ""):
    ga_id = "G-TXX82GHF78"
    ga_script = f"""
        <script async src="https://www.googletagmanager.com/gtag/js?id={ga_id}"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){{dataLayer.push(arguments);}}
            gtag('js', new Date());
            gtag('config', '{ga_id}');
        </script>
    """
    components.html(ga_script, height=0, width=0)

st.markdown(
    f"""
    <style>
    [data-testid="collapsedControl"] {{display: none;}}
    #MainMenu {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stApp {{ background: {bg_css}; background-attachment: fixed; color: {text_color}; }}
    h1, h2, h3, p, label, .stMarkdown {{ color: {text_color} !important; }}
    .stButton>button {{ color: white !important; background-color: {btn_color} !important; border: 1px solid {btn_color} !important; }}
    .stButton>button:hover {{ opacity: 0.8; }}
    .result-card {{ padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.3); color: white; }}
    .card-green {{ background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }}
    .card-yellow {{ background: linear-gradient(135deg, #f12711 0%, #f5af19 100%); }}
    .card-red {{ background: linear-gradient(135deg, #cb2d3e 0%, #ef473a 100%); }}
    .achievement {{ background-color: rgba(0, 255, 204, 0.1); border: 1px solid #00ffcc; padding: 10px; border-radius: 10px; margin-bottom: 10px; color: #00ffcc !important; font-weight: bold; }}
    .achievement-locked {{ background-color: rgba(128,128,128,0.1); border: 1px dashed rgba(128,128,128,0.5); padding: 10px; border-radius: 10px; margin-bottom: 10px; color: gray !important; opacity: 0.5; }}
    .quest-level {{ background: rgba(128, 128, 128, 0.2); border-left: 5px solid #ffcc00; padding: 10px; margin-bottom: 10px; border-radius: 5px; color: {text_color}; }}
    .hustle-box {{ background: rgba(128, 128, 128, 0.2); padding: 15px; border-radius: 10px; border: 1px dashed #00ffcc; text-align: center; margin-top: 10px; }}
    .profile-card {{ background: rgba(128, 128, 128, 0.2); border-radius: 15px; padding: 20px; text-align: center; border: 1px solid {btn_color}; margin-bottom: 20px; }}
    .league-row {{ display: flex; justify-content: space-between; padding: 10px; border-bottom: 1px solid rgba(128,128,128,0.3); color: {text_color}; }}
    .league-me {{ background-color: rgba(108, 92, 231, 0.3); border-radius: 5px; font-weight: bold; }}
    .shop-item {{ background: rgba(128, 128, 128, 0.1); padding: 15px; border-radius: 10px; text-align: center; border: 1px solid {btn_color}; margin-bottom: 10px; }}
    .chest-box {{ background: rgba(255, 215, 0, 0.1); padding: 15px; border-radius: 10px; border: 1px solid #ffd700; margin-top: 10px; color: {text_color}; }}
    .quest-step {{ background: rgba(128, 128, 128, 0.2); border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 15px; font-weight: bold; border: 2px solid {btn_color}; font-size: 18px; position: relative; }}
    .quest-step-done {{ background: rgba(0, 255, 204, 0.2); border: 2px solid #00ffcc; color: #00ffcc; }}
    .quest-line {{ text-align: center; font-size: 24px; margin-bottom: 15px; color: {btn_color}; }}
    .status-green {{ background-color: rgba(0, 255, 0, 0.2); border-left: 5px solid #00ff00; padding: 15px; border-radius: 5px; margin-bottom: 10px; color: {text_color}; }}
    .status-yellow {{ background-color: rgba(255, 255, 0, 0.2); border-left: 5px solid #ffff00; padding: 15px; border-radius: 5px; margin-bottom: 10px; color: {text_color}; }}
    .status-red {{ background-color: rgba(255, 0, 0, 0.2); border-left: 5px solid #ff0000; padding: 15px; border-radius: 5px; margin-bottom: 10px; color: {text_color}; }}
    .ach-icon {{ font-size: 24px; margin-right: 5px; }}
    .ach-locked {{ opacity: 0.3; filter: grayscale(100%); }}
    .ach-hint {{ font-size: 12px; color: gray; margin-top: 5px; }}
    .challenge-box {{ background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 99%, #fecfef 100%); padding: 15px; border-radius: 10px; color: #333 !important; margin-top: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
    .challenge-box b {{ color: #000 !important; }}
    .calendar-day {{ display: inline-block; width: 30px; height: 30px; line-height: 30px; text-align: center; border-radius: 50%; margin: 2px; background-color: rgba(128,128,128,0.2); font-size: 12px; }}
    .calendar-day-active {{ background-color: #00ffcc; color: #000; font-weight: bold; }}
    .quest-check {{ font-size: 20px; margin-right: 10px; }}
    </style>
    """,
    unsafe_allow_html=True
)

# --- НАВИГАЦИЯ ---
col_lang, col_space, col_streak, col_xp, col_cryst = st.columns([2, 1, 1, 1, 1])
with col_lang:
    lang = st.radio("Язык / Language", ["Русский", "English"], index=lang_index, horizontal=True,
                    label_visibility="collapsed")
t = texts[lang]

with col_streak: st.write(f"🔥 **{streak}**")
with col_xp: st.write(f"⭐ **{xp} XP**")
with col_cryst: st.write(f"💎 **{crystals}**")

if "page" not in st.session_state: st.session_state.page = "home"


def nav_button(text, page_name, current_page):
    if page_name == current_page:
        st.button(text, use_container_width=True, disabled=True, type="primary")
    else:
        if st.button(text, use_container_width=True):
            st.session_state.page = page_name
            st.rerun()


nav1, nav2, nav3, nav4, nav5, nav6 = st.columns(6)
with nav1: nav_button(t["nav_home"], "home", st.session_state.page)
with nav2: nav_button(t["nav_game"], "game", st.session_state.page)
with nav3: nav_button(t["nav_league"], "league", st.session_state.page)
with nav4: nav_button(t["nav_shop"], "shop", st.session_state.page)
with nav5: nav_button(t["nav_knowledge"], "knowledge", st.session_state.page)
with nav6: nav_button(t["nav_dictionary"], "dictionary", st.session_state.page)

# ==========================================
# СТРАНИЦА 0: ГЛАВНАЯ
# ==========================================
if st.session_state.page == "home":
    st.title(t["dash_hello"].format(name=user_name))
    col_prof, col_daily = st.columns([1, 1])
    with col_prof:
        st.markdown(f"""
        <div class="profile-card">
            <div style="font-size: 50px; margin-bottom: 10px;">{current_avatar}</div>
            <h2>👤 {t['dash_level']} {level}</h2>
            <p>{t['dash_xp']}: {xp}</p>
            <p>🔥 {t['streak_label']}: {streak} {t['days']} (🧊 {streak_freeze})</p>
            <p>💎 {t['crystals_label']}: {crystals}</p>
        </div>
        """, unsafe_allow_html=True)

        xp_for_next = (level * 100) - xp
        st.write(f"{t['level_progress']}: {xp % 100} / 100 ({xp_for_next} XP left)")
        st.progress((xp % 100) / 100)

        # Календарь активности (последние 7 дней)
        st.write("---")
        st.write("📅 Активность за 7 дней:")
        today = date.today()
        cols_cal = st.columns(7)
        for i in range(7):
            day = today - timedelta(days=6 - i)
            day_str = day.strftime("%d")
            # Простая логика: если стрик больше i, то день активен
            is_active = (6 - i) < streak
            css_class = "calendar-day calendar-day-active" if is_active else "calendar-day"
            with cols_cal[i]:
                st.markdown(f'<div class="{css_class}">{day_str}</div>', unsafe_allow_html=True)

        st.write("---")
        st.subheader(t["daily_quests_title"])
        # Сброс заданий, если новый день
        today_str = date.today().isoformat()
        if last_daily_reset != today_str:
            with engine.begin() as conn:
                conn.execute(text(
                    "UPDATE users SET daily_quest_calc = FALSE, daily_quest_read = FALSE, last_daily_reset = :d WHERE name = :name"),
                             {"d": today_str, "name": user_name})
            st.rerun()

        st.markdown(f"{'✅' if True else '❌'} {t['quest_login']}")
        st.markdown(f"{'✅' if daily_quest_calc else '❌'} {t['quest_calc_task']}")
        st.markdown(f"{'✅' if daily_quest_read else '❌'} {t['quest_read_task']}")

        if daily_quest_calc and daily_quest_read:
            st.success("🎁 Все задания выполнены! Бонус +50 XP")
            # Здесь можно добавить логику единоразовой выдачи бонуса, чтобы не спамили

        st.write("---")
        st.subheader(t["records_title"])
        st.write(f"🏆 {t['rec_streak']}: {max_streak}")
        st.write(f"⭐ {t['rec_level']}: {max_level}")

        today_str = date.today().isoformat()
        with engine.connect() as conn:
            last_challenge = conn.execute(text("SELECT last_challenge_date FROM users WHERE name = :name"),
                                          {"name": user_name}).fetchone()[0]

        st.write("---")
        st.markdown(f"""
        <div class="challenge-box">
            <h3>🔥 {t['challenge_title']}</h3>
            <p>{t['challenge_desc']}</p>
        </div>
        """, unsafe_allow_html=True)

        if last_challenge != today_str:
            if st.button(t["challenge_btn"], key="claim_challenge", use_container_width=True):
                claim_daily_challenge(user_name)
                st.balloons()
                st.rerun()
        else:
            st.success(t["challenge_done"])

    with col_daily:
        st.subheader(t["quest_map"])

        if quest_calc == 0:
            st.info(f"1️⃣ {t['q_step1']}")
            st.info(f"2️⃣ {t['q_step2']}")
        else:
            st.success(f"✅ {t['q_step1']}")
            st.success(f"✅ {t['q_step2']}")

        if quest_read == 0:
            st.info(f"3️⃣ {t['q_step3']}")
        else:
            st.success(f"✅ {t['q_step3']}")

        if shared == 0:
            st.info(f"4️⃣ {t['q_step4']}")
        else:
            st.success(f"✅ {t['q_step4']}")

    st.write("---")
    if st.button(t["privacy_btn"], use_container_width=True):
        st.session_state.page = "privacy"
        st.rerun()

    if st.button(t["btn_next_game"], use_container_width=True):
        st.session_state.page = "game"
        st.rerun()

# ==========================================
# СТРАНИЦА 2: ЛИГА (С ПРОФИЛЕМ СОПЕРНИКА)
# ==========================================
elif st.session_state.page == "league":
    st.title(t["league_title"])
    st.write(t["league_desc"])

    all_players = get_leaderboard()

    st.write("---")
    for rank, (name, p_xp, p_avatar) in enumerate(all_players, start=1):
        if name == user_name:
            my_rank = rank

        row_class = "league-me" if name == user_name else ""
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}."

        st.markdown(f"""
        <div class="league-row {row_class}">
            <span>{medal} {p_avatar} {name}</span>
            <span>⭐ {p_xp} XP</span>
        </div>
        """, unsafe_allow_html=True)

        if name != user_name:
            with st.expander(f"👀 {t['view_profile']} ({name})"):
                opp_stats = get_opponent_stats(name)
                if opp_stats:
                    o_xp, o_crys, o_streak, o_av = opp_stats
                    col_o1, col_o2, col_o3 = st.columns(3)
                    col_o1.metric("XP", o_xp)
                    col_o2.metric("💎", o_crys)
                    col_o3.metric("🔥", f"{o_streak} {t['days']}")
                    st.write(f"Аватар: {o_av}")

    st.write("---")

    if 'my_rank' not in locals():
        my_rank = len(all_players)

    league_share_text = t["share_league_text"].format(rank=my_rank)

    st.write(t["share_league_btn"])
    st.code(league_share_text, language="text")

    if shared == 1:
        st.success(t["share_reward_done"])
    else:
        if st.button(t["btn_share_reward"], use_container_width=True):
            complete_quest(user_name, "share", 0, 20)
            st.success("+20 💎")
            st.rerun()

    st.write("---")
    if st.button(t["btn_next_shop"], use_container_width=True):
        st.session_state.page = "shop"
        st.rerun()

# ==========================================
# СТРАНИЦА 1: ИГРА (КВЕСТ)
# ==========================================
elif st.session_state.page == "game":
    if "goal" not in st.session_state: st.session_state.goal = "iPhone"
    if "target" not in st.session_state: st.session_state.target = 80000
    if "current" not in st.session_state: st.session_state.current = 5000
    if "monthly" not in st.session_state: st.session_state.monthly = 500
    if "extra" not in st.session_state: st.session_state.extra = 0
    if "hide_numbers" not in st.session_state: st.session_state.hide_numbers = False

    col_hide1, col_hide2 = st.columns([3, 1])
    with col_hide2:
        if st.button(t["hide_btn"] if not st.session_state.hide_numbers else t["show_btn"], use_container_width=True):
            st.session_state.hide_numbers = not st.session_state.hide_numbers
            st.rerun()

    if not st.session_state.hide_numbers:
        user_type = st.radio(t["who"], [t["teen"], t["adult"]], horizontal=True)
        if lang == "Русский":
            if user_type == t["teen"]:
                jobs = [("Нет", 0), ("Промоутер", 3000), ("Курьер", 8000), ("Репетитор", 10000), ("Официант", 12000),
                        ("Фриланс", 15000), ("Мойка машин", 7000), ("Выгул собак", 5000), ("Помощь с уроками", 6000),
                        ("Продажа вещей", 4000), ("Стриминг", 3000), ("Своя подработка", 0)]
            else:
                jobs = [("Нет", 0), ("Врач", 80000), ("Учитель", 50000), ("Инженер", 70000), ("Программист", 100000),
                        ("Менеджер", 60000), ("Дизайнер", 65000), ("Маркетолог", 55000), ("Бухгалтер", 50000),
                        ("Юрист", 90000), ("Своя работа", 0)]
        else:
            if user_type == t["teen"]:
                jobs = [("None", 0), ("Promoter", 3000), ("Courier", 8000), ("Tutor", 10000), ("Waiter", 12000),
                        ("Freelance", 15000), ("Car wash", 7000), ("Dog walking", 5000), ("Homework help", 6000),
                        ("Selling stuff", 4000), ("Streaming", 3000), ("Own part-time job", 0)]
            else:
                jobs = [("None", 0), ("Doctor", 80000), ("Teacher", 50000), ("Engineer", 70000), ("Programmer", 100000),
                        ("Manager", 60000), ("Designer", 65000), ("Marketer", 55000), ("Accountant", 50000),
                        ("Lawyer", 90000), ("Own work", 0)]

        st.header(t["goal_header"])
        col1, col2 = st.columns(2)
        with col1:
            st.session_state.goal = st.text_input(t["goal_input"], st.session_state.goal)
        with col2:
            currency = st.selectbox(t["currency"], [t["rub"], t["usd"]])
        is_usd = (currency == t["usd"])
        symbol = "$" if is_usd else "₽"
        rate = 90 if is_usd else 1

        st.session_state.target = st.number_input(f"{t['target']} ({symbol})", min_value=0,
                                                  value=st.session_state.target, step=1000)

        st.header(t["data_header"])
        st.session_state.current = st.number_input(f"{t['current']} ({symbol})", min_value=0,
                                                   value=st.session_state.current, step=1000)
        st.write(t["monthly"])

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            b0 = st.button("100")
        with col2:
            b1 = st.button("500")
        with col3:
            b2 = st.button("1000")
        with col4:
            b3 = st.button("2000")
        col5, col6, col7 = st.columns(3)
        with col5:
            b4 = st.button("3000")
        with col6:
            b5 = st.button("5000")
        with col7:
            b6 = st.button(t["custom"])

        if "custom_mode" not in st.session_state: st.session_state.custom_mode = False
        if b0: st.session_state.monthly, st.session_state.custom_mode = 100, False
        if b1: st.session_state.monthly, st.session_state.custom_mode = 500, False
        if b2: st.session_state.monthly, st.session_state.custom_mode = 1000, False
        if b3: st.session_state.monthly, st.session_state.custom_mode = 2000, False
        if b4: st.session_state.monthly, st.session_state.custom_mode = 3000, False
        if b5: st.session_state.monthly, st.session_state.custom_mode = 5000, False
        if b6: st.session_state.custom_mode = True

        if st.session_state.custom_mode:
            custom = st.number_input(t["custom_input"], min_value=1, value=st.session_state.monthly, step=100)
            st.session_state.monthly = custom

        st.header(t["jobs_header"])
        if st.button(t["hustle_btn"]):
            idea, income = random.choice(t["hustles"])
            st.markdown(
                f'<div class="hustle-box">💡 {t["hustle_result"].format(idea=idea, income=income, symbol=symbol)}</div>',
                unsafe_allow_html=True)

        job_choice = st.selectbox(t["choose"], [j[0] for j in jobs])
        base_salary = next((j[1] for j in jobs if j[0] == job_choice), 0)
        if is_usd: base_salary = base_salary / rate

        if job_choice in [t["own_job"]]:
            st.session_state.extra = st.number_input(f"{t['salary']} ({symbol})", min_value=0,
                                                     value=st.session_state.extra, step=1000)
        elif job_choice != t["no"]:
            st.session_state.extra = st.number_input(f"{t['salary']} ({symbol})", min_value=0, value=int(base_salary),
                                                     step=1000)
        else:
            st.session_state.extra = 0
        symbol_display = symbol
        total_monthly = st.session_state.monthly + st.session_state.extra
    else:
        st.info(t["hide_mode_info"])
        symbol_display = "₽"
        user_type = t["teen"]
        total_monthly = st.session_state.monthly + st.session_state.extra

    st.header(t["result"])

    if st.session_state.target <= 0:
        st.error("Цель не может быть равна 0." if lang == "Русский" else "Goal cannot be 0.")
    elif st.session_state.target <= st.session_state.current:
        st.success(t["goal_reached"])
    elif total_monthly > 0:
        months = (st.session_state.target - st.session_state.current) / total_monthly
        years = months / 12
        inflation = 0.06
        real_target = st.session_state.target * ((1 + inflation) ** years)

        if months <= 6:
            card_class = "card-green"
        elif months <= 18:
            card_class = "card-yellow"
        else:
            card_class = "card-red"

        goal_display = st.session_state.goal if not st.session_state.hide_numbers else "***"
        target_display = f"{st.session_state.target:,.0f} {symbol_display}" if not st.session_state.hide_numbers else "***"
        months_text = f"{months:.0f} {t['months']}" if not st.session_state.hide_numbers else "***"

        st.markdown(f"""
        <div class="result-card {card_class}">
            <h2 style="margin:0;">🎯 {goal_display}: {target_display}</h2>
            <h3 style="margin:10px 0 0 0;">⏱️ {months_text}</h3>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.metric(t["target_label"], target_display)
        with col2:
            real_target_display = f"{real_target:,.0f} {symbol_display}" if not st.session_state.hide_numbers else "***"
            st.metric(t["inflation_label"], real_target_display)

        if months <= 6:
            st.markdown(f'<div class="status-green">{t["status_green"]}</div>', unsafe_allow_html=True)
        elif months <= 18:
            st.markdown(f'<div class="status-yellow">{t["status_yellow"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-red">{t["status_red"]}</div>', unsafe_allow_html=True)

        data = []
        balance = st.session_state.current
        for m in range(int(months) + 1):
            data.append({t["chart_month"]: m, t["chart_balance"]: balance})
            balance += total_monthly
        df = pd.DataFrame(data)
        st.line_chart(df.set_index(t["chart_month"])[t["chart_balance"]], color=btn_color)
        progress = min(st.session_state.current / st.session_state.target, 1.0)
        st.progress(progress)
        if not st.session_state.hide_numbers: st.write(f"{t['you_at']} {progress * 100:.1f}{t['to_goal']}")

        if not st.session_state.hide_numbers:
            if st.button(t["save_goal_btn"], use_container_width=True):
                save_goal_to_db(user_name, st.session_state.goal, st.session_state.target, st.session_state.current)
                st.success("Цель сохранена!" if lang == "Русский" else "Goal saved!")
                st.rerun()

        st.header(t["quest_levels"])


        def milestone_status(percentage):
            return t["milestone_done"] if progress >= percentage else t["milestone_wait"]


        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_10"]}</b> ({st.session_state.target * 0.1:,.0f} {symbol_display}) — {milestone_status(0.1)}</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_25"]}</b> ({st.session_state.target * 0.25:,.0f} {symbol_display}) — {milestone_status(0.25)}</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_50"]}</b> ({st.session_state.target * 0.5:,.0f} {symbol_display}) — {milestone_status(0.5)}</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_75"]}</b> ({st.session_state.target * 0.75:,.0f} {symbol_display}) — {milestone_status(0.75)}</div>',
            unsafe_allow_html=True)
        st.markdown(
            f'<div class="quest-level"><b>{t["milestone_100"]}</b> ({st.session_state.target:,.0f} {symbol_display}) — {milestone_status(1.0)}</div>',
            unsafe_allow_html=True)

        st.header(t["achievements"])
        ach_conditions = [
            (progress > 0.01, t["ach1"]), (total_monthly >= 1000, t["ach2"]), (progress >= 0.25, t["ach3"]),
            (progress >= 0.5, t["ach4"]), (progress >= 0.75, t["ach5"]), (months >= 12, t["ach6"]),
            (months < 6, t["ach7"]), (st.session_state.extra > 0, t["ach8"]), (total_monthly >= 10000, t["ach9"]),
            (user_type == t["teen"], t["ach10"]),
        ]
        for unlocked, text_ach in ach_conditions:
            css_class = "achievement" if unlocked else "achievement-locked"
            st.markdown(f'<div class="{css_class}">{text_ach}</div>', unsafe_allow_html=True)

        if st.session_state.extra == 0:
            st.info(f"{t['next_step']} {t['next_step_1']}")
        else:
            st.success(f"{t['next_step']} {t['next_step_2']}")

        st.write("---")

        st.subheader(t["compound_title"])
        st.write(t["compound_desc"])
        cc1, cc2 = st.columns(2)
        with cc1:
            c_principal = st.number_input(t["compound_principal"], min_value=0, value=10000, step=1000, key="cc_p")
            c_rate = st.number_input(t["compound_rate"], min_value=0.0, max_value=100.0, value=10.0, step=0.5,
                                     key="cc_r")
        with cc2:
            c_monthly = st.number_input(t["compound_monthly"], min_value=0, value=1000, step=500, key="cc_m")
            c_years = st.number_input(t["compound_years"], min_value=1, max_value=50, value=10, step=1, key="cc_y")

        if st.button(t["compound_calc"], key="cc_btn", use_container_width=True):
            total, contributed, balances = calc_compound(c_principal, c_monthly, c_rate, c_years)
            profit = total - contributed

            ccol1, ccol2 = st.columns(2)
            with ccol1:
                st.metric(t["compound_with"], f"{total:,.0f} ₽")
            with ccol2:
                st.metric(t["compound_without"], f"{contributed:,.0f} ₽")
            ccol3, ccol4 = st.columns(2)
            with ccol3:
                st.metric(t["compound_contributed"], f"{contributed:,.0f} ₽")
            with ccol4:
                st.metric(t["compound_profit"], f"{profit:,.0f} ₽")

            st.success(t["compound_magic"].format(diff=f"{profit:,.0f} ₽"))

            if balances:
                df_cc = pd.DataFrame(balances, columns=[t["compound_years"], t["compound_chart"]])
                df_cc = df_cc.set_index(t["compound_years"])
                st.line_chart(df_cc, color=btn_color)

        st.write("---")

        if quest_calc == 1:
            st.success(t["quest_calc_done"])
        else:
            if st.button(t["btn_claim_calc"], use_container_width=True):
                complete_quest(user_name, "calc", 50, 10)
                st.balloons()
                st.rerun()

        st.write("---")

        st.write(t["ad_text"])
        share_msg = t["share_text"].format(goal=st.session_state.goal, months=f"{months:.0f}")
        st.code(share_msg, language="text")

        if shared == 1:
            st.success(t["share_reward_done"])
        else:
            if st.button(t["btn_share_reward"], use_container_width=True):
                complete_quest(user_name, "share", 0, 20)
                st.success("+20 💎")
                st.rerun()

        st.write("---")
    else:
        st.warning(t["warning"])

    st.write("---")
    st.subheader(t["my_goals"])
    my_goals = get_saved_goals(user_name)
    if not my_goals:
        st.info(t["no_goals"])
    else:
        for g_id, g_name, g_target, g_saved in my_goals:
            progress_g = min(g_saved / g_target, 1.0) if g_target > 0 else 0
            st.write(f"{g_name} — {g_saved:,.0f} / {g_target:,.0f} ({progress_g * 100:.1f}%)")
            st.progress(progress_g)
            if st.button("Удалить" if lang == "Русский" else "Delete", key=f"del_{g_id}"):
                delete_goal(g_id)
                st.rerun()

    st.write("---")
    st.subheader(t["safety_title"])
    st.write(t["safety_desc"])
    col1, col2 = st.columns(2)
    with col1:
        expenses = st.number_input(t["safety_expenses"], min_value=0, value=15000, step=1000)
    with col2:
        months_safety = st.number_input(t["safety_months"], min_value=1, value=3, step=1)
    if st.button(t["safety_btn"]):
        safety_fund = expenses * months_safety
        st.success(f"{t['safety_result']} **{safety_fund:,.0f} ₽**")
    st.caption(t["safety_hint"])

    st.write("---")
    # --- NPS БЛОК ---
    st.subheader(t["feedback_title"])
    st.write(t["feedback_desc"])

    with st.form("feedback_form"):
        col_f1, col_f2 = st.columns([1, 1])
        with col_f1:
            rating = st.radio("Оцени сайт:", ["👍 Отлично", "👎 Есть проблемы"], horizontal=True,
                              label_visibility="collapsed")
        with col_f2:
            fb_text = st.text_input(t["feedback_placeholder"], label_visibility="collapsed")

        submitted = st.form_submit_button(t["feedback_btn"])
        if submitted:
            save_feedback(user_name, f"{rating} - {fb_text}")
            st.success(t["feedback_done"])

    st.write("---")
    if st.button(t["btn_next_league"], use_container_width=True):
        st.session_state.page = "league"
        st.rerun()

# ==========================================
# СТРАНИЦА 3: МАГАЗИН
# ==========================================
elif st.session_state.page == "shop":
    st.title(t["shop_title"])
    st.write(t["shop_desc"])

    # Промокод
    st.subheader(t["promo_title"])
    col_p1, col_p2 = st.columns([3, 1])
    with col_p1:
        promo_input = st.text_input(t["promo_input"], label_visibility="collapsed", placeholder="START2026")
    with col_p2:
        if st.button(t["promo_btn"], use_container_width=True):
            if apply_promo(user_name, promo_input.strip()):
                st.success(t["promo_success"])
                st.rerun()
            else:
                st.error(t["promo_error"])

    st.write("---")
    # Заморозка стрика
    st.subheader(t["streak_freeze_title"])
    st.write(t["streak_freeze_desc"])
    st.write(f"{t['streak_freeze_owned'].format(count=streak_freeze)}")
    if st.button(t["streak_freeze_btn"], use_container_width=True):
        if buy_streak_freeze(user_name):
            st.success("Куплено!" if lang == "Русский" else "Purchased!")
            st.rerun()
        else:
            st.error(t["not_enough"])

    st.write("---")
    st.subheader(t["avatar_shop"])
    st.write(t["avatar_desc"])

    avatars = [("🦉", 0), ("🐱", 30), ("🐶", 30), ("🦊", 50), ("🐼", 50), ("🐸", 100)]
    cols = st.columns(3)
    for i, (av_emoji, cost) in enumerate(avatars):
        with cols[i % 3]:
            if current_avatar == av_emoji:
                st.button(f"{av_emoji} {t['owned_btn']}", key=f"av_{av_emoji}", disabled=True, use_container_width=True)
            else:
                if st.button(f"{av_emoji} {t['buy_btn'].format(cost=cost)}", key=f"av_{av_emoji}",
                             use_container_width=True):
                    if buy_avatar(user_name, av_emoji, cost):
                        st.success("Куплено!" if lang == "Русский" else "Purchased!")
                        st.rerun()
                    else:
                        st.error(t["not_enough"])

    st.write("---")
    st.subheader(t["theme_shop"])
    st.write(t["theme_desc"])

    col1, col2, col3 = st.columns(3)
    themes = [
        ("default", t["theme_default"], 0),
        ("light", t["theme_light"], 35),
        ("neon", t["theme_neon"], 50),
        ("space", t["theme_space"], 100),
        ("dark", t["theme_dark"], 0)
    ]

    for i, (theme_id, theme_name, cost) in enumerate(themes):
        col = [col1, col2, col3, col1, col2][i]
        with col:
            st.markdown(f"""
            <div class="shop-item">
                <h3>{theme_name}</h3>
                <p>{t['cost_label'].format(cost=cost)}</p>
            </div>
            """, unsafe_allow_html=True)
            if current_theme == theme_id:
                st.button(t["owned_btn"], key=f"btn_{theme_id}", disabled=True, use_container_width=True)
            else:
                if st.button(t["buy_btn"].format(cost=cost), key=f"btn_{theme_id}", use_container_width=True):
                    if buy_theme(user_name, theme_id, cost):
                        st.success("Куплено!" if lang == "Русский" else "Purchased!")
                        st.rerun()
                    else:
                        st.error(t["not_enough"])

    st.write("---")
    if st.button(t["btn_next_knowledge"], use_container_width=True):
        st.session_state.page = "knowledge"
        st.rerun()

# ==========================================
# СТРАНИЦА 4: БАЗА ЗНАНИЙ
# ==========================================
elif st.session_state.page == "knowledge":
    if "current_tip" not in st.session_state:
        st.session_state.current_tip = None

    st.header(t["speed_up"])
    st.info(
        "Введи данные в разделе 'Твой квест', чтобы увидеть персональные расчеты." if lang == "Русский" else "Enter data in 'Your Quest' to see personalized calculations.")

    with st.expander(t["why_save"], expanded=True):
        st.write(t["why1"])
        st.write(t["why2"])
        st.write(t["why3"])
        st.write(t["why4"])

    with st.expander(t["spend_less"]):
        st.write(t["spend1"])
        st.write(t["spend2"])
        st.write(t["spend3"])
        st.write(t["spend4"])
        st.write(t["spend5"])

    with st.expander(t["psychology"]):
        st.write(t["psy1"])
        st.write(t["psy2"])
        st.write(t["psy3"])
        st.write(t["psy4"])
        st.write(t["psy5"])

    st.divider()
    st.header(t["feature"])

    if quest_read == 1:
        st.success(t["quest_read_done"])
        if st.session_state.current_tip:
            st.success(f"💡 {st.session_state.current_tip}")
    else:
        if st.button(t["btn_claim_read"]):
            st.session_state.current_tip = random.choice(t["tips"])
            complete_quest(user_name, "read", 20, 5)
            st.balloons()
            st.rerun()

        if st.session_state.current_tip:
            st.success(f"💡 {st.session_state.current_tip}")

    st.write("---")
    if st.button(t["btn_next_dict"], use_container_width=True):
        st.session_state.page = "dictionary"
        st.rerun()

# ==========================================
# СТРАНИЦА 5: СЛОВАРЬ
# ==========================================
elif st.session_state.page == "dictionary":
    st.title(t["dict_title"])
    st.write(t["dict_desc"])
    st.divider()

    current_terms = texts[lang]["dict_terms"]
    for term, definition in current_terms.items():
        st.markdown(f"**{term}**: {definition}")

    st.write("---")
    st.success(t["wish"])

    if st.button(t["btn_next_home"], use_container_width=True):
        st.session_state.page = "home"
        st.rerun()

    st.caption(t["made_with_love"])

# ==========================================
# СТРАНИЦА 6: КОНФИДЕНЦИАЛЬНОСТЬ
# ==========================================
elif st.session_state.page == "privacy":
    st.title(t["privacy_title"])
    st.markdown(t["privacy_text"])

    st.write("---")
    if st.button(t["btn_next_home"], use_container_width=True):
        st.session_state.page = "home"
        st.rerun()

    st.caption(t["made_with_love"])
