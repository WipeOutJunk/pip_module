import re
import json
import logging
from ollama import chat
from config import Config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_to_ollama(text, history=None, max_answers=4):
    """
    Отправляет текст в нейросеть для генерации одного вопроса.
    """
    try:
        # Логика для учёта истории
        history_prompt = ""
        if history:
            history_prompt = f"\nИстория предыдущих вопросов:\n" + "\n".join(f"- {q}" for q in history)

        # Формируем запрос с учётом истории
        prompt = f"""
        Представь что ты преподаватель, который готовит тестовые вопросы по своему материалу и тебе нужно 
        используя предоставленный текст, составь 1 уникальный вопрос по материалу.
        Вопрос должен содержать от 3 до {max_answers} вариантов ответа. Правильный ОТВЕТ может быть только ОДИН.

        Текст материала:
        {text}
        
        УЖЕ СУЩЕСТВУЮЩИЕ ВОПРОСЫ, ИХ НЕЛЬЗЯ ИСПОЛЬЗОВАТЬ, ТВОЙ ВОПРОС ДОЛЖЕН БЫТЬ УНИКАЛЬНЫМ ОТ УЖЕ СОСТАВЛЕННЫХ:
        {history_prompt}

        Формат ответа:
        - Вопрос: [Текст вопроса]
        - Варианты ответа:
          1. [Первый вариант]
          2. [Второй вариант]
          3. [Третий вариант]
          4. [Четвёртый вариант]
        - Правильный ответ: [Номера варианта ответа]
        """

        # Отправляем запрос
        response = chat(
            model=Config.OLLAMA_MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.5},
        )

        logger.info(f"Ollama response: {response.message.content}")

        # Парсим ответ
        return parse_ollama_response(response.message.content, max_answers)

    except Exception as e:
        logger.error(f"Ошибка при обращении к Ollama: {e}")
        return {"status": "error", "error_message": str(e)}

def parse_ollama_response(content, max_answers=4):
    """
    Парсит ответ от Ollama, обрабатывает вопросы, варианты ответа и правильный ответ.
    """
    try:
        logger.info(f"Parsing content: {content}")

        # Шаблон для извлечения вопроса
        question_match = re.search(r"(?:- )?Вопрос: (.+?)(?:\n|$)", content, re.DOTALL)
        question = question_match.group(1).strip() if question_match else None

        if not question:
            raise ValueError("Не удалось извлечь вопрос")

        # Шаблон для извлечения вариантов ответа
        options_match = re.findall(r"\d\.\s(.+)", content)
        options = [opt.strip() for opt in options_match][:max_answers]

        if len(options) < 3:
            raise ValueError(f"Недостаточное количество вариантов ответа: {len(options)}")

        # Шаблон для извлечения правильного ответа
        correct_answer_match = re.search(r"(?:- )?Правильный ответ: (.+)", content, re.DOTALL)
        correct_answer_raw = correct_answer_match.group(1).strip() if correct_answer_match else None

        if not correct_answer_raw:
            raise ValueError("Не удалось извлечь правильный ответ")

        # Преобразуем правильный ответ в числа
        correct_numbers = list(
            set(int(num) for num in re.findall(r"\d+", correct_answer_raw) if int(num) <= len(options))
        )

        if not correct_numbers:
            raise ValueError("Правильный ответ не соответствует вариантам")

        # Возвращаем обработанный результат
        return {
            "status": "success",
            "question": question,
            "options": options,
            "correct_answer": correct_numbers,
        }

    except Exception as e:
        logger.error(f"Ошибка при парсинге ответа: {e}")
        return {"status": "error", "error_message": str(e)}
