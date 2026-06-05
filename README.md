# WB Auto-Responder + Claude Telegram Bot

## Авто-ответы на WB — wb_responder.py

Скрипт автоматически читает новые отзывы и вопросы покупателей на WB, генерирует ответы через Claude AI и публикует их обратно.

### Переменные окружения

- `WB_API_TOKEN` — токен WB с доступом к разделу "Общение с покупателями" (ОБЯЗАТЕЛЬНЫЙ)
- - `ANTHROPIC_API_KEY` — ключ Anthropic Claude API (ОБЯЗАТЕЛЬНЫЙ)
  - - `BRAND_NAME` — название вашего магазина/бренда (рекомендуется)
    - - `POLL_INTERVAL` — интервал проверки в секундах (по умолчанию: 60)
     
      - ### Как получить WB API токен
     
      - 1. Войдите в Личный кабинет WB Seller: https://seller.wildberries.ru
        2. 2. Перейдите в раздел "Интеграции по API"
           3. 3. Создайте Персональный токен с доступом к категории "Общение с покупателями"
              4. 4. Скопируйте токен и добавьте в переменные окружения
                
                 5. ### Запуск
                
                 6. ```bash
                    pip install -r requirements.txt
                    export WB_API_TOKEN=ваш_токен
                    export ANTHROPIC_API_KEY=ваш_ключ
                    export BRAND_NAME="Мой магазин"
                    python wb_responder.py
                    ```

                    **Важно:** wb_responder.py — постоянно работающий процесс. Vercel НЕ подходит. Используйте Railway (https://railway.app) или VPS-сервер.
