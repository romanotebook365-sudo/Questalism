import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Questalism", page_icon="💰", layout="wide")

# --- НОВЫЙ ДИЗАЙН (ФИОЛЕТОВО-СИНИЙ ГРАДИЕНТ + СЕТКА) ---
st.markdown(
    """
    <style>
    /* Градиентный фон */
    .stApp {
        background: radial-gradient(circle at 10% 20%, #2b1055 0%, #000000 90%);
        background-attachment: fixed;
        color: white;
    }
    
    /* Эффект сетки поверх фона */
    .stApp::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background-image: linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
        background-size: 30px 30px;
        z-index: -1;
        pointer-events: none;
    }

    h1, h2, h3, p, label, .stMarkdown {
        color: #ffffff !important;
    }
    
    /* Карточка результата */
    .result-card {
        background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 100%); /* Яркий градиент для карточки */
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 20px rgba(255, 65, 108, 0.3);
    }
    
    /* Ачивка */
    .achievement {
        background-color: rgba(0, 255, 204, 0.1);
        border: 1px solid #00ffcc;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        color: #00ffcc !important;
        font-weight: bold;
    }

    /* Веха квеста */
    .quest-level {
        background: rgba(255, 255, 255, 0.05);
        border-left: 5px solid #ffcc00;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 5px;
    }

    /* Кнопка подработки */
    .hustle-box {
        background: rgba(255, 255, 255, 0.1);
        padding: 15px;
        border-radius: 10px;
        border: 1px dashed #00ffcc;
        text-align: center;
        margin-top: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- ЯЗЫК ---
lang = st.sidebar.radio("Язык / Language", ["Русский", "English"])

# --- СТРИК (ДНИ ПОДРЯД) ---
if "streak" not in st.session_state:
    st.session_state.streak = 1 # Имитация стрика (в будущем - из базы данных)

texts = {
    "Русский": {
        "title": "💰 Questalism",
        "subtitle": "Твоя мечта. Твой путь. Твои деньги.",
        "nav_game": "🎮 Твой квест",
        "nav_knowledge": "📚 База знаний",
        "streak": f"🔥 Стрик: {st.session_state.streak} дн.",
        "who": "Кто ты?",
        "teen": "Подросток",
        "adult": "Взрослый",
        "age": "Сколько тебе лет?",
        "goal_header": "1. Твоя цель",
        "goal_input": "На что копишь?",
        "currency": "Валюта",
        "rub": "Рубли (₽)",
        "usd": "Доллары ($)",
        "target": "Сколько стоит?",
        "data_header": "2. Твои данные",
        "current": "Сколько есть сейчас?",
        "monthly": "**Сколько можешь откладывать в месяц?**",
        "custom": "Своё",
        "custom_input": "Введи сумму:",
        "jobs_header": "3. Твоя подработка",
        "choose": "Выбери",
        "no": "Нет",
        "own_job": "Своя подработка",
        "salary": "Сколько ты зарабатываешь?",
        "result": "🏆 Твой результат",
        "target_label": "Цель",
        "term_label": "Срок",
        "inflation_label": "С инфляцией",
        "inflation_info": "Инфляция — это подорожание денег в будущем.",
        "months": "мес.",
        "chart_month": "Месяц",
        "chart_balance": "Баланс",
        "you_at": "Ты на",
        "to_goal": "% к цели",
        "achievements": "🎖️ Твои ачивки",
        "quest_levels": "🛡️ Твои вехи (Этапы)",
        "reminder": "📅 Напоминание",
        "reminder1": "Откладывай **1-го числа** каждого месяца.",
        "reminder2": "Проверяй прогресс **каждое воскресенье**.",
        "reminder3": "Пересматривай цель **раз в месяц**.",
        "speed_up": "🚀 Как ускорить цель",
        "if_more": "Если откладывать на",
        "more": "больше → срок:",
        "need_daily": "Нужно откладывать в день:",
        "wish": "Удачи! Ты справишься. 💪",
        "warning": "Введи сумму больше 0.",
        "goal_reached": "Ты уже накопил на эту цель! 🎉",
        "status_green": "🟢 **Реально!** Ты достигнешь цели быстро.",
        "status_yellow": "🟡 **Средне.** Придется постараться.",
        "status_red": "🔴 **Долго.** Подумай, как увеличить доход.",
        "next_step": "👉 **Следующий шаг:**",
        "next_step_1": "Попробуй добавить подработку, чтобы сократить срок.",
        "share_btn": "📲 Поделиться результатом",
        "share_text": "Я накоплю на {goal} за {months} месяцев с Questalism! А ты сможешь? Проверь свои финансы: questalism.onrender.com",
        "hustle_header": "💡 Не знаешь, где взять деньги?",
        "hustle_btn": "Сгенерировать идею",
        "hustle_result": "Тебе подойдет: {idea}. Примерный доход: {income} {symbol}.",
        "hustles": [
            ("Выгул собак", 5000), ("Помощь с уроками", 6000), 
            ("Курьер на велосипеде", 8000), ("Стриминг игр", 3000),
            ("Продажа старых вещей", 4000), ("Репетиторство", 10000),
            ("Помощь с компьютером", 7000), ("Оцифровка документов", 6000)
        ],
        "ach1": "🎯 **Первый шаг** — ты начал копить.",
        "ach2": "💎 **Сберегатель** — откладываешь больше 1000 в месяц.",
        "ach3": "🥇 **Четверть пути** — ты прошёл 25% к цели.",
        "ach4": "🔥 **Половина** — ты на середине пути.",
        "ach5": "⭐ **Почти у цели** — осталось 25%.",
        "ach6": "🏆 **Марафонец** — твоя цель на год и больше.",
        "ach7": "🚀 **Спринтер** — ты достигнешь цели за полгода.",
        "ach8": "💪 **Работяга** — у тебя есть дополнительный доход.",
        "ach9": "👑 **Высокий доход** — ты зарабатываешь больше 10K.",
        "ach10": "🎓 **Школьник** — ты учишься и копишь одновременно.",
        "milestone_10": "10% — Первый шаг к мечте",
        "milestone_25": "25% — Четверть пути пройдена",
        "milestone_50": "50% — Экватор! Ты на середине",
        "milestone_75": "75% — Уже виден финиш",
        "milestone_100": "100% — Финальный босс: покупка!",
        "milestone_done": "✅ Пройдено",
        "milestone_wait": "🔒 Впереди",
        "why_save": "8. Почему важно копить",
        "why1": "• Финансовая свобода — ты не зависишь от других.",
        "why2": "• Мечты сбываются — ты достигаешь целей.",
        "why3": "• Уверенность — ты знаешь, что справишься.",
        "why4": "• Будущее — ты строишь базу для жизни.",
        "spend_less": "9. Как меньше тратить",
        "spend1": "• Правило 24 часов — подожди день перед покупкой.",
        "spend2": "• Список покупок — не ходи в магазин без него.",
        "spend3": "• Кофе дома — экономия каждый день.",
        "spend4": "• Подписки — проверь, что не используешь.",
        "spend5": "• Импульс — не покупай на эмоциях.",
        "psychology": "10. Психология накоплений",
        "psy1": "• Автоматизация — откладывай сразу при доходе.",
        "psy2": "• Визуализация — смотри на цель каждый день.",
        "psy3": "• Маленькие шаги — лучше 100, чем 0.",
        "psy4": "• Поддержка — расскажи другу о цели.",
        "psy5": "• Прощение — если сорвался, продолжай.",
        "dictionary": "11. Словарь терминов",
        "feature": "💡 Совет дня",
        "feature_btn": "Получить совет",
        "tips": [
            "Начни с 100 рублей. Главное — начать.",
            "Запиши цель на бумаге. Это повышает шансы на 42%.",
            "Сравни себя с собой вчерашним, а не с другими.",
            "Отложи 10% с любого дохода. Сразу.",
            "Не жди понедельника. Начни сегодня."
        ]
    },
    "English": {
        "title": "💰 Questalism",
        "subtitle": "Your dream. Your path. Your money.",
        "nav_game": "🎮 Your Quest",
        "nav_knowledge": "📚 Knowledge Base",
        "streak": f"🔥 Streak: {st.session_state.streak} days",
        "who": "Who are you?",
        "teen": "Teenager",
        "adult": "Adult",
        "age": "How old are you?",
        "goal_header": "1. Your goal",
        "goal_input": "What are you saving for?",
        "currency": "Currency",
        "rub": "Rubles (₽)",
        "usd": "Dollars ($)",
        "target": "How much does it cost?",
        "data_header": "2. Your data",
        "current": "How much do you have now?",
        "monthly": "**How much can you save per month?**",
        "custom": "Custom",
        "custom_input": "Enter amount:",
        "jobs_header": "3. Your part-time job",
        "choose": "Choose",
        "no": "None",
        "own_job": "Own part-time job",
        "salary": "How much do you earn?",
        "result": "🏆 Your result",
        "target_label": "Goal",
        "term_label": "Term",
        "inflation_label": "With inflation",
        "inflation_info": "Inflation is the rise in prices in the future.",
        "months": "mo.",
        "chart_month": "Month",
        "chart_balance": "Balance",
        "you_at": "You are at",
        "to_goal": "% to goal",
        "achievements": "🎖️ Your achievements",
        "quest_levels": "🛡️ Milestones",
        "reminder": "📅 Reminder",
        "reminder1": "Save on the **1st of each month**.",
        "reminder2": "Check progress **every Sunday**.",
        "reminder3": "Review your goal **once a month**.",
        "speed_up": "🚀 How to speed up",
        "if_more": "If you save",
        "more": "more → term:",
        "need_daily": "Need to save daily:",
        "wish": "Good luck! You can do it. 💪",
        "warning": "Enter an amount greater than 0.",
        "goal_reached": "You have already saved enough for this goal! 🎉",
        "status_green": "🟢 **Realistic!** You will reach your goal fast.",
        "status_yellow": "🟡 **Medium.** You will need to try hard.",
        "status_red": "🔴 **Long.** Think about how to increase income.",
        "next_step": "👉 **Next step:**",
        "next_step_1": "Try adding a part-time job to shorten the term.",
        "share_btn": "📲 Share result",
        "share_text": "I will save up for {goal} in {months} months with Questalism! Can you? Check your finances: questalism.onrender.com",
        "hustle_header": "💡 Don't know where to get money?",
        "hustle_btn": "Generate idea",
        "hustle_result": "Try this: {idea}. Expected income: {income} {symbol}.",
        "hustles": [
            ("Dog walking", 5000), ("Homework help", 6000), 
            ("Bike courier", 8000), ("Game streaming", 3000),
            ("Selling old stuff", 4000), ("Tutoring", 10000),
            ("PC help", 7000), ("Document digitizing", 6000)
        ],
        "ach1": "🎯 **First step** — you started saving.",
        "ach2": "💎 **Saver** — you save more than 1000 per month.",
        "ach3": "🥇 **Quarter way** — you passed 25% of your goal.",
        "ach4": "🔥 **Halfway** — you are in the middle.",
        "ach5": "⭐ **Almost there** — 25% left.",
        "ach6": "🏆 **Marathoner** — your goal is for a year or more.",
        "ach7": "🚀 **Sprinter** — you'll reach your goal in half a year.",
        "ach8": "💪 **Hard worker** — you have extra income.",
        "ach9": "👑 **High income** — you earn more than 10K.",
        "ach10": "🎓 **Student** — you study and save at the same time.",
        "milestone_10": "10% — First step to the dream",
        "milestone_25": "25% — Quarter of the way",
        "milestone_50": "50% — Halfway there!",
        "milestone_75": "75% — The finish is visible",
        "milestone_100": "100% — Final boss: the purchase!",
        "milestone_done": "✅ Completed",
        "milestone_wait": "🔒 Ahead",
        "why_save": "8. Why saving matters",
        "why1": "• Financial freedom — you don't depend on others.",
        "why2": "• Dreams come true — you reach your goals.",
        "why3": "• Confidence — you know you can do it.",
        "why4": "• Future — you build a foundation for life.",
        "spend_less": "9. How to spend less",
        "spend1": "• 24-hour rule — wait a day before buying.",
        "spend2": "• Shopping list — don't go without it.",
        "spend3": "• Coffee at home — save every day.",
        "spend4": "• Subscriptions — check what you don't use.",
        "spend5": "• Impulse — don't buy on emotions.",
        "psychology": "10. Psychology of saving",
        "psy1": "• Automation — save immediately when you get paid.",
        "psy2": "• Visualization — look at your goal every day.",
        "psy3": "• Small steps — 100 is better than 0.",
        "psy4": "• Support — tell a friend about your goal.",
        "psy5": "• Forgiveness — if you slip, keep going.",
        "dictionary": "11. Dictionary",
        "feature": "💡 Tip of the day",
        "feature_btn": "Get a tip",
        "tips": [
            "Start with $1. The main thing is to start.",
            "Write your goal down. It increases your chances by 42%.",
            "Compare yourself to yesterday's you, not to others.",
            "Save 10% of any income. Immediately.",
            "Don't wait for Monday. Start today."
        ]
    }
}

t = texts[lang]

# --- ДАННЫЕ ПО ЯЗЫКАМ ---
if lang == "Русский":
    jobs_teen = [("Нет", 0), ("Промоутер", 3000), ("Курьер", 8000), ("Репетитор", 10000), ("Официант", 12000), ("Фриланс", 15000), ("Мойка машин", 7000), ("Выгул собак", 5000), ("Помощь с уроками", 6000), ("Продажа вещей", 4000), ("Стриминг", 3000), ("Своя подработка", 0)]
    jobs_adult = [("Нет", 0), ("Врач", 80000), ("Учитель", 50000), ("Инженер", 70000), ("Программист", 100000), ("Менеджер", 60000), ("Дизайнер", 65000), ("Маркетолог", 55000), ("Бухгалтер", 50000), ("Юрист", 90000), ("Своя работа", 0)]
    alternatives_teen = [("Найди подработку", "Дополнительный доход ускорит цель."), ("Трать меньше", "Меньше трат — больше накоплений."), ("Положи на вклад", "Банк платит процент. Деньги работают."), ("Продай ненужное", "Старые вещи — это деньги.")]
    alternatives_adult = [("Откладывай больше", "Увеличь сумму — срок сократится."), ("Трать меньше", "Меньше трат — больше накоплений."), ("Вклад", "Банк платит процент. Безопасно."), ("Инвестиции", "Акции, облигации. Долгосрочно."), ("Автоматизация", "Откладывай сразу при доходе.")]
    terms_teen = {"Инфляция": "Подорожание денег в будущем. Через год та же цель будет стоить дороже.", "Вклад": "Ты кладёшь деньги в банк. Банк платит процент. Деньги работают."}
    terms_adult = {"Инфляция": "Подорожание денег. Через год та же цель будет стоить дороже.", "Вклад": "Ты кладёшь деньги в банк. Банк платит процент.", "Акции": "Доля в компании. Растёт компания — растут деньги.", "Облигации": "Ты даёшь в долг. Тебе платят процент."}
else:
    jobs_teen = [("None", 0), ("Promoter", 3000), ("Courier", 8000), ("Tutor", 10000), ("Waiter", 12000), ("Freelance", 15000), ("Car wash", 7000), ("Dog walking", 5000), ("Homework help", 6000), ("Selling stuff", 4000), ("Streaming", 3000), ("Own part-time job", 0)]
    jobs_adult = [("None", 0), ("Doctor", 80000), ("Teacher", 50000), ("Engineer", 70000), ("Programmer", 100000), ("Manager", 60000), ("Designer", 65000), ("Marketer", 55000), ("Accountant", 50000), ("Lawyer", 90000), ("Own work", 0)]
    alternatives_teen = [("Find a part-time job", "Extra income will speed up your goal."), ("Spend less", "Less spending — more savings."), ("Put in a deposit", "Bank pays interest. Money works."), ("Sell unused stuff", "Old things — it's money.")]
    alternatives_adult = [("Save more", "Increase the amount — the term will shrink."), ("Spend less", "Less spending — more savings."), ("Deposit", "Bank pays interest. Safe."), ("Investments", "Stocks, bonds. Long-term."), ("Automation", "Save immediately when you get paid.")]
    terms_teen = {"Inflation": "Prices rise in the future. A year later the same goal will cost more.", "Deposit": "You put money in the bank. The bank pays interest. Money works."}
    terms_adult = {"Inflation": "Prices rise in the future. A year later the same goal will cost more.", "Deposit": "You put money in the bank. The bank pays interest.", "Stocks": "A share in a company. If the company grows, your money grows.", "Bonds": "You lend money. You get paid interest."}

# --- ЗАГОЛОВОК ---
st.title(t["title"])
st.write(t["subtitle"])

# --- НАВИГАЦИЯ В САЙДБАРЕ ---
st.sidebar.write(t["streak"]) # Показываем стрик в сайдбаре
page = st.sidebar.radio("Навигация / Navigation", [t["nav_game"], t["nav_knowledge"]])

# ==========================================
# СТРАНИЦА 1: ИГРА (КАЛЬКУЛЯТОР)
# ==========================================
if page == t["nav_game"]:
    user_type = st.radio(t["who"], [t["teen"], t["adult"]], horizontal=True)

    if user_type == t["teen"]:
        age = st.slider(t["age"], 13, 17, 15)
        jobs = jobs_teen
        alternatives = alternatives_teen
        terms = terms_teen
    else:
        age = st.slider(t["age"], 18, 60, 30)
        jobs = jobs_adult
        alternatives = alternatives_adult
        terms = terms_adult

    st.header(t["goal_header"])
    col1, col2 = st.columns(2)
    with col1:
        goal = st.text_input(t["goal_input"], "iPhone")
    with col2:
        currency = st.selectbox(t["currency"], [t["rub"], t["usd"]])

    is_usd = (currency == t["usd"])
    symbol = "$" if is_usd else "₽"
    rate = 90 if is_usd else 1

    target = st.number_input(f"{t['target']} ({symbol})", min_value=0, value=80000 if not is_usd else 1000, step=1000)

    st.header(t["data_header"])
    current = st.number_input(f"{t['current']} ({symbol})", min_value=0, value=5000 if not is_usd else 50, step=1000)

    st.write(t["monthly"])

    col1, col2, col3, col4 = st.columns(4)
    with col1: b0 = st.button("100")
    with col2: b1 = st.button("500")
    with col3: b2 = st.button("1000")
    with col4: b3 = st.button("2000")

    col5, col6, col7 = st.columns(3)
    with col5: b4 = st.button("3000")
    with col6: b5 = st.button("5000")
    with col7: b6 = st.button(t["custom"])

    if "monthly" not in st.session_state:
        st.session_state.monthly = 500
    if "custom_mode" not in st.session_state:
        st.session_state.custom_mode = False

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

    monthly = st.session_state.monthly

    st.header(t["jobs_header"])
    
    # --- ГЕНЕРАТОР ПОДРАБОТОК (ИЗЮМИНКА) ---
    if st.button(t["hustle_btn"]):
        idea, income = random.choice(t["hustles"])
        st.markdown(f'<div class="hustle-box">💡 {t["hustle_result"].format(idea=idea, income=income, symbol=symbol)}</div>', unsafe_allow_html=True)

    job_choice = st.selectbox(t["choose"], [j[0] for j in jobs])
    base_salary = next((j[1] for j in jobs if j[0] == job_choice), 0)
    if is_usd: base_salary = base_salary / rate

    extra = 0
    if job_choice in [t["own_job"]]:
        extra = st.number_input(f"{t['salary']} ({symbol})", min_value=0, value=0, step=1000)
    elif job_choice != t["no"]:
        extra = st.number_input(f"{t['salary']} ({symbol})", min_value=0, value=int(base_salary), step=1000)

    # --- РАСЧЁТ ---
    total_monthly = monthly + extra
    st.header(t["result"])
    
    if target <= current:
        st.success(t["goal_reached"])
    elif total_monthly > 0:
        months = (target - current) / total_monthly
        years = months / 12
        inflation = 0.06
        real_target = target * ((1 + inflation) ** years)

        st.markdown(f"""
        <div class="result-card">
            <h2 style="margin:0;">🎯 {goal}: {target:,.0f} {symbol}</h2>
            <h3 style="margin:10px 0 0 0;">⏱️ {months:.0f} {t['months']}</h3>
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.metric(t["target_label"], f"{target:,.0f} {symbol}")
        with col2:
            st.metric(t["inflation_label"], f"{real_target:,.0f} {symbol}")
        
        if months <= 6:
            st.success(t["status_green"])
        elif months <= 18:
            st.warning(t["status_yellow"])
        else:
            st.error(t["status_red"])

        data = []
        balance = current
        for m in range(int(months) + 1):
            data.append({t["chart_month"]: m, t["chart_balance"]: balance})
            balance += total_monthly
        df = pd.DataFrame(data)
        st.line_chart(df.set_index(t["chart_month"])[t["chart_balance"]])

        progress = min(current / target, 1.0)
        st.progress(progress)
        st.write(f"{t['you_at']} {progress*100:.1f}{t['to_goal']}")

        # --- ВЕХИ (MILESTONES) ---
        st.header(t["quest_levels"])
        
        def milestone_status(percentage):
            if progress >= percentage:
                return t["milestone_done"]
            else:
                return t["milestone_wait"]

        st.markdown(f'<div class="quest-level"><b>{t["milestone_10"]}</b> ({target*0.1:,.0f} {symbol}) — {milestone_status(0.1)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="quest-level"><b>{t["milestone_25"]}</b> ({target*0.25:,.0f} {symbol}) — {milestone_status(0.25)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="quest-level"><b>{t["milestone_50"]}</b> ({target*0.5:,.0f} {symbol}) — {milestone_status(0.5)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="quest-level"><b>{t["milestone_75"]}</b> ({target*0.75:,.0f} {symbol}) — {milestone_status(0.75)}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="quest-level"><b>{t["milestone_100"]}</b> ({target:,.0f} {symbol}) — {milestone_status(1.0)}</div>', unsafe_allow_html=True)

        # --- АЧИВКИ ---
        st.header(t["achievements"])
        earned = []
        if progress > 0.01: earned.append(t["ach1"])
        if monthly >= 1000: earned.append(t["ach2"])
        if progress > 0.25: earned.append(t["ach3"])
        if progress > 0.5: earned.append(t["ach4"])
        if progress > 0.75: earned.append(t["ach5"])
        if years > 1: earned.append(t["ach6"])
        if months < 6: earned.append(t["ach7"])
        if extra > 0: earned.append(t["ach8"])
        if user_type == t["teen"]: earned.append(t["ach10"])

        for ach in earned:
            st.markdown(f'<div class="achievement">{ach}</div>', unsafe_allow_html=True)
            
        st.info(f"{t['next_step']} {t['next_step_1']}")

        share_msg = t["share_text"].format(goal=goal, months=f"{months:.0f}")
        st.code(share_msg, language="text")
        
        st.success(t["wish"])
    else:
        st.warning(t["warning"])

# ==========================================
# СТРАНИЦА 2: БАЗА ЗНАНИЙ (СОВЕТЫ)
# ==========================================
elif page == t["nav_knowledge"]:
    st.header(t["speed_up"])
    st.info("Введи данные в разделе 'Твой квест', чтобы увидеть персональные расчеты." if lang == "Русский" else "Enter data in 'Your Quest' to see personalized calculations.")
    
    st.divider()

    st.header(t["why_save"])
    st.write(t["why1"]); st.write(t["why2"]); st.write(t["why3"]); st.write(t["why4"])

    st.header(t["spend_less"])
    st.write(t["spend1"]); st.write(t["spend2"]); st.write(t["spend3"]); st.write(t["spend4"]); st.write(t["spend5"])

    st.header(t["psychology"])
    st.write(t["psy1"]); st.write(t["psy2"]); st.write(t["psy3"]); st.write(t["psy4"]); st.write(t["psy5"])

    st.header(t["dictionary"])
    for term, definition in terms_adult.items():
        st.write(f"**{term}** — {definition}")

    st.divider()
    
    st.header(t["feature"])
    if st.button(t["feature_btn"]):
        st.success(random.choice(t["tips"]))
