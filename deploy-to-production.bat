@echo off
REM 🚀 Деплой в продакшен через GitHub Actions
REM Продовый бот: 8200317917:AAE3wSxtG6N7wKeLJezgNaQsCd5uHMcXjVk

echo.
echo 🚀 Деплой в продакшен...
echo 🤖 Продовый бот: @faceitstatsme_bot
echo 🌐 ВПС: автоматический деплой через GitHub Actions
echo.

REM Проверка статуса git
echo 📋 Проверка изменений...
git status

echo.
set /p message="💬 Введите сообщение коммита: "

if "%message%"=="" (
    echo ❌ Сообщение коммита не может быть пустым
    pause
    exit /b 1
)

REM Добавление всех изменений
echo 📝 Добавление изменений...
git add .

REM Создание коммита
echo 💾 Создание коммита...
git commit -m "%message%"

if %errorlevel% neq 0 (
    echo ❌ Ошибка создания коммита
    pause
    exit /b 1
)

REM Push в продакшен
echo 🚀 Отправка в продакшен...
git push production master

if %errorlevel% == 0 (
    echo.
    echo ✅ Код успешно отправлен в продакшен!
    echo 🔄 GitHub Actions запустил автоматический деплой
    echo 📊 Отследить прогресс: https://github.com/Karridarxan-hub/NEW-NEW-TG-BOT/actions
    echo ⏳ Ожидайте ~4-5 минут для завершения деплоя
) else (
    echo ❌ Ошибка отправки в продакшен
)

echo.
pause