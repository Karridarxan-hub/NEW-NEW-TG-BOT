-- FACEIT CS2 Bot - Essential Tables Migration
-- Создание только критически необходимых таблиц для работы кэша

-- Создание расширений (если не существуют)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Таблица кэша FACEIT данных (для уменьшения нагрузки на API)
CREATE TABLE IF NOT EXISTS faceit_cache (
    cache_key VARCHAR(500) PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Индексы для таблицы faceit_cache (если не существуют)
CREATE INDEX IF NOT EXISTS idx_faceit_cache_expires ON faceit_cache(expires_at);
CREATE INDEX IF NOT EXISTS idx_faceit_cache_created ON faceit_cache(created_at);
CREATE INDEX IF NOT EXISTS idx_faceit_cache_data_gin ON faceit_cache USING GIN (data);

-- Функция для очистки просроченного кэша
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS void AS $$
BEGIN
    DELETE FROM faceit_cache WHERE expires_at < NOW();
END;
$$ LANGUAGE plpgsql;

-- Таблица для списков сравнения игроков (хранится в Redis, но нужна для связей)
CREATE TABLE IF NOT EXISTS comparison_lists (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    player_faceit_id VARCHAR(255) NOT NULL,
    player_nickname VARCHAR(255) NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ограничение на уникальность (один игрок в списке пользователя)
    CONSTRAINT comparison_unique_user_player UNIQUE (user_id, player_faceit_id)
);

-- Индексы для таблицы comparison_lists
CREATE INDEX IF NOT EXISTS idx_comparison_lists_user_id ON comparison_lists(user_id);
CREATE INDEX IF NOT EXISTS idx_comparison_lists_added_at ON comparison_lists(added_at);

-- Комментарии к таблицам
COMMENT ON TABLE faceit_cache IS 'Кэш данных FACEIT API с TTL механизмом';
COMMENT ON TABLE comparison_lists IS 'Списки игроков для сравнения (минимальная поддержка)';

-- Успешное создание таблиц
SELECT 'Essential tables created successfully!' as message;