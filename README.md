# **FlashCards**

Наше приложение Flashcards поможет вам быстро и эффективно запомнить учебный материал! 📚 Создавайте колоды с карточками, изучайте их и закрепляйте знания.

🌐 Хотите изучать английский язык? Создайте языковую колоду! Выберите исходный и целевой язык (английский → русский или русский → английский), введите слово, а перевод добавится автоматически через LibreTranslate.
# <a name="_toc201011389"></a>**Участники проекта**

|ФИО|Группа|
| :- | :- |
|Анисимова Алина Вячеславовна|5130904/20102|
|Емшанова Полина Игоревна|5130904/20102|
|Кузнецова Елизавета Дмитриевна|5130904/20102|
|Смирникова Лилиана Егоровна|5130904/20102|

# **Этапы**
[Определение проблемы](#_toc201011390)

[Выработка требований](#_toc201011391)

[Разработка архитектуры и детальное проектирование](#_toc201011392)

[Характер нагрузки на сервис](#_toc201011393)

[Соотношение R/W нагрузĸи](#_toc201011394)

[Объемы трафика](#_toc201011395)

[Объемы дисковой системы:](#_toc201011396)

[Диаграммы C4 Model](#_toc201011397)

[Контраĸты API + Ожидаемые нефунĸциональные требования на время отĸлиĸа](#_toc201011398)

[Схема базы данных](#_toc201011399)

[Схема масштабирования при росте нагрузки в 10 раз](#_toc201011400)

[Unit-тестирование](#_toc201011401)

[Интеграционное тестирование](#_toc201011402)

[Сборка](#_toc201011403)

[Вывод](#_toc201011404)


# <a name="_toc201009652"></a><a name="_toc201011390"></a>**Определение проблемы**
Молодым людям, изучающим какой-либо материал (к примеру, иностранные языки), не хватает удобного и доступного инструмента для регулярной практики и повторения материала прямо в привычной среде, например в мессенджере Telegram. Им приходится использовать сторонние приложения, переключаться между платформами  и ставить себе напоминание о повторении выученных терминов. Это снижает мотивацию и увеличивает риск забывания выученного.

# <a name="_toc201009653"></a><a name="_toc201011391"></a>**Выработка требований** 
**Пользовательские истории:**

1. Так не хочется скачивать какие-то сторонние приложения для изучения флеш-карточек, заполнять ими память телефона, а потом получать кучу рекламы и ненужных уведомлений. Вот бы все было в одном месте, например в чате с телеграм-ботом. 
1. Было бы удобно иметь встроенный переводчик в приложении по повторению иностранных слов, чтобы он автоматически подставлял перевод слова, но при этом иметь возможность ввести для слова какое-то свое значение.  
1. Мне не хочется регистрироваться в куче каких-то приложений и оставлять там свои данные, вдруг я забуду пароль, мне заблокируют почту или я перейду на новое устройство и потеряю свой прогресс по изучению иностранных слов или терминов. Как хорошо бы было, если бы приложение и его данные были привязаны к моему аккаунту в телеграме и сразу выдавало мне мои колоды и карточки, с какого бы устройства я ни решил их посмотреть. 

**Оценка числа пользователей сервиса:**

~ 10 тыс. пользователей в сутки

**Оценка периода хранения информации:** 

Храним информацию 10 лет
# <a name="_toc201009654"></a><a name="_toc201011392"></a>**Разработка архитектуры и детальное проектирование** 
## <a name="_toc201009655"></a><a name="_toc201011393"></a>**Характер нагрузки на сервис**
Для анализа характера нагрузки будем исходить из нескольких возможных вариантов поведения пользователя: 

1. создание новой колоды -> создание карточек (с использованием переводчика) -> просмотр своих колод -> переход к колоде для повторения карточек -> удаление ненужных карточек.
1. создание новой колоды -> создание карточек (без использования переводчика) -> просмотр своих колод -> переход к колоде для повторения карточек -> удаление ненужных карточек.
1. просмотр колод -> переход к одной из колод для повторения карточек -> удаление ненужных карточек (2-3 раза).

Предположим, средний размер колоды равен 30 карточкам, в колоде будет встроенный переводчик, если это колода для изучения иностранных слов. Примерно 5 карточек из колоды пользователь запомнит сразу и удалит из колоды. 

Если пользователь заходит для повторения карточек, будем считать, что он повторяет за раз не больше 2-3 колод, также удаляя ненужные карточки, которые уже нет необходимости повторять. 

1 вариант:

- <a name="_hlk200993643"></a>Создание новой колоды: 1 запрос к backend ("/decks/")
- Создание карточек: 30 запросов к backend (“/lang\_cards/{card\_id}")
- Перевод слов: по 30 запросов к backend:
1. Выбор языков перевода (например, из английского в русский) (“/languages/”)
1. Перевод слова: 2 запроса к backend (“/translate” и “translate\_word”)
- Просмотр своих колод: 1 запрос к backend(“/decks/{telegram\_id}/”)
- Просмотр карточек в колоде: 1 запрос к backend (“/lang\_cards/{deck\_id}”)
- Удаление карточек из колоды: 5 запросов к backend ("/lang\_cards/{card\_id}")

2 вариант:

- Создание новой колоды: 1 запрос к backend ("/decks/")
- Создание карточек: 30 запросов к backend (“/cards/{card\_id}")
- Просмотр своих колод: 1 запрос к backend(“/decks/{telegram\_id}/”)
- Просмотр карточек в колоде: 1 запрос к backend (“/cards/{deck\_id}”)
- Удаление карточек из колоды: 5 запросов к backend ("/cards/{card\_id}")

3 вариант:

- Просмотр своих колод: 1 запрос к backend(“/decks/{telegram\_id}/”)
- Просмотр карточек в колоде: 1 запрос к backend (“/cards/{deck\_id}”)
- Удаление карточек из колоды: 5 запросов к backend ("/cards/{card\_id}")

При условии, что пользователь изучает несколько колод за раз, количество запросов в 3 варианте умножается на соответствующее количество колод.
### <a name="_toc201009656"></a><a name="_toc201011394"></a>**Соотношение R/W нагрузĸи**
- Read (чтение):
1. Backend (api): некоторые эндпоинты отвечают за чтение данных из базы данных (получение карточек, получение языковых карточек, получение колод, получение языковых колод)
1. Bot: В функциях process\_time и check\_time\_and\_notify происходит чтение сообщения пользователя с указанием времени отправки уведомлений, чтение состояния FSM, чтение словаря users и текущего времени.
- Write (запись):
1. Backend (api): часть эндпоинтов отвечает за запись/удаление данных (получение колод, получение языковых колод, получение карточек, получение языковых карточек, удаление колод, удаление языковых колод, удаление карточек, удаление языковых карточек)
1. Bot: функции process\_time, cmd\_cancel, check\_time\_and\_notify обновляют словарь users, добавляя или удаляя время отправки уведомлений, а также добавляя или удаляя пользователя в список пользователей с уведомлениями. 

**Вывод:**

Хоть добавление пользователем флеш-карточек создает много write-запросов, пользователи не часто занимаются созданием новых колод. При этом пользователи часто обращаются к одной колоде по несколько раз или повторяют старые, поэтому можно считать, что соотношение Read/Write операций равно ~ 1:1.
### <a name="_toc201009657"></a><a name="_toc201011395"></a>**Объемы трафика**
Предположим, у нас 10 тыс. активных пользователей в день. Каждый из них раз в неделю создает новую колоду. Все пользователи раз в день заходят в приложение повторить 2-3 колоды, при этом у половины пользователей включены уведомления от телеграм-бота. Также, предположим, что каждый пользователь взаимодействует с самим ботом 1–2 раза в неделю (например, /start, /info, /notify для настройки или /cancel).

**Telegram Bot:**

Входящий:

- Сообщения от пользователя: 1 команда не больше 10 байт. 10 байт \* 2 команды в неделю \* 10 000 пользоватлей ~ 195 Кбайт/неделя

Исходящий: 

- Уведомления от бота *NOTIFICATION\_MESSAGE* не больше 100 байт. 100 байт  \* 5000 пользователей ~ 490 Кбайт/день, то есть ~ 3,4 Мбайт в неделю
- Сообщения от бота: 1 сообщение не больше 800 байт. 800 байт \* 2 сообщения в неделю \* 10 000 пользоватлей ~ 15 Мбайт/неделя

**Итог:** объем внешнего трафика бота составляет ~18,7 Мбайт в неделю, то есть ~ 2,7 Мбайт/день, внутренний трафик отсутствует.

**Mini App + FastAPI:**

Входящий: 

- Создание колоды: ~2 Кбайт /запрос (JSON с параметрами колоды) \* 1429 колод в день = ~2,9 Мбайт /день.
- Повторение колод: ~ 1 Кбайт/день на чтения данных пользователя, ~ 1 Кбайт/день запрос на получение колод, ~ 3 Кбайт/день запрос на получение карточек каждой колоды. 5 Кбайт/день \* 10 000 пользователей ~ 50 Мбайт/день  

Исходящий: 

- Ответ при создании колоды: ~5 Кбайт /ответ (JSON с созданной колодой) \* 1429 колод в день = ~7,1 Мбайт /день.
- Повторение колод: : ~ 10 Кбайт/день на получение колод, ~ 30 Кбайт/день на получение карточек каждой колоды. 40 Кбайт/день \* 10 000 пользователей ~ 400 Мбайт/день

**Итог:** суммарный объем внешнего трафика составляет ~ 460 Мбайт/день. Внутренний трафик отсутсвует.

**FastAPI + PostgreSQL:** 

Внутренний трафик:

- Создание колоды: 1429 запросов POST /decks/ → 1429 INSERT в таблицу в день. 1,429 × (1 Кбайт запрос + 5 Кбайт ответ) ~ 8,6 Мбайт/день.
- Повторение колод: 16,070 API-запросов → ~16,070 SQL-запросов: 
- ~ 3 571 (среднее, если пользователь повторяет 2-3 колоды в день) SELECT для GET /users/ (~5 Кбайт /ответ).
- ~ 3 571 SELECT для GET /decks/ (~10 Кбайт /ответ).
- ~ 8 928 SELECT для GET /cards/ или /lang\_cards/ (~20 Кбайт /ответ).
- Всего: 16 070 × (1 + 15) Кбайт = ~ 256,1 Мбайт /день.

**Итог**: Суммарный объем внутреннего трафика составляет ~ 264,7 Мбайт в день.

**Общий трафик:**

Внутренний: ~ 264,7 Мбайт /день.

Внешний: ~ 462,7 Мбайт /день.
### <a name="_toc201009658"></a><a name="_toc201011396"></a>**Объемы дисковой системы:** 
1. **Данные из таблиц:**
- users: каждый пользователь создается при первом взаимодействии. 10 000 пользователей × 100 байт/запись = 10 000 × 100 = 1 Мбайт
- decks: каждый пользователь создаёт 1 колоду/неделю. За неделю: 10 000 колод. За месяц (30 дней): 10 000 × 4,3 (недель) ~ 43 000 колод. Размер: 43 000 × 200 байт ~ 8,6 Мбайт. Дневной прирост: 1 429 колод × 200 байт ~ 0,29 Мбайт /день.
- cards и lang\_cards: предположим, каждая колода содержит ~ 30 карточек (обычных или языковых). За месяц: 43 000 колод × 30 карточек = 1 290 000 карточек. Размер: 1 290 000 × 500 байт  ~ 430 Мбайт. Дневной прирост: 1 429 колод × 30 × 500 байт ~ 20,6 Мбайт /день. 

Итого: ~ 440 Мбайт данных на старте, дневной прирост составляет ~ 21 Мбайт в день, при условии, что пользователи не будут удалять старые карточки и колоды.

1. **Логи:**
- Telegram-бот: 
  - Логирование в main.py (через logging): команды, уведомления, ошибки.
  - ~ 2 143 команды/день + 5 000 уведомлений → ~ 7 143 записей логов.
  - Средний размер записи: ~ 1 Кбайт.
  - Трафик: 7 143 × 1 Кбайт = ~ 7,1 Мбайт /день.
- FastAPI-бэкенд: 
  - Логи API-запросов: ~ 1 429 (POST /decks) + 16 070 (сессии повтора) = ~ 17 499 запросов/день.
  - Размер: ~ 1 Кбайт /запись.
  - Трафик: 17 499 × 1 Кбайт = ~ 17,5 Мбайт /день.
- Итог: 
  - 7,1 + 17,5 = ~ 24,6 Мбайт /день.
  - Месячный: 24,6 × 30 = ~ 738 Мбайт /месяц.
## <a name="_toc201009659"></a><a name="_toc201011397"></a>**Диаграммы C4 Model**
Уровень 1: System Context Diagram Эта диаграмма показывает, как система вписывается в окружающий мир.

![System Context Diagram](image.png)

В проекте представлены две архитектурные схемы уровня контейнеров (Container Diagram): одна — для локального запуска приложения, вторая — для развернутой версии на хостинге с использованием домена и HTTPS. Это сделано для поддержки локального запуска и разработки. Приложение разработано так, чтобы любой пользователь или разработчик мог скачать исходный код и Docker Compose-файлы и запустить систему у себя на компьютере. Для этого достаточно иметь установленный Docker и выполнить простую команду сборки (.[/](tg://bot_command?command=run)[run.sh](https://run.sh/)). В этой версии компоненты взаимодействуют напрямую по локальным портам, без необходимости в HTTPS и домене. Это удобно для тестирования и отладки. Также представлена развернутая версия с хостингом и HTTPS. Для пользователей конечного продукта реализована развёрнутая версия на сервере, доступная через глобальный домен [https://flashcardsapp.ru](https://flashcardsapp.ru/) и Telegram Bot [@flashcards_new_bot](https://t.me/flashcards_new_bot). Здесь добавлен компонент Nginx как реверс-прокси, который обеспечивает доступ по HTTPS, маршрутизирует запросы к frontend и backend и позволяет использовать приложение как Telegram Mini App (Telegram требует HTTPS). 
![Container Diagram 1](image-1.png)
![Container Diagram 2](image-2.png)

## <a name="_toc201009660"></a><a name="_toc201011398"></a>**Контраĸты API + Ожидаемые нефунĸциональные требования на время отĸлиĸа**
FastAPI-бэкенд (порт 8080)

- **GET /users/{telegram\_id}/info** 
  - Query-params: None
  - Path-params: telegram\_id: int
  - Ответ: 200 OK (JSON: {id: int, telegram\_id: int, name: str}), 404 Not Found, 500 Internal Server Error
  - NFR (время отклика): P95 < 200 ms (быстрое чтение из PostgreSQL с кэшированием в Redis)
- **POST /decks/** 
  - Body (JSON): {telegram\_id: int, name: str, is\_language\_deck: bool, source\_lang: str | null, target\_lang: str | null}
  - Ответ: 201 Created (JSON: {id: int, telegram\_id: int, name: str, is\_language\_deck: bool, source\_lang: str | null, target\_lang: str | null}), 400 Bad Request, 500 Internal Server Error
  - NFR (время отклика): P95 < 300 ms (запись в PostgreSQL)
- **GET /decks/{telegram\_id}/** 
  - Query-params: None
  - Path-params: telegram\_id: int
  - Ответ: 200 OK (JSON: [{id: int, name: str, is\_language\_deck: bool, source\_lang: str | null, target\_lang: str | null}]), 404 Not Found, 500 Internal Server Error
  - NFR (время отклика): P95 < 200 ms (чтение с кэшированием в Redis)
- **DELETE /decks/{deck\_id}** 
  - Path-params: deck\_id: int
  - Ответ: 204 No Content, 404 Not Found, 500 Internal Server Error
  - NFR (время отклика): P95 < 250 ms (удаление с каскадным удалением карточек)
- **POST /cards/** 
  - Body (JSON): {deck\_id: int, term: str, definition: str}
  - Ответ: 201 Created (JSON: {id: int, deck\_id: int, term: str, definition: str}), 400 Bad Request, 500 Internal Server Error
  - NFR (время отклика): P95 < 300 ms (запись в PostgreSQL)
- **GET /cards/{deck\_id}** 
  - Query-params: limit: int = 20, offset: int = 0
  - Path-params: deck\_id: int
  - Ответ: 200 OK (JSON: [{id: int, term: str, definition: str}]), 404 Not Found, 500 Internal Server Error
  - NFR (время отклика): P95 < 200 ms (чтение с пагинацией и кэшированием)
- **POST /lang\_cards/** 
  - Body (JSON): {deck\_id: int, word: str, translation: str, source\_lang: str, target\_lang: str}
  - Ответ: 201 Created (JSON: {id: int, deck\_id: int, word: str, translation: str, source\_lang: str, target\_lang: str}), 400 Bad Request, 500 Internal Server Error
  - NFR (время отклика): P95 < 300 ms (запись в PostgreSQL)
- **GET /lang\_cards/{deck\_id}** 
  - Query-params: limit: int = 20, offset: int = 0
  - Path-params: deck\_id: int
  - Ответ: 200 OK (JSON: [{id: int, word: str, translation: str, source\_lang: str, target\_lang: str}]), 404 Not Found, 500 Internal Server Error
  - NFR (время отклика): P95 < 200 ms (чтение с пагинацией и кэшированием)
- **POST /translate** 
  - Body (JSON): {text: str, source\_lang: str, target\_lang: str}
  - Ответ: 200 OK (JSON: {translated\_text: str}), 400 Bad Request, 500 Internal Server Error
  - NFR (время отклика): P95 < 500 ms (зависит от внешнего API LibreTranslate)
- **POST /reminders/** 
  - Body (JSON): {telegram\_id: int, reminder\_time: str, is\_active: bool}
  - Ответ: 201 Created (JSON: {telegram\_id: int, reminder\_time: str, is\_active: bool}), 400 Bad Request, 500 Internal Server Error
  - NFR (время отклика): P95 < 300 ms (запись в PostgreSQL)
- **GET /reminders/{telegram\_id}** 
  - Path-params: telegram\_id: int
  - Ответ: 200 OK (JSON: {telegram\_id: int, reminder\_time: str, is\_active: bool}), 404 Not Found, 500 Internal Server Error
  - NFR (время отклика): P95 < 200 ms (чтение с кэшированием)

Telegram-бот (интеграция через Telegram Bot API)

- **Команды (/start, /info, /notify, /cancel)** 
  - Ответ: Текстовое сообщение, inline-клавиатура или запрос ввода времени
  - NFR (время отклика): P95 < 500 ms (асинхронная обработка через aiogram, зависит от Telegram Bot API)
- **Уведомления** 
  - Ответ: Текстовое сообщение
  - NFR (время отклика): Доставка в течение 60 секунд от заданного времени (зависит от планировщика и Telegram Bot API)

Фронтенд (Telegram Mini App)

- **Загрузка интерфейса** 
  - NFR (время отклика): < 1 s (зависит от CDN и размера статических файлов)
- **Рендеринг данных** 
  - NFR (время отклика): P95 < 500 ms (зависит от API FastAPI и сети пользователя)

<a name="_toc201009661"></a><a name="_toc201011399"></a>**Схема базы данных**
![Схема базы данных](image-3.png) 

**Почему она выдержит нагрузку?**

**1. Нормализованная структура**. Данные разбиты по 4 небольшим таблицам (users, cards, decks, lang\_cards), что снижает избыточность и ускоряет доступ. Это уменьшает объем передаваемых и обрабатываемых данных.

2\. **Индексация первичных ключей**. Все таблицы имеют первичные ключи (id), что обеспечивает быстрый доступ по JOIN и выборке.

3\. **Связи по внешним ключам**. Четкие связи между пользователями, колодами и карточками позволяют точно фильтровать и быстро доставать нужные данные.

4\. **Масштабируемость PostgreSQL**. PostgreSQL хорошо справляется с высокой конкуренцией на чтение. Поддерживает вертикальное масштабирование (наращивание ресурсов сервера) и оптимизацию под многопоточность.

5\. **Возможность использования кэширования**. Часто используемые данные (например, lang\_cards) можно кэшировать (Redis, Memcached). Это снизит нагрузку на саму БД при пиковых обращениях.

6\**. Отсутствие тяжёлых операций в структуре**. Нет хранения больших объектов (BLOB), только varchar и int, что снижает I/O нагрузку.
## <a name="_toc201009662"></a><a name="_toc201011400"></a>**Схема масштабирования при росте нагрузки в 10 раз**
При 10-кратном росте (100 000 пользователей/день) текущая архитектура столкнется с проблемами. Вот план масштабирования:

1. **Горизонтальное масштабирование Telegram-бота:**\
   Развернуть несколько экземпляров бота для обработки ~21,429 команд и 50,000 уведомлений в день. Использовать вебхуки вместо polling для снижения задержек и балансировщик нагрузки (например, Nginx) для распределения запросов.
1. **Персистентное хранилище для напоминаний:**\
   Перенести данные о 50,000 напоминаниях из памяти (словарь users) в PostgreSQL или Redis для устойчивости при перезапусках. Заменить текущую проверку времени на планировщик задач (например, APScheduler).
1. **Горизонтальное масштабирование FastAPI-бэкенда:**\
   Развернуть несколько экземпляров FastAPI для обработки ~160,713 API-запросов в день (создание колод и повторение). Использовать многопроцессный сервер (например, Gunicorn с Uvicorn) и балансировщик нагрузки (Nginx), чтобы распределить запросы и обеспечить пропускную способность до ~500,000 запросов в день. 
1. **Репликация и шардинг PostgreSQL:**\
   Настроить одну главную базу (master) и две реплики для чтения, чтобы распределить ~80% запросов на чтение (списки колод, карточек). Подготовить шардинг по telegram\_id для будущего роста, чтобы разделить данные (~4.3 GB, ~8.6M карточек). Оптимизировать индексы для ускорения запросов. 
1. **Кэширование данных:**\
   Внедрить Redis для кэширования списков колод и карточек (~80% GET-запросов), чтобы снизить нагрузку на PostgreSQL на ~80%. Установить TTL кэша на 1 час, что уменьшит ~102,856 запросов в день к базе. 

Данная схема позволит превратить проект в отказоустойчивую, масштабируемую систему, готовую к серьезным нагрузкам.

# <a name="_toc201009663"></a><a name="_toc201011401"></a>**Unit-тестирование** 
Проект включает в себя unit-тесты для бэкэнда и фронтенда и обеспечивают высокое покрытие ключевой функциональности

\1)	**api/tetst/unit/** unit-тесты бэкэнда

**1. test\_cards.py**

Тесты для работы с обычными карточками (эндпоинты /cards/).

- test\_create\_card\_valid: Проверяет создание карточки с валидными данными (term, definition, deck\_id). Убеждается, что эндпоинт POST /cards/ возвращает статус 200 и корректные данные карточки, а также что карточка сохраняется в базе данных.
- test\_create\_card\_invalid\_deck: Проверяет обработку ошибки при попытке создать карточку для несуществующей колоды. Убеждается, что эндпоинт возвращает статус 404 с сообщением "Deck not found".
- test\_update\_card\_valid: Проверяет обновление существующей карточки через PUT /cards/{card\_id}. Убеждается, что эндпоинт возвращает статус 200 и обновленные данные карточки (term, definition).
- test\_delete\_card\_valid: Проверяет удаление существующей карточки через DELETE /cards/{card\_id}. Убеждается, что эндпоинт возвращает статус 200 с сообщением "Card deleted successfully".

**2. test\_decks.py**

Тесты для работы с колодами (эндпоинт /decks/).

- test\_create\_deck\_valid: Проверяет создание колоды с валидными данными (name, telegram\_id, is\_language\_deck, source\_lang, target\_lang). Убеждается, что эндпоинт POST /decks/ возвращает статус 200 и корректные данные колоды.
- test\_create\_deck\_missing\_fields: Проверяет обработку ошибки при создании языковой колоды с отсутствующими полями (source\_lang, target\_lang). Убеждается, что эндпоинт возвращает статус 400 с сообщением об обязательных полях.

**3. test\_languages.py**

Тест получения списка языков (эндпоинт /languages/).

- test\_get\_languages\_success: Проверяет успешное получение списка доступных языков от сервиса перевода. Мокает HTTP-запрос к внешнему сервису и убеждается, что эндпоинт GET /languages/ возвращает статус 200 и список языков (например, [{"code": "en", "name": "English"}]).

**4. test\_lang\_cards.py**

Тесты для работы с языковыми карточками (эндпоинт /lang\_cards/).

- test\_create\_lang\_card\_valid: Проверяет создание языковой карточки с валидными данными (word, deck\_id, source\_lang, target\_lang). Мокает перевод слова и убеждается, что эндпоинт POST /lang\_cards/ возвращает статус 200, а карточка содержит правильное слово и перевод (например, "Hello" → "Hola").
- test\_create\_lang\_card\_invalid\_deck: Проверяет обработку ошибки при попытке создать языковую карточку для несуществующей или неподходящей колоды. Убеждается, что эндпоинт возвращает статус 400 с сообщением "Invalid deck for language cards".

**5. test\_translate.py**

Тесты для перевода слов (эндпоинт /translate).

- test\_translate\_success: Проверяет успешный перевод слова с использованием внешнего сервиса перевода. Мокает HTTP-запрос и убеждается, что эндпоинт POST /translate возвращает статус 200 и правильный перевод (например, "Hello" → "Привет").
- test\_translate\_service\_unavailable: Проверяет обработку ошибки, когда сервис перевода недоступен. Мокает сбой HTTP-запроса и убеждается, что эндпоинт возвращает статус 503 с сообщением "Translation service unavailable".

**6. test\_users.py**

Тесты для функции управления пользователями (get\_or\_create\_user).

- test\_get\_or\_create\_user\_existing: Проверяет получение существующего пользователя по telegram\_id. Убеждается, что функция возвращает пользователя без создания новой записи в базе данных.
- test\_get\_or\_create\_user\_new: Проверяет создание нового пользователя, если он не существует. Убеждается, что функция создает пользователя с указанным telegram\_id и сохраняет его в базе данных.

\2)	frontend/src/App\.test\.jsx unit-тесты фронтенда

**1. test\_deck\_creation\_form\_render**

Проверяет рендеринг формы создания колоды.

- Убеждается, что компонент App рендерит форму с заголовком "Создать новую колоду", полем ввода названия колоды (с placeholder "Введите название") и чекбоксом "Языковая колода".

**2. test\_toggle\_language\_deck\_checkbox**

Проверяет активацию чекбокса "Языковая колода" и отображение селекторов языков.

- Убеждается, что при клике на чекбок "Языковая колода" в форме создания колоды появляются селекторы "Выберите исходный язык" и "Выберите целевой язык".
- Проверяет, что в селекторах отображаются языки из замоканного ответа /languages/ ("English" и "Spanish").

**3. test\_create\_deck\_valid**

Проверяет создание колоды с валидными данными.

- Убеждается, что при заполнении поля названия колоды ("Test Deck") и клике на кнопку "Создать колоду" отправляется POST-запрос к эндпоинту /decks/ с корректными данными (telegram\_id, name, is\_language\_deck=false, source\_lang=null, target\_lang=null). Проверяет, что отображается тост об успешном создании (toast-success) 

**4. test\_create\_deck\_empty\_name**

Проверяет обработку ошибки при попытке создать колоду без названия.

- Убеждается, что при клике на кнопку "Создать колоду" с пустым полем названия отображается тост с предупреждением (toast-warning) и сообщением "Введите название колоды".

**5. test\_toggle\_show\_decks**

Проверяет переключение отображения списка колод и рендеринг колод.

- Убеждается, что при клике на кнопку "Показать" отправляется GET-запрос к эндпоинту /decks/1/ и в DOM отображается список колод.

**6. test\_open\_card\_modal**

Проверяет открытие модального окна редактирования карточек.

- Убеждается, что при клике на кнопку "Редактировать карточки" в списке колод открывается модальное окно с заголовком "Редактировать карточки" и полем ввода для термина.
- Проверяет, что перед открытием модального окна список колод загружается через GET /decks/1/.

**7. test\_remove\_card\_row**

Проверяет удаление строки карточки в модальном окне редактирования.

- Убеждается, что при добавлении новой строки карточки (клик на "+") и последующем клике на кнопку удаления ("×") количество строк с полями для термина уменьшается.

**8. test\_save\_edited\_cards**

Проверяет сохранение отредактированных карточек.

- Убеждается, что при редактировании термина карточки (изменение на "Updated term") и клике на кнопку "Сохранить" отправляется PUT-запрос к эндпоинту /cards/{card\_id} и отображается тост об успешном сохранении (toast-success).

**9. test\_auto\_translate\_lang\_card**

Проверяет автоперевод слова в модальном окне редактирования языковой колоды.

- Убеждается, что при вводе слова ("hello") в поле "Слово" языковой колоды и потере фокуса (событие blur) отправляется POST-запрос к эндпоинту /translate, и в поле перевода отображается результат ("hola").

**10. test\_delete\_deck\_with\_confirmation**

Проверяет удаление колоды с подтверждением.

- Убеждается, что при клике на кнопку "Удалить колоду" отображается модальное окно подтверждения (confirm-modal), а после клика на кнопку "Подтвердить" отправляется DELETE-запрос к эндпоинту /decks/1 и отображается тост об успешном удалении (toast-success).

**11. test\_start\_study\_mode**

Проверяет запуск режима изучения карточек.

- Убеждается, что при клике на кнопку "Учить карточки" в списке колод отображается интерфейс изучения с заголовком "Изучение карточек" и первой карточкой ("Term 1"). 
# <a name="_toc201009664"></a><a name="_toc201011402"></a>**Интеграционное тестирование** 
**api/tests/test\_integration.py**

Интеграционный тест test\_user\_full\_journey проверяет полный сценарий взаимодействия пользователя с приложением, имитируя реальную пользовательскую историю. Тест включает следующие проверки:

- **Создание пользователя**: Проверяет, что пользователь с указанным telegram\_id создается и сохраняется в базе данных.
- **Создание колод**: Проверяет создание обычной и языковой колоды через POST /decks/, включая валидацию полей (name, is\_language\_deck, source\_lang, target\_lang).
- **Добавление карточек**: Проверяет создание обычной карточки (POST /cards/) и языковой карточки с автопереводом (POST /lang\_cards/), включая корректность перевода (например, "Hello" → "привет").
- **Ожидание сервиса перевода**: Проверяет готовность внешнего сервиса перевода (LibreTranslate) с помощью healthcheck-запроса, обеспечивая надежность теста.
- **Перевод слова**: Проверяет работу эндпоинта POST /translate, убеждаясь, что перевод выполняется корректно.
- **Режим изучения**: Проверяет получение карточек для режима изучения через GET /cards/{deck\_id} и GET /lang\_cards/{deck\_id}, имитируя просмотр карточек в приложении.
- **Удаление данных**: Проверяет удаление карточек (DELETE /cards/{card\_id}, DELETE /lang\_cards/{card\_id}) и колод (DELETE /decks/{deck\_id}), убеждаясь, что данные удаляются из базы.
- **Получение списка языков**: Проверяет эндпоинт GET /languages/, убеждаясь, что возвращается непустой список языков.

Тест использует реальную базу данных (через SessionLocal) и сервис перевода, чтобы проверить интеграцию всех компонентов приложения в рамках единого сценария.
# <a name="_toc201009665"></a><a name="_toc201011403"></a>**Сборка** 
Telegram Mini App – это веб-приложение, которое запускается через бота в телеграме. Телеграм требует защищенную ссылку на приложение, поэтому при локальной сборке и запуске нет возможности протестировать приложение через телеграм. Но его можно открыть в браузере на http://localhost:5173/?test_mode=true и протестировать весь функционал приложение, за исключением авторизации в телеграме (используется тестовый пользователь по умолчанию). Более того, мы захостили приложение и его можно открыть в телеграме через бота @flashcards\_new\_bot. Далее идет описание локальной сборки с возможностью открытия приложения в браузере в тестовом режиме.

Проект использует Docker-контейнеризацию и автоматизированную сборку через shell-скрипт.

**Команды сборки**

\# Полная сборка, тестирование и запуск (по умолчанию)

./run.sh

\# Только сборка Docker образов

./run.sh build

\# Запуск уже собранных сервисов

./run.sh start

\# Остановка всех сервисов

./run.sh stop

**Процесс сборки**

1\.	Сборка образов: docker compose build - создает Docker образы для всех сервисов

2\.	Тестирование: Запуск unit-тестов и интеграционного теста в контейнерах

3\.	Развертывание: docker compose up -d - запуск всех сервисов в background режиме

**Особенности сборки**

- **Автоматические health checks** для критических сервисов
- **Dependency management** - telegram\_bot ждет готовности всех API
- **Volume mapping** для персистентного хранения данных

**Требования к окружению**

- Docker и Docker Compose
- Bash shell для выполнения run.sh
- Переменные окружения

Для правильной работы системы необходимо настроить следующие переменные окружения в .env файле в корне проекта:

BOT\_TOKEN=your\_telegram\_bot\_token

DATABASE\_URL=postgresql+psycopg2://postgres:1234@postgres:5432/flashcards

# <a name="_toc201009666"></a><a name="_toc201011404"></a>**Вывод**
В рамках курсового проекта был разработан Telegram-бот и мини-приложение для заучивания слов и определений с помощью флеш-карточек, ориентированный на студентов и изучающих иностранные языки. Проект решает проблему неудобства использования сторонних приложений, предлагая полноценный функционал прямо в Telegram. Система реализована в виде микросервисной архитектуры, включает backend на FastAPI, frontend на React, и использует PostgreSQL для хранения данных. Встроена интеграция с сервисом перевода, предусмотрена авторизация через Telegram ID, что обеспечивает переносимость и сохранность данных пользователя. Приложение поддерживает до 10,000 пользователей в сутки, включает unit и интеграционные тесты для backend и frontend, покрывающие ключевой функционал, и собрано с использованием Docker и shell-скрипта, что обеспечивает автоматизированную сборку и развёртывание. Проект эффективно обрабатывает типичную нагрузку за счёт оптимизированной базы данных, использования индексов и внедрения кэширования.
2

