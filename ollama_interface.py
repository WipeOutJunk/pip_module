import re
import json
import logging
import requests
from config import Config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_to_ollama(text, history=None, max_answers=4):
    """
    Отправляет текст в Ollama для генерации уникального вопроса.
    """
    try:
        history_prompt = ""
        if history:
            history_prompt = "\nИстория предыдущих вопросов:\n" + "\n".join(f"- {q}" for q in history)

        prompt = f"""
        Представь, что ты преподаватель, который готовит тестовые вопросы по материалу. 
        Используя предоставленный текст, составь 1 уникальный вопрос.
        Вопрос должен содержать от 3 до {max_answers} вариантов ответа. Правильный ответ может быть только ОДИН.
        
        Текст материала:
        {text}
        
        УЖЕ СУЩЕСТВУЮЩИЕ ВОПРОСЫ, ИХ НЕЛЬЗЯ ИСПОЛЬЗОВАТЬ, ТВОЙ ВОПРОС ДОЛЖЕН БЫТЬ УНИКАЛЬНЫМ:
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
        
        ollama_url = f"{Config.OLLAMA_API_URL}/api/generate"
        
        payload = {
            "model": Config.OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }
        
        response = requests.post(ollama_url, json=payload)
        response.raise_for_status()
        response_data = response.json()

        logger.info(f"Ollama response: {response_data}")

        return parse_ollama_response(response_data.get("response", ""), max_answers)

    except Exception as e:
        logger.error(f"Ошибка при обращении к Ollama: {e}")
        return {"status": "error", "error_message": str(e)}

def parse_ollama_response(content, max_answers=4):
    """
    Парсит ответ от Ollama, извлекает вопрос, варианты ответов и правильный ответ.
    """
    try:
        logger.info(f"Parsing content: {content}")

        question_match = re.search(r"(?:- )?Вопрос: (.+?)(?:\n|$)", content, re.DOTALL)
        question = question_match.group(1).strip() if question_match else None

        if not question:
            raise ValueError("Не удалось извлечь вопрос")

        options_match = re.findall(r"\d[.)]\s(.+)", content)
        options = [opt.strip() for opt in options_match][:max_answers]

        if len(options) < 3:
            raise ValueError(f"Недостаточное количество вариантов ответа: {len(options)}")

        correct_answer_match = re.search(r"(?:- )?Правильный ответ: (.+)", content, re.DOTALL)
        correct_answer_raw = correct_answer_match.group(1).strip() if correct_answer_match else None

        if not correct_answer_raw:
            raise ValueError("Не удалось извлечь правильный ответ")

        correct_numbers = list(set(int(num) for num in re.findall(r"\d+", correct_answer_raw) if int(num) <= len(options)))

        if not correct_numbers:
            raise ValueError("Правильный ответ не соответствует вариантам")

        return {
            "status": "success",
            "question": question,
            "options": options,
            "correct_answer": correct_numbers,
        }

    except Exception as e:
        logger.error(f"Ошибка при парсинге ответа: {e}")
        return {"status": "error", "error_message": str(e)}
