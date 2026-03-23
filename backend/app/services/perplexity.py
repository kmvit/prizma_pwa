"""
Сервис Perplexity AI для психологического анализа. Адаптирован из perplexy_bot для PWA (user.id).
"""
import asyncio
import re
import httpx
from typing import List, Dict
from datetime import datetime

from app.config import PERPLEXITY_API_KEY, PERPLEXITY_MODEL, PERPLEXITY_ENABLED
from app.database.models import User, Answer, Question
from app.prompts.base import BasePrompts
from app.prompts.psychology import PsychologyPrompts
from app.prompts.premium_new import PremiumPromptsNew
from app.services.pdf_service import ReportGenerator

from loguru import logger


def _user_id(user: User) -> int:
    return getattr(user, 'id', None) or getattr(user, 'telegram_id', 0)


class PerplexityAIService:
    """Сервис для работы с Perplexity AI"""

    def __init__(self):
        self.api_key = PERPLEXITY_API_KEY
        self.model = PERPLEXITY_MODEL or "sonar-pro"
        self.api_url = "https://api.perplexity.ai/chat/completions"
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY не найден")

    def _prepare_user_data(self, user: User, questions: List[Question], answers: List[Answer]) -> str:
        qa_pairs = []
        answer_dict = {ans.question_id: ans for ans in answers}
        for question in questions:
            answer = answer_dict.get(question.id)
            if answer and answer.text_answer:
                qa_pairs.append(f"Вопрос {question.order_number}: {question.text}\nОтвет: {answer.text_answer}")
        return "\n\n".join(qa_pairs)

    def _get_page_specific_prompt(self, page_type: str) -> str:
        prompts_map = PsychologyPrompts.get_context_prompts_map()
        if page_type not in prompts_map:
            raise ValueError(f"Неизвестный тип страницы: {page_type}")
        return prompts_map[page_type]()

    async def _make_api_request(self, messages: List[Dict], retry_count: int = 3, is_premium: bool = False) -> Dict:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "PRIZMA-AI-Psychologist/1.0"
        }
        max_tokens = 12000 if is_premium else 4000
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.6,
            "stream": False
        }
        for attempt in range(retry_count):
            try:
                async with httpx.AsyncClient(timeout=120.0) as client:
                    response = await client.post(self.api_url, headers=headers, json=payload)
                if response.status_code != 200:
                    if response.status_code == 429:
                        wait_time = (2 ** attempt) * 10
                        logger.warning(f"Rate limit, ждем {wait_time}с")
                        await asyncio.sleep(wait_time)
                        continue
                    raise Exception(f"API Error {response.status_code}: {response.text}")
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    usage = result.get("usage", {})
                    return {"content": content, "usage": usage}
                raise Exception("Неожиданный формат ответа от API")
            except (httpx.RemoteProtocolError, httpx.ReadTimeout, httpx.ConnectError) as e:
                wait_time = (2 ** attempt) * 5
                logger.warning(f"Попытка {attempt + 1}/{retry_count} неудачна: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(wait_time)
                else:
                    raise
        raise Exception("Все попытки исчерпаны")

    async def analyze_user_responses(self, user: User, questions: List[Question], answers: List[Answer]) -> Dict:
        """Анализ ответов пользователя через Perplexity AI"""
        user_data = self._prepare_user_data(user, questions, answers)
        uid = _user_id(user)
        logger.info(f"Запускаем AI анализ для пользователя {uid}")

        conversation = [
            {"role": "system", "content": BasePrompts.get_common_context()},
            {"role": "user", "content": f"""Вот данные для психологического анализа:

{user_data}

Изучите эти ответы и подтвердите готовность к созданию анализа.

КРИТИЧЕСКИ ВАЖНО:
- ВСЕ цитаты — только реальные дословные фрагменты из ответов выше
- ЗАПРЕЩЕНО выдумывать примеры
- Обращайтесь к человеку через "ВЫ", "ВАШИ", "ВАМ"."""
             }
        ]

        initial_response = await self._make_api_request(conversation)
        conversation.append({"role": "assistant", "content": initial_response["content"]})

        results = {}
        page_names = {"page3": "Тип личности", "page4": "Мышление и решения", "page5": "Ограничивающие паттерны"}

        for i, page_type in enumerate(["page3", "page4", "page5"]):
            page_prompt = self._get_page_specific_prompt(page_type)
            conversation.append({"role": "user", "content": page_prompt})
            page_response = await self._make_api_request(conversation)
            results[page_type] = page_response
            conversation.append({"role": "assistant", "content": page_response["content"]})
            if i < 2:
                await asyncio.sleep(3)

        return {
            "success": True,
            "page3_analysis": results["page3"]["content"],
            "page4_analysis": results["page4"]["content"],
            "page5_analysis": results["page5"]["content"],
            "usage": {},
            "timestamp": datetime.utcnow().isoformat()
        }

    def _get_section_prompt(self, section_key: str) -> str:
        methods = {
            "premium_analysis": PremiumPromptsNew.get_premium_analysis_prompt,
            "premium_strengths": PremiumPromptsNew.get_premium_strengths_prompt,
            "premium_growth_zones": PremiumPromptsNew.get_premium_growth_zones_prompt,
            "premium_compensation": PremiumPromptsNew.get_premium_compensation_prompt,
            "premium_interaction": PremiumPromptsNew.get_premium_interaction_prompt,
            "premium_prognosis": PremiumPromptsNew.get_premium_prognosis_prompt,
            "premium_practical": PremiumPromptsNew.get_premium_practical_prompt,
            "premium_conclusion": PremiumPromptsNew.get_premium_conclusion_prompt,
            "premium_appendix": PremiumPromptsNew.get_premium_appendix_prompt,
        }
        if section_key not in methods:
            raise ValueError(f"Неизвестный раздел: {section_key}")
        return methods[section_key]()

    def _extract_page_count_from_description(self, description: str) -> float:
        """Извлекает количество страниц из описания подблока"""
        patterns = [
            r'\((\d+(?:[,\.]\d+)?)\s*страниц?\w*\)',
            r'\((\d+)-(\d+)\s*страниц?\w*\)',
        ]
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                if len(match.groups()) == 1:
                    return float(match.group(1).replace(',', '.'))
                return (float(match.group(1)) + float(match.group(2))) / 2
        return 1.0

    def _get_premium_page_prompt(self, section_key: str, page_num: int, total_pages: int):
        """Промпт для конкретной страницы премиум-анализа. Возвращает (промпт, expected_pages)."""
        section_subblocks = {
            "premium_analysis": {"name": "Психологический портрет", "subblocks": [
                "АНАЛИЗ BIG FIVE (1 страница)", "ОПРЕДЕЛЕНИЕ ТИПА MBTI (1 страница)", "АРХЕТИПИЧЕСКАЯ СТРУКТУРА (1 страница)",
                "КОГНИТИВНЫЙ ПРОФИЛЬ (1 страница)", "ЭМОЦИОНАЛЬНЫЙ ИНТЕЛЛЕКТ (1-2 страницы)", "СИСТЕМА ЦЕННОСТЕЙ (1 страница)",
                "КОММУНИКАТИВНЫЙ СТИЛЬ (1 страница)", "МОТИВАЦИОННЫЕ ДРАЙВЕРЫ (1 страница)",
                "ТЕНЕВЫЕ АСПЕКТЫ ЛИЧНОСТИ (1-2 страницы)", "ЭКЗИСТЕНЦИАЛЬНАЯ ИСПОЛНЕННОСТЬ (1-2 страницы)"
            ]},
            "premium_strengths": {"name": "Сильные стороны и таланты", "subblocks": [
                "ПРИРОДНЫЕ ТАЛАНТЫ (1,5 страницы)", "ПРЕДРАСПОЛОЖЕННОСТИ К ОПРЕДЕЛЁННЫМ ОБЛАСТЯМ (0,5 страницы)",
                "ПРИОБРЕТЁННЫЕ КОМПЕТЕНЦИИ (2 страницы)", "РЕСУРСНЫЕ СОСТОЯНИЯ (2 страницы)",
                "ПОТЕНЦИАЛ РАЗВИТИЯ (1 страница)", "УНИКАЛЬНЫЕ КОМБИНАЦИИ КАЧЕСТВ (1 страница)"
            ]},
            "premium_growth_zones": {"name": "Зоны роста", "subblocks": [
                "ОГРАНИЧИВАЮЩИЕ УБЕЖДЕНИЯ (1 страница)", "ТРАНСФОРМАЦИЯ УБЕЖДЕНИЙ (0.5 страницы)",
                "КОГНИТИВНЫЕ ИСКАЖЕНИЯ (1 страница)", "СЛЕПЫЕ ЗОНЫ (1 страница)",
                "ЭМОЦИОНАЛЬНЫЕ ТРИГГЕРЫ (2 страницы)", "ПАТТЕРНЫ САМОСАБОТАЖА (1 страница)",
                "СОМАТИЧЕСКИЕ ПРОЯВЛЕНИЯ (1 страница)"
            ]},
            "premium_compensation": {"name": "Компенсаторика", "subblocks": [
                "СТРАТЕГИИ РАЗВИТИЯ (2 страницы)", "ТЕХНИКИ САМОРЕГУЛЯЦИИ (1 страница)",
                "АЛЬТЕРНАТИВНЫЕ МОДЕЛИ ПОВЕДЕНИЯ (1 страница)", "РЕСУРСЫ ВОССТАНОВЛЕНИЯ (1 страница)",
                "ИНДИВИДУАЛЬНЫЙ ПЛАН РАЗВИТИЯ (3 страницы)", "РЕКОМЕНДУЕМЫЕ ПРАКТИКИ (2 страницы)",
                "ОБРАЗНО-СИМВОЛИЧЕСКАЯ РАБОТА (1 страница)"
            ]},
            "premium_interaction": {"name": "Взаимодействие с окружающими", "subblocks": [
                "СОВМЕСТИМОСТЬ (1 страница)", "СТРАТЕГИИ ДЛЯ СЛОЖНЫХ СОЧЕТАНИЙ (1 страница)",
                "ПЕРСОНАЛЬНЫЙ СТИЛЬ ОБЩЕНИЯ (1 страница)", "ТЕХНИКИ АДАПТИВНОЙ КОММУНИКАЦИИ (1 страница)",
                "РОЛЬ В КОМАНДЕ (1 страница)", "БЛИЗКИЕ ОТНОШЕНИЯ (1 страница)",
                "РАЗРЕШЕНИЕ КОНФЛИКТОВ (1 страница)", "СЕМЕЙНЫЕ ПАТТЕРНЫ И ГРАНИЦЫ (1 страница)"
            ]},
            "premium_prognosis": {"name": "Прогностика", "subblocks": [
                "ДВУХСЦЕНАРНЫЙ ПРОГНОЗ РАЗВИТИЯ (1 страница)", "КРИЗИСЫ И ТОЧКИ РОСТА (1 страница)",
                "САМОРЕАЛИЗАЦИЯ (1 страница)", "ПРОГНОЗ РАЗВИТИЯ КАЧЕСТВ (1 страница)",
                "ДОЛГОСРОЧНЫЕ ПЕРСПЕКТИВЫ (1 страница)", "ИТОГОВЫЕ РЕКОМЕНДАЦИИ (1 страница)"
            ]},
            "premium_practical": {"name": "Практическое приложение", "subblocks": [
                "ПРОФРЕАЛИЗАЦИЯ (2 страницы)", "ПРОДУКТИВНОСТЬ (2 страницы)", "ПРИНЯТИЕ РЕШЕНИЙ (2 страницы)",
                "СОЦИАЛЬНЫЕ НАВЫКИ (2 страницы)", "ЗДОРОВЬЕ И БЛАГОПОЛУЧИЕ (2 страницы)",
                "ТЕХНИКИ ДЛЯ СИЛЬНЫХ СТОРОН (1 страница)", "УПРАЖНЕНИЯ ДЛЯ ЗОН РОСТА (1 страница)",
                "ЧЕК-ЛИСТЫ И ТРЕКЕРЫ (1 страница)"
            ]},
            "premium_conclusion": {"name": "Заключение", "subblocks": [
                "ОБОБЩЕНИЕ ИНСАЙТОВ (1 страница)", "СИНТЕЗ СИЛЬНЫХ СТОРОН (1 страница)",
                "МОТИВАЦИОННОЕ ПОСЛАНИЕ (1 страница)", "РЕКОМЕНДАЦИИ ПО ИСПОЛЬЗОВАНИЮ (1 страница)",
                "ЭВОЛЮЦИЯ ЛИЧНОСТИ (1 страница)", "ФИНАЛЬНОЕ ПОСЛАНИЕ (1 страница)"
            ]},
            "premium_appendix": {"name": "Приложения", "subblocks": [
                "ГЛОССАРИЙ ТЕРМИНОВ (1 страница)", "РЕКОМЕНДУЕМЫЕ РЕСУРСЫ (2 страницы)",
                "ВИЗУАЛИЗАЦИИ И ДИАГРАММЫ (1 страница)", "ПЕРСОНАЛЬНЫЕ АФФИРМАЦИИ (2 страницы)",
                "ШАБЛОНЫ ДЛЯ САМОАНАЛИЗА (1 страница)", "ПРОЕКТИВНЫЕ ОБРАЗЫ И МЕТАФОРЫ (1 страница)"
            ]},
        }
        if section_key not in section_subblocks or page_num > len(section_subblocks[section_key]["subblocks"]):
            raise ValueError(f"Страница {page_num} в разделе {section_key}")
        subblock_desc = section_subblocks[section_key]["subblocks"][page_num - 1]
        expected_pages = self._extract_page_count_from_description(subblock_desc)
        expected_chars = int(expected_pages * 3000)
        prompt = f"""Создайте СТРАНИЦУ {page_num} из {total_pages}.
🎯 СОДЕРЖАНИЕ: {subblock_desc}
🚨 ОБЪЁМ: ТОЧНО {expected_chars} символов (±100 максимум)
🎯 ТРЕБОВАНИЯ: Обращение через "ВЫ", "ВАШИ", "ВАМ". Максимум 2-3 цитаты из ответов. Финальный размер: {expected_chars} ± 100 символов.
Используйте загруженные инструкции раздела."""
        return prompt, expected_pages

    def _estimate_tokens(self, conversation: List[Dict]) -> int:
        """Оценка токенов: для кириллицы ~1 символ ≈ 1.5-2 токена в BPE"""
        total_bytes = sum(len(m.get("content", "").encode("utf-8")) for m in conversation)
        return total_bytes // 3

    async def analyze_premium_responses(self, user: User, questions: List[Question], answers: List[Answer]) -> Dict:
        """Платный анализ (50 вопросов) — ПОСТРАНИЧНАЯ ГЕНЕРАЦИЯ 63 страниц.

        Архитектура контекста:
        - base_messages (system + Q&A + initial_ack) сохраняется для КАЖДОГО раздела
        - Между разделами conversation сбрасывается до base_messages
        - Внутри раздела страницы накапливаются, чтобы AI не повторялся
        - Модель 240k токенов — обрезка контекста не нужна
        """
        user_data = self._prepare_user_data(user, questions, answers)
        uid = _user_id(user)
        logger.info(f"Запускаем постраничный премиум AI анализ для user_id={uid} (63 страницы)")

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
        initial_response = await self._make_api_request(base_messages, is_premium=True)
        base_messages.append({"role": "assistant", "content": initial_response["content"]})

        base_tokens = self._estimate_tokens(base_messages)
        logger.info(f"Первичный анализ получен: {len(initial_response['content'])} символов, base ≈ {base_tokens} токенов")

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

        for section_key, section_name, page_count in page_structure:
            conversation = list(base_messages)

            section_prompt = self._get_section_prompt(section_key)
            conversation.append({"role": "user", "content": f'Переходим к разделу "{section_name}". Инструкции:\n{section_prompt}\nИспользуйте эти инструкции для всех страниц данного раздела.'})
            section_response = await self._make_api_request(conversation, is_premium=True)
            conversation.append({"role": "assistant", "content": section_response["content"]})

            section_tokens = self._estimate_tokens(conversation)
            logger.info(f"Раздел: {section_name} ({page_count} страниц), контекст ≈ {section_tokens} токенов")

            for page_num in range(1, page_count + 1):
                page_prompt, _ = self._get_premium_page_prompt(section_key, page_num, page_count)
                conversation.append({"role": "user", "content": page_prompt})
                page_response = await self._make_api_request(conversation, is_premium=True)

                all_individual_pages[f"page_{page_counter:02d}"] = {
                    "content": page_response["content"],
                    "section": section_name,
                    "section_key": section_key,
                    "page_num": page_num,
                    "global_page": page_counter
                }
                conversation.append({"role": "assistant", "content": page_response["content"]})
                page_counter += 1
                await asyncio.sleep(1)

            final_tokens = self._estimate_tokens(conversation)
            logger.info(f"Раздел {section_name} завершён, финальный контекст ≈ {final_tokens} токенов")

            section_pages = {k: v["content"] for k, v in all_individual_pages.items() if v["section_key"] == section_key}
            all_pages[section_key] = "\n\n".join(section_pages.values())

        total_length = sum(len(c) for c in all_pages.values())
        logger.info(f"Премиум-анализ завершён: {total_length} символов, {page_counter - 1} страниц")

        return {
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
            "initial_analysis": initial_response["content"],
            "usage": {"pages_generated": page_counter - 1},
            "timestamp": datetime.utcnow().isoformat()
        }


def _create_fallback_analysis() -> Dict:
    """Базовый анализ без ИИ"""
    return {
        "success": True,
        "page3_analysis": "Ваши ответы показывают уникальные особенности личности. Детальный анализ будет добавлен при включении Perplexity API.",
        "page4_analysis": "На основе ваших ответов можно выделить ключевые характеристики вашего психологического профиля.",
        "page5_analysis": "Рекомендации по развитию будут предоставлены в обновленной версии отчета.",
        "usage": {},
        "timestamp": datetime.utcnow().isoformat()
    }


class AIAnalysisService:
    """
    Фасад для генерации психологического отчёта.
    Использует Perplexity AI при PERPLEXITY_ENABLED=true, иначе — fallback + PDF.
    """
    def __init__(self):
        self.perplexity_enabled = PERPLEXITY_ENABLED
        self.ai_service = PerplexityAIService() if (PERPLEXITY_ENABLED and PERPLEXITY_API_KEY) else None
        self.report_generator = ReportGenerator()

    async def generate_psychological_report(
        self, user: User, questions: List[Question], answers: List[Answer]
    ) -> Dict:
        """Генерация полного психологического отчета (PDF)"""
        try:
            if self.perplexity_enabled and self.ai_service:
                analysis_result = await self.ai_service.analyze_user_responses(user, questions, answers)
                if not analysis_result.get("success"):
                    analysis_result = _create_fallback_analysis()
            else:
                analysis_result = _create_fallback_analysis()

            report_filepath = self.report_generator.create_pdf_report(user, analysis_result)
            logger.info(f"Отчет создан: {report_filepath}")

            return {
                "success": True,
                "report_file": report_filepath,
                "page3_analysis": analysis_result.get("page3_analysis", ""),
                "page4_analysis": analysis_result.get("page4_analysis", ""),
                "page5_analysis": analysis_result.get("page5_analysis", ""),
            }
        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {e}")
            return {
                "success": False,
                "error": str(e),
                "stage": "general"
            }

    async def generate_premium_report(
        self, user: User, questions: List[Question], answers: List[Answer]
    ) -> Dict:
        """Генерация премиум-отчёта (template_pdf_premium)"""
        try:
            if self.perplexity_enabled and self.ai_service:
                analysis_result = await self.ai_service.analyze_premium_responses(user, questions, answers)
                if not analysis_result.get("success"):
                    raise Exception(analysis_result.get("error", "AI error"))
            else:
                raise Exception("Премиум-отчёт требует PERPLEXITY_ENABLED")
            report_filepath = self.report_generator.create_premium_pdf_report(user, analysis_result)
            logger.info(f"Премиум-отчёт создан: {report_filepath}")
            return {"success": True, "report_file": report_filepath}
        except Exception as e:
            logger.error(f"Ошибка генерации премиум-отчёта: {e}")
            return {"success": False, "error": str(e), "stage": "premium"}
