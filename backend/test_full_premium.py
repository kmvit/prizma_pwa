"""
Полный тест премиум-генерации: все 9 разделов, 63 страницы + PDF отчёт.
Запуск: cd backend && ./venv/bin/python test_full_premium.py

Время выполнения: ~30-60 минут (72+ API вызовов)
Лог сохраняется в reports/test_full_premium_log.txt
"""
import asyncio
import json
import sys
import os
import time
from pathlib import Path
from types import SimpleNamespace
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
os.chdir(Path(__file__).parent)

from dotenv import load_dotenv
load_dotenv(override=True)

FAKE_ANSWERS = {
    1: "Когда я запустил свой первый проект, чувствовал невероятный подъём. Вокруг были единомышленники, мы работали в коворкинге допоздна, и энергия буквально била ключом. Музыка играла, кофе стоял на столе, и каждая идея казалась гениальной.",
    2: "Обычно я сначала собираю информацию, анализирую плюсы и минусы, но в итоге доверяю интуиции. Логика для меня — фундамент, но решающий толчок всегда даёт внутреннее чувство. Бывало, что логика говорила одно, а я делал наоборот — и не жалел.",
    3: "В незнакомой компании первые минуты наблюдаю. Стараюсь понять атмосферу, кто тут главный, кто расслаблен. Потом нахожу одного-двух человек, с которыми можно перекинуться парой фраз, и постепенно включаюсь. Никогда не лезу в центр внимания сразу.",
    4: "Глава называлась бы «Перезагрузка». Сейчас переосмысливаю свои ценности, меняю подход к работе и отношениям. Ощущение, что старая версия меня закончилась, а новая ещё не определилась. Это одновременно страшно и захватывающе.",
    5: "Восхищаюсь своим дедом. Он прошёл через невероятные трудности, но сохранил чувство юмора и доброту. Он никогда не жаловался и находил решение в любой ситуации. Меня поражает его стойкость и умение радоваться мелочам.",
    6: "Когда потерял близкого друга, испытал сильнейшую боль. Первые дни закрылся от всех, не мог нормально функционировать. Потом начал записывать свои мысли в дневник — это помогло. Со временем научился проживать горе, а не подавлять его.",
    7: "Обычно чувствую настроение людей по микросигналам — тон голоса, поза, взгляд. Недавно заметил, что коллега улыбается, но говорит тише обычного и избегает зрительного контакта. Спросил, всё ли в порядке — оказалось, у него серьёзные проблемы дома.",
    8: "Был конфликт с партнёром по бизнесу — мы разошлись во мнении о стратегии. Я предложил взять паузу на день, потом мы сели и каждый изложил свою позицию письменно. Нашли компромисс: его подход к маркетингу, мой к продукту.",
    9: "Успех для меня — это когда просыпаешься утром с предвкушением дня. Когда есть люди рядом, которые тебя понимают, и дело, которое зажигает. Деньги важны, но они средство, а не цель. Успешная жизнь — это свобода выбора и внутренний мир.",
    10: "Путешествовал бы и создавал образовательные проекты. Мечтаю построить школу нового формата, где дети учатся через проекты, а не зубрёжку. И ещё написал бы книгу о психологии принятия решений.",
    11: "Горжусь тем, что смог преодолеть свой страх публичных выступлений. Раньше даже перед малой группой потели ладони. Записался на курс ораторского мастерства, а через полгода выступил перед аудиторией в 200 человек.",
    12: "Больше всего расстраивает неискренность и пассивная агрессия. Когда человек говорит одно, а делает другое. Не выношу, когда вместо прямого разговора начинаются манипуляции и обиды. Это подрывает доверие.",
    13: "Стараюсь выражать несогласие спокойно: «Я вижу это иначе, вот почему...». Недавно на совещании коллега предложил план, который я считал рискованным. Сказал прямо: ценю идею, но вижу три конкретных риска. Предложил альтернативу.",
    14: "Самые близкие отношения — с женой. Нас объединяет абсолютная честность. Мы договорились никогда не ложиться спать в ссоре и всегда говорить, что чувствуем, даже если это неприятно. Это создаёт безопасность.",
    15: "Чаще всего оказываюсь в роли стратега-наблюдателя. Слушаю всех, анализирую ситуацию, а потом предлагаю структурированное решение. Иногда это перерастает в роль лидера, но мне комфортнее влиять через идеи, а не через власть.",
    16: "Первая мысль в стрессе: «Стоп, что реально происходит?». Потом включается самокритик: «Ты мог это предвидеть». Стараюсь отловить этот момент и переключиться на вопрос «Что я могу сделать прямо сейчас?». Не всегда получается.",
    17: "Ожидал от друга, что он поддержит мой проект хотя бы словом. Вместо этого он промолчал и позже высказал скепсис другим. Я высказал обиду напрямую. Он объяснил, что боялся мне навредить неосторожной поддержкой. Мы разобрались, но осадок остался.",
    18: "Сначала раскладываю проблему на составные части. Задаю вопросы: «Что известно? Что не известно? Какие есть варианты?». Потом рисую схему или список. Обсуждаю с кем-то — чужой взгляд помогает увидеть слепые зоны.",
    19: "Уволился с высокооплачиваемой работы без плана B. Внутренний голос просто сказал: «Хватит, это не твоё». Логика кричала остаться. Прошло два месяца неопределённости, но потом нашёл дело, которое по-настоящему зажигает.",
    20: "Мешает убеждение «я должен быть идеальным». Из-за этого откладываю проекты, пока не будут «готовы на 100%». Также мешает мысль «если попрошу помощи — покажусь слабым». Знаю, что это иррационально, но отпустить трудно.",
    21: "Не принимаю свою нетерпеливость. Хочу, чтобы всё было сделано быстро и качественно, и раздражаюсь, когда люди медлят. Понимаю, что это токсично, но борьба с этим — моя постоянная работа.",
    22: "Увлёкся стартапом, вложил всё время и деньги. Верил, что через полгода всё взлетит. Когда проект не пошёл, испытал сильное разочарование и потерю смысла. Долго восстанавливался, но извлёк урок о реалистичных ожиданиях.",
    23: "На критику реагирую сначала защитной реакцией — внутри вспыхивает «это несправедливо!». Потом беру паузу, перечитываю или обдумываю. Часто нахожу рациональное зерно. Недавно клиент раскритиковал мою работу — сначала обиделся, потом увидел, что он прав на 70%.",
    24: "Хотел предложить новую идею руководству, но представил, как её раскритикуют при всех. Промолчал. Через месяц коллега предложил почти то же самое и получил одобрение. Было досадно и стыдно за свою трусость.",
    25: "Тревогу ощущаю как сжатие в груди и холод в руках. Радость — как тепло в солнечном сплетении. Гнев — напряжение в челюсти и плечах. Грусть — тяжесть в груди и замедление всего тела.",
    26: "Хроническое напряжение в шее и плечах. Связываю это с постоянным давлением на работе. Когда был в отпуске две недели — всё прошло. Как только вернулся — вернулось и напряжение. Ещё бывает бессонница перед важными встречами.",
    27: "Перед важным событием чувствую бабочек в животе и учащённое сердцебиение. Ладони потеют. Иногда подташнивает. Но научился это воспринимать как признак мобилизации, а не страха. «Тело готовится» — так говорю себе.",
    28: "Процентов на 60-70. Часто делаю то, что «надо», а не то, что хочу. Например, выбрал стабильную карьеру вместо творчества. Но постепенно начинаю больше прислушиваться к себе. Последний год стал переломным.",
    29: "Жизнь кажется осмысленной, когда помогаю кому-то разобраться в сложной ситуации. Или когда вижу, как мой совет реально изменил чью-то жизнь. Также — моменты глубокого разговора с близким человеком и природа в тишине.",
    30: "Обязательно сказал бы близким, как сильно их люблю и ценю. Закончил бы книгу, которую начал писать три года назад. И съездил бы с семьёй в Японию — давно мечтаем, но всё откладываем.",
    31: "В семье я герой и одновременно миротворец. Всегда пытался быть лучшим, чтобы родители гордились. И при этом разруливал конфликты между мамой и сестрой. Это утомляет, но отказаться от этих ролей пока не могу.",
    32: "Папа был авторитарным — его слово было законом. Замечаю, что сам иногда давлю на близких, когда уверен в своей правоте. Мама была тревожной — и я унаследовал склонность к избыточному контролю.",
    33: "В семье было правило: «Не выносить сор из избы». Раньше следовал ему — никому не рассказывал о проблемах. Сейчас сознательно нарушаю: обратился к психологу и не стесняюсь говорить друзьям, если мне плохо.",
    34: "«Мужчины не плачут» — слышал это постоянно. До сих пор мне сложно показывать уязвимость. Ещё фраза бабушки: «Терпи — стерпится, слюбится». Из-за этого слишком долго терпел то, что нужно было менять.",
    35: "Моя тревога — это тёмно-серый туман, плотный и липкий, который обволакивает голову. Он не имеет чёткой формы, но давит сверху. Размером с комнату — заполняет всё пространство и не даёт увидеть выход.",
    36: "Моя основная проблема — как лабиринт со стеклянными стенами. Я вижу цель, вижу выход, но постоянно натыкаюсь на невидимые барьеры. Иду, уверенный в направлении, и вдруг — стена.",
    37: "Был бы волком. Сильный, независимый, но при этом преданный своей стае. Волк может быть одиночкой, но предпочитает быть в группе, где у каждого своя роль. И у волка есть интуиция — он чувствует опасность и возможности.",
    38: "Я — горная река. Сильная, целеустремлённая, иногда бурная. Пробивает себе путь через скалы, но при этом питает всё вокруг. Иногда замедляется и становится спокойной заводью, чтобы набраться сил перед следующим порогом."
}


class TestLogger:
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.lines = []
        self.section_stats = []
        self.total_cost = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.start_time = time.time()

    def log(self, msg: str):
        ts = datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        print(line)
        self.lines.append(line)

    def track_usage(self, usage: dict):
        self.total_input_tokens += usage.get("prompt_tokens", 0)
        self.total_output_tokens += usage.get("completion_tokens", 0)
        cost = usage.get("cost", {})
        self.total_cost += cost.get("total_cost", 0)

    def save(self):
        elapsed = time.time() - self.start_time
        self.lines.append("")
        self.lines.append("=" * 70)
        self.lines.append("  ИТОГОВАЯ СТАТИСТИКА")
        self.lines.append("=" * 70)
        self.lines.append(f"  Время выполнения: {elapsed:.0f} сек ({elapsed/60:.1f} мин)")
        self.lines.append(f"  Всего input токенов: {self.total_input_tokens:,}")
        self.lines.append(f"  Всего output токенов: {self.total_output_tokens:,}")
        self.lines.append(f"  Общая стоимость API: ${self.total_cost:.4f}")
        self.lines.append("")
        for s in self.section_stats:
            self.lines.append(f"  {s}")
        self.lines.append("=" * 70)
        self.log_path.write_text("\n".join(self.lines), encoding="utf-8")
        print(f"\nЛог сохранён: {self.log_path}")


def make_mock_data():
    with open("data/questions_premium.json", "r", encoding="utf-8") as f:
        raw = json.load(f)

    user = SimpleNamespace(
        id=999, telegram_id=None,
        name="Тестовый Пользователь", email="test@test.com",
        age=32, gender="male"
    )

    questions, answers = [], []
    for i, q in enumerate(raw["questions"], start=1):
        qobj = SimpleNamespace(id=i, text=q["text"], order_number=q["order_number"], test_version="premium")
        questions.append(qobj)
        if i in FAKE_ANSWERS:
            answers.append(SimpleNamespace(id=i, question_id=i, text_answer=FAKE_ANSWERS[i]))

    return user, questions, answers


async def run_full_test():
    from app.services.perplexity import PerplexityAIService
    from app.services.pdf_service import ReportGenerator
    from app.prompts.premium_new import PremiumPromptsNew

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    log = TestLogger(reports_dir / "test_full_premium_log.txt")

    service = PerplexityAIService()
    user, questions, answers = make_mock_data()

    log.log("=" * 70)
    log.log("  ПОЛНЫЙ ТЕСТ ПРЕМИУМ-ГЕНЕРАЦИИ (63 страницы + PDF)")
    log.log("=" * 70)
    log.log(f"  Вопросов: {len(questions)}, Ответов: {len(answers)}")
    log.log(f"  Модель: {service.model}")
    log.log(f"  Пользователь: {user.name} (id={user.id})")
    log.log("=" * 70)

    user_data = service._prepare_user_data(user, questions, answers)
    log.log(f"user_data: {len(user_data)} символов")

    # --- Фаза 1: AI генерация ---
    log.log("")
    log.log(">>> ФАЗА 1: AI ГЕНЕРАЦИЯ <<<")

    base_messages = [
        {"role": "system", "content": PremiumPromptsNew.get_base_prompt()},
        {"role": "user", "content": f"""Вот данные для ПЛАТНОГО психологического анализа (50 вопросов):

{user_data}

Пожалуйста, изучите эти ответы и подтвердите готовность к созданию подробного ПЛАТНОГО психологического анализа.

🚨 КРИТИЧЕСКИ ВАЖНО - ЦИТАТЫ:
- ВСЕ цитаты и примеры должны быть ТОЛЬКО реальными дословными фрагментами из предоставленных ответов выше
- ЗАПРЕЩЕНО выдумывать примеры или цитаты
- Если в ответах нет подходящей цитаты - НЕ создавайте пример
- Обращайтесь к человеку через "ВЫ", "ВАШИ", "ВАМ" - НЕ используйте слова "пользователь" или "клиент"."""}
    ]

    log.log("Отправляю первичный запрос...")
    t0 = time.time()
    initial = await service._make_api_request(base_messages, is_premium=True)
    base_messages.append({"role": "assistant", "content": initial["content"]})
    log.track_usage(initial.get("usage", {}))
    log.log(f"Первичный анализ: {len(initial['content'])} симв, {time.time()-t0:.1f}с, usage={initial.get('usage', {})}")

    page_structure = [
        ("premium_analysis", "Психологический портрет", 10),
        ("premium_strengths", "Сильные стороны и таланты", 5),
        ("premium_growth_zones", "Зоны роста", 7),
        ("premium_compensation", "Компенсаторика", 7),
        ("premium_interaction", "Взаимодействие с окружающими", 8),
        ("premium_prognosis", "Прогностика", 6),
        ("premium_practical", "Практическое приложение", 8),
        ("premium_conclusion", "Заключение", 6),
        ("premium_appendix", "Приложения", 6)
    ]

    all_pages = {}
    all_individual_pages = {}
    page_counter = 1
    quality_issues = []

    for section_key, section_name, page_count in page_structure:
        log.log("")
        log.log(f"{'─'*50}")
        log.log(f"РАЗДЕЛ: {section_name} ({page_count} страниц)")
        log.log(f"{'─'*50}")

        section_start = time.time()
        conversation = list(base_messages)

        section_prompt = service._get_section_prompt(section_key)
        conversation.append({"role": "user", "content": f'Переходим к разделу "{section_name}". Инструкции:\n{section_prompt}\nИспользуйте эти инструкции для всех страниц данного раздела.'})

        t0 = time.time()
        section_resp = await service._make_api_request(conversation, is_premium=True)
        conversation.append({"role": "assistant", "content": section_resp["content"]})
        log.track_usage(section_resp.get("usage", {}))

        ctx_tokens = service._estimate_tokens(conversation)
        log.log(f"  Ack раздела: {len(section_resp['content'])} симв, {time.time()-t0:.1f}с, ctx≈{ctx_tokens}tok")

        section_chars = 0
        for page_num in range(1, page_count + 1):
            page_prompt, _ = service._get_premium_page_prompt(section_key, page_num, page_count)
            conversation.append({"role": "user", "content": page_prompt})

            ctx_tokens = service._estimate_tokens(conversation)
            t0 = time.time()
            page_resp = await service._make_api_request(conversation, is_premium=True)
            elapsed_page = time.time() - t0
            log.track_usage(page_resp.get("usage", {}))

            content = page_resp["content"]
            conversation.append({"role": "assistant", "content": content})

            all_individual_pages[f"page_{page_counter:02d}"] = {
                "content": content,
                "section": section_name,
                "section_key": section_key,
                "page_num": page_num,
                "global_page": page_counter
            }
            section_chars += len(content)

            has_quotes = '«' in content or '"' in content
            has_you = any(w in content.lower() for w in ["ваш", "вам", "вы "])
            usage = page_resp.get("usage", {})
            prompt_tok = usage.get("prompt_tokens", 0)

            status = "OK"
            if not has_quotes:
                status = "⚠️ НЕТ ЦИТАТ"
                quality_issues.append(f"Стр.{page_counter} ({section_name} p{page_num}): нет цитат")
            if not has_you:
                status += " ⚠️ НЕТ ВЫ"
                quality_issues.append(f"Стр.{page_counter} ({section_name} p{page_num}): нет обращения на ВЫ")

            log.log(f"  Стр.{page_counter:02d} (p{page_num}/{page_count}): {len(content)} симв, {elapsed_page:.1f}с, in={prompt_tok}tok, ctx≈{ctx_tokens}tok [{status}]")

            page_counter += 1
            await asyncio.sleep(1)

        section_elapsed = time.time() - section_start
        final_ctx = service._estimate_tokens(conversation)
        stat = f"{section_name}: {section_chars} симв, {page_count} стр, {section_elapsed:.0f}с, макс.ctx≈{final_ctx}tok"
        log.section_stats.append(stat)
        log.log(f"  ИТОГО раздел: {section_chars} симв, {section_elapsed:.0f}с, финальный ctx≈{final_ctx}tok")

        section_pages = {k: v["content"] for k, v in all_individual_pages.items() if v["section_key"] == section_key}
        all_pages[section_key] = "\n\n".join(section_pages.values())

    total_chars = sum(len(c) for c in all_pages.values())
    total_pages = page_counter - 1
    log.log("")
    log.log(f"AI ГЕНЕРАЦИЯ ЗАВЕРШЕНА: {total_chars} символов, {total_pages} страниц")

    if quality_issues:
        log.log(f"\n⚠️ ПРОБЛЕМЫ КАЧЕСТВА ({len(quality_issues)}):")
        for issue in quality_issues:
            log.log(f"  - {issue}")
    else:
        log.log("\n✅ Все страницы содержат цитаты и обращение на ВЫ")

    # --- Фаза 2: PDF генерация ---
    log.log("")
    log.log(">>> ФАЗА 2: PDF ГЕНЕРАЦИЯ <<<")

    analysis_result = {
        "success": True,
        "premium_analysis": all_pages.get("premium_analysis", ""),
        "premium_strengths": all_pages.get("premium_strengths", ""),
        "premium_growth_zones": all_pages.get("premium_growth_zones", ""),
        "premium_compensation": all_pages.get("premium_compensation", ""),
        "premium_interaction": all_pages.get("premium_interaction", ""),
        "premium_prognosis": all_pages.get("premium_prognosis", ""),
        "premium_practical": all_pages.get("premium_practical", ""),
        "premium_conclusion": all_pages.get("premium_conclusion", ""),
        "premium_appendix": all_pages.get("premium_appendix", ""),
        "individual_pages": all_individual_pages,
        "initial_analysis": initial["content"],
        "usage": {"pages_generated": total_pages},
        "timestamp": datetime.utcnow().isoformat()
    }

    try:
        report_gen = ReportGenerator()
        t0 = time.time()
        report_path = report_gen.create_premium_pdf_report(user, analysis_result)
        log.log(f"PDF отчёт создан: {report_path} ({time.time()-t0:.1f}с)")

        if Path(report_path).exists():
            size_mb = Path(report_path).stat().st_size / (1024 * 1024)
            log.log(f"Размер файла: {size_mb:.2f} MB")
        else:
            log.log("⚠️ Файл PDF не найден!")
    except Exception as e:
        log.log(f"❌ Ошибка генерации PDF: {e}")
        txt_path = reports_dir / f"test_premium_raw_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
        parts = []
        for key in ["premium_analysis", "premium_strengths", "premium_growth_zones", "premium_compensation",
                     "premium_interaction", "premium_prognosis", "premium_practical", "premium_conclusion", "premium_appendix"]:
            if all_pages.get(key):
                parts.append(f"\n{'='*60}\n{key}\n{'='*60}\n{all_pages[key]}")
        txt_path.write_text("\n".join(parts), encoding="utf-8")
        log.log(f"Сырой текст сохранён: {txt_path}")

    log.save()


if __name__ == "__main__":
    asyncio.run(run_full_test())
