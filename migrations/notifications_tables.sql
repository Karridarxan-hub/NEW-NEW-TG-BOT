-- FACEIT CS2 Bot - Notifications Tables Migration
-- Добавление таблиц для системы уведомлений о матчах

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

-- Индексы для таблицы match_notifications
CREATE INDEX IF NOT EXISTS idx_match_notifications_match_id ON match_notifications(match_id);
CREATE INDEX IF NOT EXISTS idx_match_notifications_user_id ON match_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_match_notifications_sent_at ON match_notifications(sent_at);

-- Индексы для таблицы notification_logs
CREATE INDEX IF NOT EXISTS idx_notification_logs_user_id ON notification_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_match_id ON notification_logs(match_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_status ON notification_logs(status);
CREATE INDEX IF NOT EXISTS idx_notification_logs_created_at ON notification_logs(created_at);

-- Функция для очистки старых уведомлений (для периодической очистки)
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

-- Комментарии к таблицам
COMMENT ON TABLE match_notifications IS 'Отслеживание отправленных уведомлений о завершенных матчах';
COMMENT ON COLUMN match_notifications.match_data IS 'JSON данные матча на момент отправки уведомления';

COMMENT ON TABLE notification_logs IS 'Логи системы уведомлений для отладки и мониторинга';
COMMENT ON COLUMN notification_logs.status IS 'Статус уведомления: sent, failed, skipped';

-- Успешное создание таблиц уведомлений
SELECT 'Notifications tables created successfully!' as message;