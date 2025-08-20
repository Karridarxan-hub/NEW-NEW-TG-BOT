-- FACEIT CS2 Bot - Complete Essential Tables Migration
-- Полная миграция всех необходимых таблиц

-- Таблица пользователей (основная)
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    faceit_id VARCHAR(255) UNIQUE NOT NULL,
    nickname VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Индексы
    CONSTRAINT idx_users_faceit_id UNIQUE (faceit_id)
);

-- Таблица настроек пользователей
CREATE TABLE IF NOT EXISTS user_settings (
    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    language VARCHAR(10) DEFAULT 'ru',
    subscription_type VARCHAR(20) DEFAULT 'standard', -- 'standard', 'premium'
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица для кэширования данных
CREATE TABLE IF NOT EXISTS cache_data (
    cache_key VARCHAR(500) PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Таблица для отслеживания отправленных уведомлений о матчах
CREATE TABLE IF NOT EXISTS match_notifications (
    id SERIAL PRIMARY KEY,
    match_id VARCHAR(255) NOT NULL,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    match_data JSONB,
    
    -- Уникальность: одно уведомление на матч для каждого пользователя
    CONSTRAINT unique_match_notification UNIQUE (match_id, user_id)
);

-- Таблица для логирования уведомлений (для отладки и статистики)
CREATE TABLE IF NOT EXISTS notification_logs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    match_id VARCHAR(255),
    status VARCHAR(50) NOT NULL, -- 'sent', 'failed', 'skipped'
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Таблица для хранения данных сравнения игроков (FSM состояния)
CREATE TABLE IF NOT EXISTS user_comparison_data (
    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    player1_data JSONB,
    player2_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ИНДЕКСЫ для оптимизации

-- Индексы для users
CREATE INDEX IF NOT EXISTS idx_users_nickname ON users(nickname);
CREATE INDEX IF NOT EXISTS idx_users_last_activity ON users(last_activity);

-- Индексы для user_settings  
CREATE INDEX IF NOT EXISTS idx_user_settings_notifications ON user_settings(notifications_enabled);
CREATE INDEX IF NOT EXISTS idx_user_settings_subscription ON user_settings(subscription_type);

-- Индексы для cache_data
CREATE INDEX IF NOT EXISTS idx_cache_data_expires_at ON cache_data(expires_at);
CREATE INDEX IF NOT EXISTS idx_cache_data_created_at ON cache_data(created_at);

-- Индексы для match_notifications
CREATE INDEX IF NOT EXISTS idx_match_notifications_match_id ON match_notifications(match_id);
CREATE INDEX IF NOT EXISTS idx_match_notifications_user_id ON match_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_match_notifications_sent_at ON match_notifications(sent_at);

-- Индексы для notification_logs
CREATE INDEX IF NOT EXISTS idx_notification_logs_user_id ON notification_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_match_id ON notification_logs(match_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_status ON notification_logs(status);
CREATE INDEX IF NOT EXISTS idx_notification_logs_created_at ON notification_logs(created_at);

-- Индексы для user_comparison_data
CREATE INDEX IF NOT EXISTS idx_user_comparison_data_updated_at ON user_comparison_data(updated_at);

-- ФУНКЦИИ для обслуживания БД

-- Функция для очистки истекшего кэша
CREATE OR REPLACE FUNCTION clean_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM cache_data WHERE expires_at < NOW();
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Функция для очистки старых уведомлений
CREATE OR REPLACE FUNCTION clean_old_notifications(days INTEGER DEFAULT 30)
RETURNS INTEGER AS $$
DECLARE
    deleted_notifications INTEGER;
    deleted_logs INTEGER;
BEGIN
    -- Удаляем старые записи уведомлений
    DELETE FROM match_notifications WHERE sent_at < NOW() - INTERVAL '1 day' * days;
    GET DIAGNOSTICS deleted_notifications = ROW_COUNT;
    
    -- Удаляем старые логи
    DELETE FROM notification_logs WHERE created_at < NOW() - INTERVAL '1 day' * days;
    GET DIAGNOSTICS deleted_logs = ROW_COUNT;
    
    RETURN deleted_notifications + deleted_logs;
END;
$$ LANGUAGE plpgsql;

-- Функция для обновления последней активности пользователя
CREATE OR REPLACE FUNCTION update_user_activity(p_user_id BIGINT)
RETURNS VOID AS $$
BEGIN
    UPDATE users SET last_activity = NOW() WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- КОММЕНТАРИИ к таблицам
COMMENT ON TABLE users IS 'Основная таблица пользователей бота с FACEIT привязкой';
COMMENT ON COLUMN users.faceit_id IS 'Уникальный ID игрока в FACEIT';
COMMENT ON COLUMN users.nickname IS 'Никнейм игрока в FACEIT';

COMMENT ON TABLE user_settings IS 'Настройки и предпочтения пользователей';
COMMENT ON COLUMN user_settings.notifications_enabled IS 'Включены ли уведомления о матчах';
COMMENT ON COLUMN user_settings.subscription_type IS 'Тип подписки: standard или premium';

COMMENT ON TABLE cache_data IS 'Кэш данных FACEIT API для ускорения работы';
COMMENT ON TABLE match_notifications IS 'Отслеживание отправленных уведомлений о завершенных матчах';
COMMENT ON TABLE notification_logs IS 'Логи системы уведомлений для отладки и мониторинга';
COMMENT ON TABLE user_comparison_data IS 'Временные данные для сравнения игроков';

-- Триггер для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Применяем триггер к таблицам
CREATE TRIGGER update_user_settings_updated_at 
    BEFORE UPDATE ON user_settings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_comparison_data_updated_at 
    BEFORE UPDATE ON user_comparison_data 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Успешное создание всех таблиц
SELECT 'All essential tables created successfully!' as message;