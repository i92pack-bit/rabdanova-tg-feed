# tg-feed — живая мини-лента «3 последних поста» для блока yandex-tg

Блок `clients/rabdanova/out-html/yandex-tg.html` показывает под каждым каналом
3 последних поста Telegram. Данные берутся из `feed.json`, который раз в час
обновляет GitHub Action. Всё бесплатно, свой сервер не нужен.

**Почему так, а не «прямо из Tilda»:** Telegram не отдаёт CORS-заголовок →
браузер не может забрать `t.me/s/...` со страницы rabdanova.ru напрямую. Поэтому
Action складывает данные в `feed.json` на GitHub (там CORS `*`), а блок его читает.

**MAX** публичной ленты не отдаёт вообще → его мини-лента зеркалит Telegram.

**Текст-онли:** сохраняются только подписи постов (без фото). Это осознанно —
на лендинге под Яндекс.Директ нельзя показывать до/после (обнажёнка → бан
модерации + нужен мед-дисклеймер).

## Что где
- `fetch_feed.py` — парсер `t.me/s/<channel>` → `feed.json` (только stdlib).
- `tg-feed.yml` — workflow (кладётся в `.github/workflows/` деплой-репозитория).

## Настройка (10 минут, один раз)
1. Создать **публичный** репозиторий на GitHub, например `rabdanova-tg-feed`.
2. Положить туда:
   - `fetch_feed.py` — в корень;
   - `tg-feed.yml` — по пути `.github/workflows/tg-feed.yml`.
3. Закоммитить/запушить. Вкладка **Actions** → workflow `tg-feed` запустится сам
   (push-триггер), либо жмём **Run workflow**. В корне появится `feed.json`.
4. Проверить ссылку (она с CORS `*`, годится для fetch):
   ```
   https://raw.githubusercontent.com/<USER>/rabdanova-tg-feed/main/feed.json
   ```
5. В блоке `yandex-tg.html` вписать её в скрипт:
   ```js
   var FEED_URL = "https://raw.githubusercontent.com/<USER>/rabdanova-tg-feed/main/feed.json";
   ```
6. Вставить блок в Tilda (T123). Готово — лента обновляется каждый час.

Пока `FEED_URL` пустой — в блоке показываются **запасные** посты из разметки,
ничего не ломается.

## Заметки
- Сменить канал: параметр `--channel` в `tg-feed.yml`.
- Больше/меньше постов: `--limit` (блок всё равно рисует максимум 3).
- Формат `feed.json`:
  ```json
  { "channel": "...", "updated": "ISO", "posts": [
      { "text": "...", "url": "https://t.me/ch/123", "type": "video|photo|text", "ago": "2 дн" }
  ] }
  ```
- Если Telegram поменяет вёрстку `t.me/s`, парсер может сломаться — тогда правим
  регулярки в `fetch_feed.py` (Action упадёт с понятной ошибкой, лента останется
  на прошлом `feed.json`).
- Проверить локально: `python3 fetch_feed.py --channel dr_rabdanova --out feed.json`.
