-- FACEIT CS2 Bot Database Schema
-- Инициализация базы данных PostgreSQL

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблица пользователей бота
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    faceit_id VARCHAR(255) UNIQUE NOT NULL,
    nickname VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Индексы для быстрого поиска
    CONSTRAINT users_faceit_id_unique UNIQUE (faceit_id)
);

-- Индексы для таблицы users
CREATE INDEX idx_users_faceit_id ON users(faceit_id);
CREATE INDEX idx_users_nickname ON users(nickname);
CREATE INDEX idx_users_last_activity ON users(last_activity);

-- Таблица настроек пользователей
CREATE TABLE user_settings (
    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    notifications BOOLEAN DEFAULT true,
    language VARCHAR(5) DEFAULT 'ru',
    subscription_type VARCHAR(20) DEFAULT 'standard',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица истории матчей
CREATE TABLE match_history (
    match_id VARCHAR(255) PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    finished_at TIMESTAMP WITH TIME ZONE NOT NULL,
    result VARCHAR(10) NOT NULL CHECK (result IN ('win', 'loss')),
    
    -- Статистика игрока в матче
    kills INTEGER DEFAULT 0,
    deaths INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    adr FLOAT DEFAULT 0.0,
    hltv_rating FLOAT DEFAULT 0.0,
    headshots INTEGER DEFAULT 0,
    headshot_percentage FLOAT DEFAULT 0.0,
    
    -- Информация о матче
    map_name VARCHAR(100),
    score_team1 INTEGER DEFAULT 0,
    score_team2 INTEGER DEFAULT 0,
    rounds_played INTEGER DEFAULT 0,
    
    -- Метаданные
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT match_history_result_check CHECK (result IN ('win', 'loss'))
);

-- Индексы для таблицы match_history
CREATE INDEX idx_match_history_user_id ON match_history(user_id);
CREATE INDEX idx_match_history_finished_at ON match_history(finished_at);
CREATE INDEX idx_match_history_map_name ON match_history(map_name);
CREATE INDEX idx_match_history_user_finished ON match_history(user_id, finished_at DESC);

-- Таблица списков сравнения игроков
CREATE TABLE comparison_lists (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    player_faceit_id VARCHAR(255) NOT NULL,
    player_nickname VARCHAR(255) NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ограничение на уникальность (один игрок в списке пользователя)
    CONSTRAINT comparison_unique_user_player UNIQUE (user_id, player_faceit_id)
);

-- Индексы для таблицы comparison_lists
CREATE INDEX idx_comparison_lists_user_id ON comparison_lists(user_id);
CREATE INDEX idx_comparison_lists_added_at ON comparison_lists(added_at);

-- Таблица сессий пользователей (для анализа активности)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_end TIMESTAMP WITH TIME ZONE,
    matches_count INTEGER DEFAULT 0,
    
    -- Статистика сессии
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    total_kills INTEGER DEFAULT 0,
    total_deaths INTEGER DEFAULT 0,
    total_assists INTEGER DEFAULT 0,
    avg_adr FLOAT DEFAULT 0.0,
    avg_hltv_rating FLOAT DEFAULT 0.0
);

-- Индексы для таблицы user_sessions
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_start ON user_sessions(session_start);
CREATE INDEX idx_user_sessions_active ON user_sessions(user_id) WHERE session_end IS NULL;

-- Таблица кэша FACEIT данных (для уменьшения нагрузки на API)
CREATE TABLE faceit_cache (
    cache_key VARCHAR(500) PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Индексы для таблицы faceit_cache
CREATE INDEX idx_faceit_cache_expires ON faceit_cache(expires_at);
CREATE INDEX idx_faceit_cache_created ON faceit_cache(created_at);

-- Таблица для отслеживания матчей (для уведомлений)
CREATE TABLE tracked_matches (
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    last_match_id VARCHAR(255),
    last_check TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    PRIMARY KEY (user_id)
);

-- Функция для очистки просроченного кэша
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM faceit_cache WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Функция для обновления last_activity при любой активности пользователя
CREATE OR REPLACE FUNCTION update_user_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE users SET last_activity = NOW() WHERE user_id = NEW.user_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Триггеры для автоматического обновления last_activity
CREATE TRIGGER trigger_update_activity_match_history
    AFTER INSERT ON match_history
    FOR EACH ROW
    EXECUTE FUNCTION update_user_activity();

CREATE TRIGGER trigger_update_activity_sessions
    AFTER INSERT OR UPDATE ON user_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_user_activity();

-- Создание индекса для JSONB данных в кэше
CREATE INDEX idx_faceit_cache_data_gin ON faceit_cache USING GIN (data);

-- Вставка тестовых данных (можно удалить в продакшене)
-- INSERT INTO users (user_id, faceit_id, nickname) 
-- VALUES (12345, 'test-faceit-id', 'TestUser')
-- ON CONFLICT (user_id) DO NOTHING;

-- Комментарии к таблицам
COMMENT ON TABLE users IS 'Пользователи Telegram бота';
COMMENT ON TABLE user_settings IS 'Настройки пользователей';
COMMENT ON TABLE match_history IS 'История матчей пользователей';
COMMENT ON TABLE comparison_lists IS 'Списки игроков для сравнения';
COMMENT ON TABLE user_sessions IS 'Игровые сессии пользователей';
COMMENT ON TABLE faceit_cache IS 'Кэш данных FACEIT API';
COMMENT ON TABLE tracked_matches IS 'Отслеживание матчей для уведомлений';

-- Успешное создание схемы
SELECT 'Database schema initialized successfully!' as message;