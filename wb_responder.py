import os
import time
import logging
import anthropic
import requests

# ─── Настройки ────────────────────────────────────────────────────────────────
WB_API_TOKEN    = os.environ.get("WB_API_TOKEN", "")       # Токен WB (раздел «Общение с покупателями»)
ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
POLL_INTERVAL   = int(os.environ.get("POLL_INTERVAL", "60"))  # секунды между проверками
BRAND_NAME      = os.environ.get("BRAND_NAME", "")            # Название вашего магазина/бренда

# ─── Логирование ──────────────────────────────────────────────────────────────
logging.basicConfig(
      level=logging.INFO,
      format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ─── WB API ────────────────────────────────────────────────────────────────────
WB_BASE      = "https://feedbacks-api.wildberries.ru"
WB_QUESTIONS = "https://feedbacks-api.wildberries.ru"

HEADERS = {"Authorization": WB_API_TOKEN, "Content-Type": "application/json"}

claude = anthropic.Anthropic(api_key=ANTHROPIC_KEY)


# ══════════════════════════════════════════════════════════════════════════════
#  ОТЗЫВЫ
# ══════════════════════════════════════════════════════════════════════════════

def get_unanswered_feedbacks() -> list:
      """Получить все отзывы без ответа (isAnswered=false)."""
      url = f"{WB_BASE}/api/v1/feedbacks"
      params = {"isAnswered": "false", "take": 100, "skip": 0}
      try:
                r = requests.get(url, headers=HEADERS, params=params, timeout=15)
                r.raise_for_status()
                data = r.json()
                return data.get("data", {}).get("feedbacks", [])
except Exception as e:
        log.error(f"Ошибка при получении отзывов: {e}")
        return []


def post_feedback_reply(feedback_id: str, text: str) -> bool:
      """Опубликовать ответ на отзыв."""
      url = f"{WB_BASE}/api/v1/feedbacks"
      payload = {"id": feedback_id, "text": text}
      try:
                r = requests.patch(url, headers=HEADERS, json=payload, timeout=15)
                r.raise_for_status()
                log.info(f"  ✅ Ответ на отзыв {feedback_id} опубликован")
                return True
except Exception as e:
        log.error(f"  ❌ Ошибка при публикации ответа на отзыв {feedback_id}: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  ВОПРОСЫ
# ══════════════════════════════════════════════════════════════════════════════

def get_unanswered_questions() -> list:
      """Получить все вопросы без ответа."""
      url = f"{WB_QUESTIONS}/api/v1/questions"
      params = {"isAnswered": "false", "take": 100, "skip": 0}
      try:
                r = requests.get(url, headers=HEADERS, params=params, timeout=15)
                r.raise_for_status()
                data = r.json()
                return data.get("data", {}).get("questions", [])
except Exception as e:
        log.error(f"Ошибка при получении вопросов: {e}")
        return []


def post_question_reply(question_id: str, text: str) -> bool:
      """Опубликовать ответ на вопрос."""
      url = f"{WB_QUESTIONS}/api/v1/questions"
      payload = {"id": question_id, "text": text, "answer": {"text": text}}
      try:
                r = requests.patch(url, headers=HEADERS, json=payload, timeout=15)
                r.raise_for_status()
                log.info(f"  ✅ Ответ на вопрос {question_id} опубликован")
                return True
except Exception as e:
        log.error(f"  ❌ Ошибка при публикации ответа на вопрос {question_id}: {e}")
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  CLAUDE — генерация ответов
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_FEEDBACK = f"""Ты — вежливый менеджер интернет-магазина {BRAND_NAME} на Wildberries.
Твоя задача — написать короткий, искренний и профессиональный ответ на отзыв покупателя.

Правила:
- Если отзыв положительный (оценка 4-5): поблагодари и пригласи снова
- Если отзыв нейтральный (оценка 3): поблагодари за честность, извинись за недочёты
- Если отзыв отрицательный (оценка 1-2): извинись, предложи связаться с поддержкой для решения проблемы
- Отвечай только текстом ответа, без вводных фраз вроде «Ответ:»
- Максимум 3-4 предложения
- Не упоминай конкурентов
- Пиши на русском языке"""

SYSTEM_QUESTION = f"""Ты — вежливый менеджер интернет-магазина {BRAND_NAME} на Wildberries.
Твоя задача — дать чёткий и полезный ответ на вопрос покупателя о товаре.

Правила:
- Отвечай по существу вопроса
- Если информации недостаточно — вежливо попроси уточнить или направь в поддержку
- Максимум 3-4 предложения
- Пиши на русском языке
- Отвечай только текстом ответа, без вводных фраз"""


def generate_reply(system_prompt: str, user_text: str) -> str:
      """Сгенерировать ответ через Claude."""
      try:
                response = claude.messages.create(
                              model="claude-haiku-4-5",
                              max_tokens=512,
                              system=system_prompt,
                              messages=[{"role": "user", "content": user_text}],
                )
                return response.content[0].text.strip()
except Exception as e:
        log.error(f"Ошибка Claude API: {e}")
        return ""


# ══════════════════════════════════════════════════════════════════════════════
#  ОСНОВНОЙ ЦИКЛ
# ══════════════════════════════════════════════════════════════════════════════

def process_feedbacks():
      feedbacks = get_unanswered_feedbacks()
      log.info(f"Отзывов без ответа: {len(feedbacks)}")
      for fb in feedbacks:
                fb_id   = fb.get("id", "")
                rating  = fb.get("productValuation", 0)
                text    = fb.get("text", "").strip()
                product = fb.get("subjectName", "товар")

          if not fb_id:
                        continue

        user_message = f"Товар: {product}\nОценка: {rating}/5\nОтзыв: {text}"
        reply = generate_reply(SYSTEM_FEEDBACK, user_message)

        if reply:
                      post_feedback_reply(fb_id, reply)
                      time.sleep(1)  # пауза между запросами


def process_questions():
      questions = get_unanswered_questions()
    log.info(f"Вопросов без ответа: {len(questions)}")
    for q in questions:
              q_id    = q.get("id", "")
              text    = q.get("text", "").strip()
              product = q.get("subjectName", "товар")

        if not q_id:
                      continue

        user_message = f"Товар: {product}\nВопрос покупателя: {text}"
        reply = generate_reply(SYSTEM_QUESTION, user_message)

        if reply:
                      post_question_reply(q_id, reply)
                      time.sleep(1)


def run():
      log.info("🚀 WB Auto-Responder запущен")
    log.info(f"   Интервал проверки: {POLL_INTERVAL} сек.")
    log.info(f"   Бренд: {BRAND_NAME or '(не задан)'}")

    if not WB_API_TOKEN:
              log.error("❌ WB_API_TOKEN не задан! Остановка.")
              return
          if not ANTHROPIC_KEY:
                    log.error("❌ ANTHROPIC_API_KEY не задан! Остановка.")
                    return

    while True:
              try:
                            log.info("── Проверка отзывов ──")
                            process_feedbacks()
                            log.info("── Проверка вопросов ──")
                            process_questions()
except Exception as e:
            log.error(f"Необработанная ошибка в основном цикле: {e}")
        log.info(f"Следующая проверка через {POLL_INTERVAL} сек...\n")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
      run()
