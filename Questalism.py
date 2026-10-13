import streamlit as st
import pandas as pd

st.set_page_config(page_title="Questalism", page_icon="💰", layout="wide")

# --- ФОН ---
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1506905925346-21bda4d32df4?q=80&w=2070&auto=format&fit=crop&sat=-100");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }
    .stApp::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0, 0, 0, 0.9);
        z-index: -1;
    }
    h1, h2, h3, p, label, .stMarkdown {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- ЯЗЫК ---
lang = st.radio("Язык / Language", ["Русский", "English"])

texts = {
    "Русский": {
        "title": "💰 Questalism",
        "subtitle": "Твоя мечта. Твой путь. Твои деньги.",
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
        "monthly": "Сколько можешь откладывать в месяц?",
        "custom": "Своё",
        "custom_input": "Введи сумму:",
        "jobs_header": "3. Подработки",
        "work_header": "3. Работа",
        "choose": "Выбери",
        "no": "Нет",
        "own_job": "Своя подработка",
        "own_work": "Своя работа",
        "salary": "Сколько ты зарабатываешь?",
        "result": "4. Результат",
        "target_label": "Цель",
        "term_label": "Срок",
        "inflation_label": "С инфляцией",
        "inflation_info": "Инфляция — это подорожание денег в будущем.",
        "months": "мес.",
        "you_at": "Ты на",
        "to_goal": "% к цели",
        "achievements": "5. Ачивки",
        "reminder": "6. Напоминание",
        "reminder1": "📅 Откладывай 1-го числа каждого месяца.",
        "reminder2": "📅 Проверяй прогресс каждое воскресенье.",
        "reminder3": "📅 Пересматривай цель раз в месяц.",
        "speed_up": "7. Как ускорить цель",
        "if_more": "Если откладывать на",
        "more": "больше → срок:",
        "need_daily": "Нужно откладывать в день:",
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
        "dictionary": "11. Словарь",
        "wish": "Удачи! Ты справишься. 💪",
        "warning": "Введи сумму больше 0.",
        "ach1": "🎯 Первый шаг — ты начал копить.",
        "ach2": "💎 Сберегатель — откладываешь больше 1000 в месяц.",
        "ach3": "🥇 Четверть пути — ты прошёл 25% к цели.",
        "ach4": "🔥 Половина — ты на середине пути.",
"ach5": "⭐ Почти у цели — осталось 25%.",
        "ach6": "🏆 Марафонец — твоя цель на год и больше.",
        "ach7": "🚀 Спринтер — ты достигнешь цели за полгода.",
        "ach8": "💪 Работяга — у тебя есть дополнительный доход.",
        "ach9": "👑 Высокий доход — ты зарабатываешь больше 10K.",
        "ach10": "🎓 Школьник — ты учишься и копишь одновременно.",
    },
    "English": {
        "title": "💰 Questalism",
        "subtitle": "Your dream. Your path. Your money.",
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
        "monthly": "How much can you save per month?",
        "custom": "Custom",
        "custom_input": "Enter amount:",
        "jobs_header": "3. Part-time jobs",
        "work_header": "3. Work",
        "choose": "Choose",
        "no": "None",
        "own_job": "Own part-time job",
        "own_work": "Own work",
        "salary": "How much do you earn?",
        "result": "4. Result",
        "target_label": "Goal",
        "term_label": "Term",
        "inflation_label": "With inflation",
        "inflation_info": "Inflation is the rise in prices in the future.",
        "months": "mo.",
        "you_at": "You are at",
        "to_goal": "% to goal",
        "achievements": "5. Achievements",
        "reminder": "6. Reminder",
        "reminder1": "📅 Save on the 1st of each month.",
        "reminder2": "📅 Check progress every Sunday.",
        "reminder3": "📅 Review your goal once a month.",
        "speed_up": "7. How to speed up",
        "if_more": "If you save",
        "more": "more → term:",
        "need_daily": "Need to save daily:",
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
        "wish": "Good luck! You can do it. 💪",
        "warning": "Enter an amount greater than 0.",
        "ach1": "🎯 First step — you started saving.",
        "ach2": "💎 Saver — you save more than 1000 per month.",
        "ach3": "🥇 Quarter way — you passed 25% of your goal.",
        "ach4": "🔥 Halfway — you are in the middle.",
        "ach5": "⭐ Almost there — 25% left.",
        "ach6": "🏆 Marathoner — your goal is for a year or more.",
        "ach7": "🚀 Sprinter — you'll reach your goal in half a year.",
        "ach8": "💪 Hard worker — you have extra income.",
        "ach9": "👑 High income — you earn more than 10K.",
        "ach10": "🎓 Student — you study and save at the same time.",
    }
}

t = texts[lang]
# --- ДАННЫЕ ПО ЯЗЫКАМ ---
if lang == "Русский":
    jobs_teen = [
        ("Нет", 0), ("Промоутер", 3000), ("Курьер", 8000),
        ("Репетитор", 10000), ("Официант", 12000), ("Фриланс", 15000),
        ("Мойка машин", 7000), ("Выгул собак", 5000),
        ("Помощь с уроками", 6000), ("Продажа вещей", 4000),
        ("Стриминг", 3000), ("Своя подработка", 0),
    ]
    jobs_adult = [
        ("Нет", 0), ("Врач", 80000), ("Учитель", 50000),
        ("Инженер", 70000), ("Программист", 100000), ("Менеджер", 60000),
        ("Дизайнер", 65000), ("Маркетолог", 55000), ("Бухгалтер", 50000),
        ("Юрист", 90000), ("Своя работа", 0),
    ]
    alternatives_teen = [
        ("Найди подработку", "Дополнительный доход ускорит цель."),
        ("Трать меньше", "Меньше трат — больше накоплений."),
        ("Положи на вклад", "Банк платит процент. Деньги работают."),
        ("Продай ненужное", "Старые вещи — это деньги."),
    ]
    alternatives_adult = [
        ("Откладывай больше", "Увеличь сумму — срок сократится."),
        ("Трать меньше", "Меньше трат — больше накоплений."),
        ("Вклад", "Банк платит процент. Безопасно."),
        ("Инвестиции", "Акции, облигации. Долгосрочно."),
        ("Автоматизация", "Откладывай сразу при доходе."),
    ]
    terms_teen = {
        "Инфляция": "Подорожание денег в будущем. Через год та же цель будет стоить дороже.",
        "Вклад": "Ты кладёшь деньги в банк. Банк платит процент. Деньги работают.",
    }
    terms_adult = {
        "Инфляция": "Подорожание денег. Через год та же цель будет стоить дороже.",
        "Вклад": "Ты кладёшь деньги в банк. Банк платит процент.",
        "Акции": "Доля в компании. Растёт компания — растут деньги.",
        "Облигации": "Ты даёшь в долг. Тебе платят процент.",
    }
else:
    jobs_teen = [
        ("None", 0), ("Promoter", 3000), ("Courier", 8000),
        ("Tutor", 10000), ("Waiter", 12000), ("Freelance", 15000),
        ("Car wash", 7000), ("Dog walking", 5000),
        ("Homework help", 6000), ("Selling stuff", 4000),
        ("Streaming", 3000), ("Own part-time job", 0),
    ]
    jobs_adult = [
        ("None", 0), ("Doctor", 80000), ("Teacher", 50000),
        ("Engineer", 70000), ("Programmer", 100000), ("Manager", 60000),
        ("Designer", 65000), ("Marketer", 55000), ("Accountant", 50000),
        ("Lawyer", 90000), ("Own work", 0),
    ]
    alternatives_teen = [
        ("Find a part-time job", "Extra income will speed up your goal."),
        ("Spend less", "Less spending — more savings."),
        ("Put in a deposit", "Bank pays interest. Money works."),
        ("Sell unused stuff", "Old things — it's money."),
    ]
    alternatives_adult = [
        ("Save more", "Increase the amount — the term will shrink."),
        ("Spend less", "Less spending — more savings."),
        ("Deposit", "Bank pays interest. Safe."),
        ("Investments", "Stocks, bonds. Long-term."),
        ("Automation", "Save immediately when you get paid."),
    ]
    terms_teen = {
        "Inflation": "Prices rise in the future. A year later the same goal will cost more.",
        "Deposit": "You put money in the bank. The bank pays interest. Money works.",
    }
    terms_adult = {
        "Inflation": "Prices rise in the future. A year later the same goal will cost more.",
        "Deposit": "You put money in the bank. The bank pays interest.",
        "Stocks": "A share in a company. If the company grows, your money grows.",
        "Bonds": "You lend money. You get paid interest.",
    }

st.title(t["title"])
st.write(t["subtitle"])

# --- 1. КТО ТЫ ---
user_type = st.radio(t["who"], [t["teen"], t["adult"]])

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
# --- 2. ЦЕЛЬ ---
st.header(t["goal_header"])
col1, col2 = st.columns(2)
with col1:
    goal = st.text_input(t["goal_input"], "iPhone")
with col2:
    currency = st.selectbox(t["currency"], [t["rub"], t["usd"]])

symbol = "₽" if currency == t["rub"] else "$"
target = st.number_input(f"{t['target']} ({symbol})", min_value=0, value=80000, step=1000)

# --- 3. ДАННЫЕ ---
st.header(t["data_header"])
current = st.number_input(f"{t['current']} ({symbol})", min_value=0, value=5000, step=1000)

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

if b0:
    st.session_state.monthly = 100
    st.session_state.custom_mode = False
if b1:
    st.session_state.monthly = 500
    st.session_state.custom_mode = False
if b2:
    st.session_state.monthly = 1000
    st.session_state.custom_mode = False
if b3:
    st.session_state.monthly = 2000
    st.session_state.custom_mode = False
if b4:
    st.session_state.monthly = 3000
    st.session_state.custom_mode = False
if b5:
    st.session_state.monthly = 5000
    st.session_state.custom_mode = False
if b6:
    st.session_state.custom_mode = True

if st.session_state.custom_mode:
    custom = st.number_input(
        t["custom_input"],
        min_value=1,
        value=st.session_state.monthly,
        step=100,
        key="custom_input"
    )
    st.session_state.monthly = custom

monthly = st.session_state.monthly

# --- 4. РАБОТА ---
if user_type == t["teen"]:
    st.header(t["jobs_header"])
else:
    st.header(t["work_header"])

job_choice = st.selectbox(t["choose"], [j[0] for j in jobs])
extra = 0
if job_choice == t["own_job"] or job_choice == t["own_work"]:
    extra = st.number_input(f"{t['salary']} ({symbol})", min_value=0, value=0, step=1000, key="job_input")
elif job_choice != t["no"]:
    extra = st.number_input(f"{t['salary']} ({symbol})", min_value=0, value=0, step=1000, key="job_input")

# --- 5. РАСЧЁТ ---
total_monthly = monthly + extra
if total_monthly > 0:
    months = (target - current) / total_monthly
    years = months / 12
    inflation = 0.06
    real_target = target * ((1 + inflation) ** years)

    st.header(t["result"])
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(t["target_label"], f"{target:,} {symbol}")
    with col2:
        st.metric(t["term_label"], f"{months:.0f} {t['months']}")
    with col3:
        st.metric(t["inflation_label"], f"{real_target:,.0f} {symbol}")
    st.info(t["inflation_info"])

    data = []
    balance = current
    for m in range(int(months) + 1):
        data.append({"Месяц": m, "Баланс": balance})
        balance += total_monthly
    df = pd.DataFrame(data)
    st.line_chart(df.set_index("Месяц")["Баланс"])

    progress = min(current / target, 1.0)
    st.progress(progress)
    st.write(f"{t['you_at']} {progress*100:.1f}{t['to_goal']}")

    # --- 5. АЧИВКИ ---
    st.header(t["achievements"])
    if progress > 0.01:
        st.write(t["ach1"])
    if monthly >= 1000:
        st.write(t["ach2"])
    if progress > 0.25:
        st.write(t["ach3"])
    if progress > 0.5:
        st.write(t["ach4"])
    if progress > 0.75:
        st.write(t["ach5"])
    if years > 1:
        st.write(t["ach6"])
    if months < 6:
        st.write(t["ach7"])
    if extra > 0:
        st.write(t["ach8"])
    if extra > 10000:
        st.write(t["ach9"])
    if user_type == t["teen"]:
        st.write(t["ach10"])

    # --- 6. НАПОМИНАНИЕ ---
    st.header(t["reminder"])
    st.write(t["reminder1"])
    st.write(t["reminder2"])
    st.write(t["reminder3"])
# --- 7. КАК УСКОРИТЬ ---
    st.header(t["speed_up"])
    st.write(f"• {t['if_more']} 500 {symbol} {t['more']} {(target - current) / (total_monthly + 500):.0f} {t['months']}")
    st.write(f"• {t['if_more']} 1000 {symbol} {t['more']} {(target - current) / (total_monthly + 1000):.0f} {t['months']}")
    daily = (target - current) / (months * 30)
    st.write(f"• {t['need_daily']} {daily:.0f} {symbol}")
    for alt_name, alt_desc in alternatives:
        st.write(f"{alt_name} — {alt_desc}")

    # --- 8. ПОЧЕМУ ВАЖНО ---
    st.header(t["why_save"])
    st.write(t["why1"])
    st.write(t["why2"])
    st.write(t["why3"])
    st.write(t["why4"])

    # --- 9. КАК МЕНЬШЕ ТРАТИТЬ ---
    st.header(t["spend_less"])
    st.write(t["spend1"])
    st.write(t["spend2"])
    st.write(t["spend3"])
    st.write(t["spend4"])
    st.write(t["spend5"])

    # --- 10. ПСИХОЛОГИЯ ---
    st.header(t["psychology"])
    st.write(t["psy1"])
    st.write(t["psy2"])
    st.write(t["psy3"])
    st.write(t["psy4"])
    st.write(t["psy5"])

    # --- 11. СЛОВАРЬ ---
    st.header(t["dictionary"])
    for term, definition in terms.items():
        st.write(f"{term} — {definition}")

    # --- 12. ПОЖЕЛАНИЕ ---
    st.success(t["wish"])

else:
    st.warning(t["warning"])
