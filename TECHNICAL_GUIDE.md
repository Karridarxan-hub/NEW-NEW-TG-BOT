# 🔧 Техническое руководство FACEIT CS2 Бота

## 📋 Обзор

Данное техническое руководство содержит детальное описание всех модулей, алгоритмов и внутренних механизмов работы FACEIT CS2 бота. Предназначено для разработчиков, желающих понять внутреннюю архитектуру или внести изменения в код.

## 📁 Структура проекта

```
faceit-cs2-bot/
├── main.py                    # Точка входа приложения
├── config.py                  # Конфигурация и настройки
├── storage.py                 # Система хранения данных
├── faceit_client.py           # FACEIT API клиент
├── keyboards.py               # Telegram клавиатуры
├── bot_handlers.py            # Основные обработчики бота
├── match_handlers.py          # Обработчики матчей
├── history_handlers.py        # Обработчики истории
├── additional_handlers.py     # Дополнительные функции
├── test_bot.py               # Модульные тесты
├── requirements.txt          # Python зависимости
├── Dockerfile                # Docker образ
├── docker-compose.yml        # Docker Compose конфигурация
├── .env.example              # Пример переменных окружения
└── docs/                     # Документация
    ├── ARCHITECTURE.md
    ├── DEPLOYMENT.md
    ├── API.md
    └── TECHNICAL_GUIDE.md
```

## 🚀 main.py - Точка входа

### Описание
Главный модуль, который инициализирует и запускает все компоненты системы: FastAPI приложение, Telegram бота и фоновые задачи. В текущей версии все обработчики интегрированы в единый роутер для упрощения архитектуры.

### Архитектура (обновлено 2025-01-08)

**Текущая реализация**: Унифицированная архитектура с единым роутером
- Все обработчики (bot_handlers, additional_handlers, history_handlers, match_handlers) объединены в main.py
- Используется единый main_router для избежания конфликтов роутеров
- FSM состояния определены в классе BotStates

### Ключевые компоненты

```python
# Создаем единый роутер и импортируем все обработчики
from aiogram import Router, F
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Создаем единый роутер
main_router = Router()

# FSM состояния
class BotStates(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_custom_number = State()
    waiting_for_player_nickname = State()
    waiting_for_match_url = State()
    waiting_for_form_count = State()
    waiting_for_custom_count = State()
```

### Управление жизненным циклом

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запуск
    logger.info("🚀 Запуск бота...")
    
    # Запускаем фоновые задачи
    cleanup_task = asyncio.create_task(cleanup_storage_task())
    polling_task = asyncio.create_task(start_polling())
    
    yield
    
    # Завершение
    logger.info("🛑 Завершение работы...")
    cleanup_task.cancel()
    polling_task.cancel()
    
    # Закрываем соединения
    await faceit_client.close()
    await bot.session.close()
```

### Текущее состояние функций

✅ **Полностью работающие:**
- **start_polling()**: Запуск Telegram polling
- **health_check()**: Health check endpoint (порт 8000)
- **search_player()**: API поиск игрока
- **get_player_stats()**: API получение статистики  
- **faceit_webhook()**: Обработка FACEIT webhooks
- **start_command()**: Обработка /start с FSM
- **process_nickname()**: Обработка ввода никнейма
- **show_overall_stats()**: Показ общей статистики

🚧 **Заглушки (готовы к реализации):**
- **match_history**: История матчей
- **form_analysis**: Анализ формы
- **last_match**: Последний матч
- **player_comparison**: Сравнение игроков
- **current_match_analysis**: Анализ текущего матча
- **profile**: Управление профилем
- **settings**: Настройки бота
- **help**: Справка

### Docker конфигурация

**Dockerfile**: Переключен на main.py (CMD ["python", "main.py"])
**docker-compose.yml**: Восстановлены порты (8000:8000) и health checks

## ⚙️ config.py - Конфигурация

### Описание
Управление конфигурацией через Pydantic Settings с автоматической загрузкой переменных окружения.

```python
class Settings(BaseSettings):
    bot_token: str
    faceit_api_key: str
    webhook_url: Optional[str] = None
    debug: bool = False
    
    class Config:
        env_file = ".env"
```

### Переменные окружения
- `BOT_TOKEN` - Токен Telegram бота (обязательно)
- `FACEIT_API_KEY` - FACEIT API ключ (обязательно)
- `WEBHOOK_URL` - URL для webhook уведомлений
- `DEBUG` - Режим отладки

## 🗄️ storage.py - Система хранения

### Описание
In-memory хранилище данных с автоматической очисткой и кэшированием. Обеспечивает быстрый доступ к пользовательским данным и сессиям.

### Основные структуры данных

```python
class InMemoryStorage:
    def __init__(self):
        self.users: Dict[int, Dict[str, Any]] = {}
        self.sessions: Dict[int, Dict[str, Any]] = {}
        self.faceit_cache: Dict[str, tuple] = {}
        self.user_settings: Dict[int, Dict[str, Any]] = {}
        self.comparison_data: Dict[int, List[Dict[str, Any]]] = {}
        self.tracked_matches: Dict[int, str] = {}
```

### Ключевые методы

#### Управление пользователями
```python
def set_user_faceit_data(self, user_id: int, faceit_id: str, nickname: str):
    """Привязка FACEIT профиля к пользователю"""
    if user_id not in self.users:
        self.users[user_id] = {}
    
    self.users[user_id].update({
        'faceit_id': faceit_id,
        'nickname': nickname,
        'linked_at': datetime.now()
    })
```

#### Управление сессиями
```python
def get_session(self, user_id: int) -> Dict[str, Any]:
    """Получение сессии пользователя с автоинициализацией"""
    if user_id not in self.sessions:
        self.sessions[user_id] = {
            'start_time': datetime.now(),
            'matches': [],
            'stats': {}
        }
    return self.sessions[user_id]
```

#### Кэширование
```python
def get_cached_data(self, cache_key: str, max_age_minutes: int = 5):
    """Получение кэшированных данных с проверкой TTL"""
    if cache_key in self.faceit_cache:
        data, timestamp = self.faceit_cache[cache_key]
        if datetime.now() - timestamp < timedelta(minutes=max_age_minutes):
            return data
        else:
            del self.faceit_cache[cache_key]
    return None
```

## 🌐 faceit_client.py - FACEIT API клиент

### Описание
Асинхронный клиент для работы с FACEIT Data API с автоматическим кэшированием, rate limiting и error handling.

### Основные endpoints

```python
class FaceitAPIClient:
    BASE_URL = "https://open.faceit.com/data/v4"
    
    async def find_player_by_nickname(self, nickname: str):
        """Поиск игрока по никнейму"""
        return await self._make_request("/players", params={"nickname": nickname})
    
    async def get_player_stats(self, player_id: str, game: str = "cs2"):
        """Получение статистики игрока"""
        return await self._make_request(f"/players/{player_id}/stats/{game}")
```

### Rate Limiting
```python
async def _make_request(self, endpoint: str, params: Optional[Dict] = None):
    """HTTP запрос с обработкой rate limiting"""
    try:
        response = await session.get(f"{self.BASE_URL}{endpoint}", params=params)
        
        if response.status_code == 429:  # Rate limit
            await asyncio.sleep(60)  # Ждем минуту
            return await self._make_request(endpoint, params)
            
    except Exception as e:
        print(f"HTTP Request Error: {e}")
        return None
```

### Расчет HLTV 2.1 рейтинга

```python
def calculate_hltv_rating(self, stats: Dict[str, Any]) -> float:
    """
    Рассчитать HLTV 2.1 рейтинг по формуле:
    Rating = 0.0073×KAST + 0.3591×KPR - 0.5329×DPR + 0.2372×Impact + 0.0032×ADR + 0.1587
    """
    rounds_played = stats.get('Rounds', 1)
    kills = stats.get('Kills', 0)
    deaths = stats.get('Deaths', 1)
    assists = stats.get('Assists', 0)
    adr = stats.get('ADR', 0)
    kast = stats.get('KAST %', 0)
    
    # Расчет компонентов
    kpr = kills / rounds_played if rounds_played > 0 else 0
    dpr = deaths / rounds_played if rounds_played > 0 else 0
    impact = 2.13 * kpr + 0.42 * assists / rounds_played - 0.41 if rounds_played > 0 else 0
    
    # Формула HLTV 2.1
    rating = 0.0073 * kast + 0.3591 * kpr - 0.5329 * dpr + 0.2372 * impact + 0.0032 * adr + 0.1587
    
    return max(0, round(rating, 2))
```

## ⌨️ keyboards.py - UI клавиатуры

### Описание
Генерация inline клавиатур для Telegram бота с использованием Aiogram InlineKeyboardBuilder.

### Основные функции

```python
def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню бота"""
    builder = InlineKeyboardBuilder()
    
    builder.button(text="📊 Статистика игрока", callback_data="player_stats")
    builder.button(text="📝 История матчей", callback_data="match_history")
    # ... другие кнопки
    
    builder.adjust(2, 2, 2, 1, 1, 1)  # Расположение кнопок по строкам
    return builder.as_markup()
```

### Динамические клавиатуры
```python
def get_notifications_toggle_keyboard(enabled: bool) -> InlineKeyboardMarkup:
    """Переключатель уведомлений с текущим состоянием"""
    builder = InlineKeyboardBuilder()
    
    status_text = "✅ Включены" if enabled else "❌ Выключены"
    action = "disable" if enabled else "enable"
    
    builder.button(text=f"🔔 {status_text}", callback_data=f"toggle_notifications_{action}")
    return builder.as_markup()
```

## 🤖 bot_handlers.py - Основные обработчики

### Описание
Главные обработчики команд и callback'ов Telegram бота с использованием FSM для управления состоянием диалогов.

### States (Состояния диалога)
```python
class BotStates(StatesGroup):
    waiting_for_nickname = State()
    waiting_for_custom_number = State()
    waiting_for_player_nickname = State()
    waiting_for_match_url = State()
```

### Команда /start
```python
@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """Обработчик команды /start с проверкой существующего профиля"""
    user_id = message.from_user.id
    faceit_id = storage.get_user_faceit_id(user_id)
    
    if faceit_id:
        # Существующий пользователь
        user_data = storage.get_user(user_id)
        await message.answer(
            f"🎮 Добро пожаловать обратно, {user_data.get('nickname', 'Игрок')}!",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        # Новый пользователь
        await message.answer("🎮 Введите ваш никнейм на FACEIT:")
        await state.set_state(BotStates.waiting_for_nickname)
```

### Обработка статистики
```python
@router.callback_query(F.data == "stats_overall")
async def show_overall_stats(callback: CallbackQuery):
    """Показ общей статистики с форматированием"""
    user_id = callback.from_user.id
    faceit_id = storage.get_user_faceit_id(user_id)
    
    # Получение и форматирование данных
    player_data = await faceit_client.get_player_details(faceit_id)
    stats_data = await faceit_client.get_player_stats(faceit_id)
    formatted_stats = faceit_client.format_player_stats(player_data, stats_data)
    
    # Расчет до следующего уровня
    current_elo = formatted_stats['elo']
    current_level = formatted_stats['level']
    next_level_elo = [800, 950, 1100, 1250, 1400, 1550, 1700, 1850, 2000, 2000][min(current_level, 9)]
    elo_to_next = max(0, next_level_elo - current_elo) if current_level < 10 else 0
    
    # Форматирование ответа
    stats_text = f"""📊 **Общая статистика**
👤 **Игрок:** {formatted_stats['nickname']}
🏆 **Уровень:** {formatted_stats['level']}
⚡ **ELO:** {formatted_stats['elo']:,}
📈 **До следующего уровня:** {elo_to_next:,}
    """
```

## 🎮 match_handlers.py - Обработчики матчей

### Описание
Специализированные обработчики для работы с матчами, включая автоматические уведомления о завершении игр.

### Форматирование статистики матча
```python
def calculate_player_stats_from_match(player_stats: dict) -> dict:
    """Рассчет статистики игрока из данных матча"""
    stats = player_stats.get('stats', {})
    
    kills = int(stats.get('Kills', 0))
    deaths = int(stats.get('Deaths', 1))
    assists = int(stats.get('Assists', 0))
    rounds = int(stats.get('Rounds', 1))
    
    # Основные метрики
    kd_ratio = round(kills / max(deaths, 1), 2)
    adr = round(float(stats.get('ADR', 0)), 1)
    kast = round(float(stats.get('KAST %', 0)), 1)
    
    # Упрощенный расчет HLTV для матча
    kpr = kills / max(rounds, 1)
    dpr = deaths / max(rounds, 1)
    impact = 2.13 * kpr + 0.42 * (assists / max(rounds, 1)) - 0.41
    hltv_rating = 0.0073 * kast + 0.3591 * kpr - 0.5329 * dpr + 0.2372 * impact + 0.0032 * adr + 0.1587
    
    return {
        'kills': kills,
        'deaths': deaths,
        'assists': assists,
        'kd_ratio': kd_ratio,
        'adr': adr,
        'kast': kast,
        'hltv_rating': max(0, round(hltv_rating, 2))
    }
```

### Автоматические уведомления
```python
async def check_for_finished_matches():
    """Фоновая задача проверки завершенных матчей"""
    while True:
        try:
            await asyncio.sleep(120)  # Проверка каждые 2 минуты
            
            for user_id, tracked_match_id in storage.tracked_matches.items():
                user_settings = storage.get_user_settings(user_id)
                if not user_settings.get('match_notifications', True):
                    continue
                
                match_details = await faceit_client.get_match_details(tracked_match_id)
                
                if match_details and match_details.get('status') == 'finished':
                    # Отправляем уведомление
                    await send_match_notification(bot, user_id, match_details, match_stats)
                    del storage.tracked_matches[user_id]
                    
        except Exception as e:
            print(f"Error checking finished matches: {e}")
```

## 📊 additional_handlers.py - Дополнительные функции

### Анализ формы
```python
async def process_form_analysis_request(callback, faceit_id: str, match_count: int):
    """Анализ формы игрока с разделением на периоды"""
    matches_data = await faceit_client.get_player_matches(faceit_id, limit=match_count)
    processed_matches = []
    
    # Обработка матчей
    for match in matches_data['items']:
        processed_match = await process_single_match(match_details, match_stats, faceit_id)
        if processed_match:
            processed_matches.append(processed_match)
    
    # Деление на два периода для сравнения
    mid_point = len(processed_matches) // 2
    recent_matches = processed_matches[:mid_point]
    older_matches = processed_matches[mid_point:]
    
    # Расчет статистики для каждого периода
    recent_stats = calculate_period_stats(recent_matches)
    older_stats = calculate_period_stats(older_matches)
    
    # Формирование анализа тренда
    trend_analysis = analyze_trend(recent_stats, older_stats)
```

### Сравнение игроков
```python
def calculate_period_stats(matches: list) -> dict:
    """Расчет статистики за период матчей"""
    if not matches:
        return {}
    
    total_matches = len(matches)
    wins = sum(1 for match in matches if match['won'])
    
    return {
        'total': total_matches,
        'wins': wins,
        'winrate': round((wins / total_matches) * 100, 1),
        'avg_kills': sum(match['stats']['kills'] for match in matches) / total_matches,
        'avg_deaths': sum(match['stats']['deaths'] for match in matches) / total_matches,
        'avg_kd': round(sum(match['stats']['kd_ratio'] for match in matches) / total_matches, 2),
        'avg_adr': round(sum(match['stats']['adr'] for match in matches) / total_matches, 1),
        'avg_hltv': round(sum(match['stats']['hltv_rating'] for match in matches) / total_matches, 2)
    }
```

### Анализ команд матча
```python
async def analyze_match_teams(match_details: dict) -> str:
    """Анализ силы команд в матче"""
    teams = match_details.get('teams', {})
    analysis_text = f"🔍 **Анализ матча**\n\n"
    
    for team_num, team in enumerate([teams.get('faction1', {}), teams.get('faction2', {})], 1):
        players = team.get('roster', [])
        team_stats = []
        
        # Получение статистики каждого игрока
        for player in players:
            player_id = player.get('player_id')
            if player_id:
                player_data = await faceit_client.get_player_details(player_id)
                stats_data = await faceit_client.get_player_stats(player_id)
                formatted_stats = faceit_client.format_player_stats(player_data, stats_data)
                team_stats.append(formatted_stats)
        
        if team_stats:
            # Расчет средних показателей команды
            avg_level = sum(p['level'] for p in team_stats) / len(team_stats)
            avg_elo = sum(p['elo'] for p in team_stats) / len(team_stats)
            avg_hltv = sum(p['hltv_rating'] for p in team_stats) / len(team_stats)
            
            # Поиск лучшего и худшего игрока
            best_player = max(team_stats, key=lambda p: p['hltv_rating'])
            worst_player = min(team_stats, key=lambda p: p['hltv_rating'])
    
    return analysis_text
```

## 🧪 test_bot.py - Модульные тесты

### Структура тестов
```python
class TestFaceitClient:
    """Тесты для FACEIT API клиента"""
    
    @pytest.mark.asyncio
    async def test_calculate_hltv_rating(self, faceit_client):
        stats = {
            'Rounds': 26, 'Kills': 20, 'Deaths': 15,
            'Assists': 5, 'ADR': 85.5, 'KAST %': 75.0
        }
        rating = faceit_client.calculate_hltv_rating(stats)
        assert isinstance(rating, float)
        assert 0 <= rating <= 3.0

class TestStorage:
    """Тесты системы хранения"""
    
    def test_user_management(self, storage):
        user_id = 12345
        storage.set_user_faceit_data(user_id, "test-id", "TestPlayer")
        assert storage.get_user_faceit_id(user_id) == "test-id"
```

### Mocking внешних API
```python
@pytest.mark.asyncio
async def test_process_nickname_success(self, mock_message, mock_state):
    mock_player_data = {
        'player_id': 'test-id',
        'nickname': 'TestPlayer',
        'games': {'cs2': {'skill_level': 5, 'faceit_elo': 1200}}
    }
    
    with patch('bot_handlers.faceit_client') as mock_client:
        mock_client.find_player_by_nickname.return_value = mock_player_data
        await process_nickname(mock_message, mock_state)
        mock_storage.set_user_faceit_data.assert_called_once()
```

## 🔧 Алгоритмы и вычисления

### ELO до следующего уровня
```python
def calculate_elo_to_next_level(current_level: int, current_elo: int) -> int:
    """Расчет ELO до следующего уровня"""
    level_thresholds = [800, 950, 1100, 1250, 1400, 1550, 1700, 1850, 2000, 2000]
    
    if current_level >= 10:
        return 0  # Максимальный уровень
    
    next_level_elo = level_thresholds[current_level]
    return max(0, next_level_elo - current_elo)
```

### Анализ тренда формы
```python
def analyze_trend(recent: dict, older: dict) -> str:
    """Анализ тренда улучшения/ухудшения формы"""
    improvements = 0
    total_metrics = 0
    
    metrics = [
        (recent['winrate'] - older['winrate'], True),
        (recent['avg_kd'] - older['avg_kd'], True),
        (recent['avg_adr'] - older['avg_adr'], True),
        (recent['avg_hltv'] - older['avg_hltv'], True)
    ]
    
    for diff, positive_is_good in metrics:
        total_metrics += 1
        if (positive_is_good and diff > 0):
            improvements += 1
    
    improvement_rate = improvements / total_metrics
    
    if improvement_rate >= 0.75:
        return "🔥 Отличная форма! Значительное улучшение"
    elif improvement_rate >= 0.5:
        return "📈 Улучшение формы"
    elif improvement_rate >= 0.25:
        return "🔄 Смешанные результаты"
    else:
        return "📉 Снижение формы"
```

## 🚀 Оптимизации производительности

### 1. Кэширование запросов
- **Player Details**: 5 минут TTL
- **Player Stats**: 5 минут TTL  
- **Match Details**: 1 час TTL
- **Match Stats**: 1 час TTL

### 2. Batch processing
```python
async def get_multiple_players_stats(player_ids: List[str]) -> List[dict]:
    """Получение статистики нескольких игроков параллельно"""
    tasks = [faceit_client.get_player_stats(pid) for pid in player_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

### 3. Memory management
```python
async def cleanup_storage_task():
    """Периодическая очистка устаревших данных"""
    while True:
        await asyncio.sleep(3600)  # Каждый час
        storage.cleanup_old_cache()
        
        # Очистка старых сессий
        cutoff_time = datetime.now() - timedelta(hours=12)
        for user_id, session in list(storage.sessions.items()):
            if session['start_time'] < cutoff_time:
                del storage.sessions[user_id]
```

## 🔒 Безопасность

### Input validation
```python
def validate_nickname(nickname: str) -> bool:
    """Валидация никнейма"""
    if not isinstance(nickname, str):
        return False
    if len(nickname) < 2 or len(nickname) > 32:
        return False
    if not re.match(r'^[a-zA-Z0-9_-]+$', nickname):
        return False
    return True
```

### Rate limiting
```python
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    async def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        user_requests = self.requests[user_id]
        
        # Удаляем старые запросы
        user_requests[:] = [req_time for req_time in user_requests 
                           if now - req_time < self.window_seconds]
        
        if len(user_requests) < self.max_requests:
            user_requests.append(now)
            return True
        
        return False
```

## 📊 Логирование и мониторинг

### Structured logging
```python
import structlog

logger = structlog.get_logger()

async def log_api_request(endpoint: str, user_id: int, duration: float):
    """Логирование API запросов"""
    logger.info(
        "api_request",
        endpoint=endpoint,
        user_id=user_id,
        duration_ms=duration * 1000,
        timestamp=datetime.utcnow().isoformat()
    )
```

### Metrics collection
```python
from prometheus_client import Counter, Histogram, Gauge

# Метрики Prometheus
REQUEST_COUNT = Counter('faceit_bot_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('faceit_bot_request_duration_seconds', 'Request duration')
ACTIVE_USERS = Gauge('faceit_bot_active_users', 'Number of active users')
```

## 📋 История изменений и текущее состояние (2025-01-08)

### 🔄 Последние изменения

#### v1.1.0 - Унификация архитектуры (2025-01-08)
- ✅ **Переход с test_main.py на main.py**: Полная интеграция всех функций
- ✅ **Исправление конфликтов роутеров**: Создан единый main_router
- ✅ **Восстановление Docker конфигурации**: Порты 8000:8000 и health checks
- ✅ **Интеграция FSM состояний**: Все состояния диалога объединены в BotStates
- ✅ **Рабочая статистика**: Функция "📊 Статистика игрока" полностью работает

### 🚀 Текущий статус развертывания

**Контейнеры Docker:**
```bash
faceit_cs2_bot   newprojectbot-faceit-bot   Up (healthy)   0.0.0.0:8000->8000/tcp
faceit_redis     redis:7-alpine             Up (healthy)   0.0.0.0:6379->6379/tcp
```

**Настройки окружения:**
- BOT_TOKEN: 8282817400:AAGmpBXkc4oYYOjZJx9l6WvAES9uAg5xy_g
- FACEIT_API_KEY: 41f48f43-609c-4639-b821-360b039f18b4
- DEBUG: false (production mode)

**Сетевая конфигурация:**
- Подсеть Docker: 172.22.0.0/16
- FastAPI порт: 8000
- Redis порт: 6379

### 🎯 Текущие возможности бота

#### ✅ Полностью реализовано:
1. **Регистрация пользователей**
   - Команда /start
   - Поиск FACEIT профиля по никнейму
   - Привязка профиля к Telegram аккаунту
   - FSM управление состояниями диалога

2. **Основная статистика**
   - Получение данных с FACEIT API
   - Расчет HLTV 2.1 рейтинга
   - Форматирование статистики (ELO, K/D, ADR, etc.)
   - Отображение уровня и прогресса

3. **Графическое меню**
   - Главное меню с 9 функциями
   - Inline клавиатуры для навигации
   - Кнопки возврата и навигации
   - Эмодзи и визуальное оформление

4. **API endpoints**
   - Health check (/health)
   - Поиск игрока (/api/player/search/{nickname})
   - Статистика игрока (/api/player/{player_id}/stats)
   - Статистика бота (/api/stats)
   - Webhook FACEIT (/webhook/faceit)

#### 🚧 Заготовки под реализацию:

**Готовые модули (требуют интеграции):**
- `additional_handlers.py` - Анализ формы и сравнение игроков
- `history_handlers.py` - История матчей с детальной статистикой
- `match_handlers.py` - Последний матч и уведомления

**Функции с заглушками:**
- 📝 История матчей
- 📈 Анализ формы  
- 🎮 Последний матч
- ⚔️ Сравнение игроков
- 🔍 Анализ текущего матча
- 👤 Профиль
- ⚙️ Настройки
- ❓ Помощь

### 🔧 Решенные технические проблемы

#### 1. Конфликт роутеров Aiogram
**Проблема**: `RuntimeError: Router is already attached`
**Решение**: Создание единого main_router в main.py вместо импорта множественных роутеров

#### 2. Docker кэширование
**Проблема**: Контейнер не обновлялся после изменений кода
**Решение**: Принудительная пересборка с `--no-cache --pull`

#### 3. Несовместимость зависимостей
**Проблема**: Конфликт aiogram 3.15.0 и pydantic 2.10.3
**Решение**: Изменение requirements.txt на `pydantic>=2.4.1,<2.10`

#### 4. Сетевые конфликты Docker
**Проблема**: Pool overlaps с существующими сетями
**Решение**: Смена подсети на 172.22.0.0/16

### 📊 Производительность и мониторинг

**Health checks активны:**
```bash
# Bot health check
GET http://localhost:8000/health
Response: {"status": "healthy", "bot_status": "running"}

# Redis health check  
redis-cli ping
Response: PONG
```

**Логирование:**
- Структурированные логи в формате timestamp - module - level - message
- Отслеживание API запросов и ошибок
- Мониторинг состояния polling

### 🎯 Roadmap развития

#### Краткосрочные цели:
1. **Интеграция готовых обработчиков** - Восстановление функций из модульных файлов
2. **Реализация истории матчей** - Полный функционал просмотра матчей
3. **Настройки пользователей** - Уведомления, язык, предпочтения

#### Среднесрочные цели:
1. **Система уведомлений** - Автоматические уведомления о матчах
2. **Анализ формы игрока** - Тренды и статистика за периоды
3. **Сравнение игроков** - Детальное сравнение статистики

#### Долгосрочные цели:
1. **ML анализ** - Предсказание результатов матчей
2. **Интеграция с другими платформами** - Steam, ESL, etc.
3. **Веб-интерфейс** - Dashboard для расширенной аналитики

---

*Техническое руководство обновлено: 2025-01-08*  
*Версия: 1.1.0*  
*Статус: Production Ready (базовый функционал)*