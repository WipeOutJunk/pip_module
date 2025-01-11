from flask import Flask, request, jsonify, session
from pdf_converter import pdf_to_text
from ollama_interface import send_to_ollama
import os
from flasgger import Swagger
from config import Config
import logging
from time import time
from difflib import SequenceMatcher
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
# Инициализация приложения Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.secret_key = Config.SECRET_KEY  # Для хранения сессии
swagger = Swagger(app)

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')



@app.route('/generate-test', methods=['POST'])
def generate_test():
    """
    Генерация теста на основе PDF файла.
    ---
    tags:
      - Test Generation
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: PDF файл для конвертации в тест
      - name: question_count
        in: formData
        type: integer
        required: true
        description: Количество вопросов для генерации
    responses:
      200:
        description: Успешная генерация теста
        schema:
          type: object
          properties:
            status:
              type: string
              description: Статус операции
            questions:
              type: array
              items:
                type: object
                properties:
                  question:
                    type: string
                    description: Сгенерированный вопрос
                  options:
                    type: array
                    items:
                      type: string
                    description: Варианты ответа
                  correct_answer:
                    type: array
                    items:
                      type: integer
                    description: Индексы правильных ответов
      400:
        description: Ошибки в запросе
        schema:
          type: object
          properties:
            error:
              type: string
              description: Описание ошибки
      500:
        description: Внутренняя ошибка сервера
        schema:
          type: object
          properties:
            error:
              type: string
              description: Описание ошибки
    """
    if 'file' not in request.files or 'question_count' not in request.form:
        return jsonify({"status": "error", "error_message": "Нет файла или количества вопросов в запросе"}), 400

    file = request.files['file']
    try:
        question_count = int(request.form['question_count'])
    except ValueError:
        return jsonify({"status": "error", "error_message": "Количество вопросов должно быть числом"}), 400

    if file.filename == '':
        return jsonify({"status": "error", "error_message": "Файл не выбран"}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"status": "error", "error_message": "Только PDF файлы поддерживаются"}), 400

    temp_path = None
    try:
        temp_dir = Config.UPLOAD_FOLDER
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)

        pdf_text = pdf_to_text(temp_path)
        if isinstance(pdf_text, dict) and 'error' in pdf_text:
            return jsonify(pdf_text), 500

        if 'question_history' not in session:
            session['question_history'] = []

        questions = []
        start_time = time()
        max_duration = Config.MAX_GENERATION_TIME

        while len(questions) < question_count:
            if time() - start_time > max_duration:
                logger.error("Превышено время генерации вопросов.")
                return jsonify({"status": "error", "error_message": "Не удалось сгенерировать вопросы за отведённое время"}), 500

            result = generate_unique_question(pdf_text, session['question_history'])
            if result:
                session['question_history'].append(result['question'])
                questions.append(result)

        return jsonify({"status": "success", "questions": questions}), 200
    except Exception as e:
        logger.error(f"Ошибка генерации теста: {e}")
        return jsonify({"status": "error", "error_message": str(e)}), 500
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def is_similar_question(new_question, history, threshold=0.7):
    stop_words = set(stopwords.words('russian'))
    new_tokens = [
        word for word in word_tokenize(new_question.lower())
        if word.isalnum() and word not in stop_words
    ]
    for past_question in history:
        past_tokens = [
            word for word in word_tokenize(past_question.lower())
            if word.isalnum() and word not in stop_words
        ]
        similarity = SequenceMatcher(None, new_tokens, past_tokens).ratio()
        if similarity > threshold:
            logger.warning(f"Повторяющийся вопрос: {new_question}")
            return True
    return False


def generate_unique_question(text, history, max_attempts=10):
    for attempt in range(max_attempts):
        try:
            result = send_to_ollama(text, history=history, max_answers=4)
            if result["status"] != "success" or not all(key in result for key in ["question", "options", "correct_answer"]):
                logger.error(f"Ошибка при генерации вопроса: {result.get('error_message', 'Неизвестная ошибка')}")
                continue

            question = result["question"]
            # if not is_similar_question(question, history):
            #     logger.info(f"Добавлен уникальный вопрос: {question}")
            #     return result
            logger.info(f"Добавлен вопрос без проверки уникальности: {question}")
            return result
        except Exception as e:
            logger.error(f"Ошибка генерации уникального вопроса: {e}")
    logger.error("Не удалось сгенерировать уникальный вопрос.")
    return None


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=Config.FLASK_PORT, debug=Config.FLASK_DEBUG)