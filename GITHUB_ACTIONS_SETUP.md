# 🚀 GitHub Actions Автодеплой - Инструкция по настройке

## 📋 Полная настройка автоматического деплоя через GitHub Actions

### ✅ ЧТО УЖЕ ГОТОВО:
- ✅ GitHub Actions workflow создан
- ✅ Скрипт настройки ВПС готов
- ✅ Ваш SSH ключ получен
- ✅ Продакшн репозиторий настроен

---

## 🔧 ШАГИ НАСТРОЙКИ

### 1. 🖥️ НАСТРОЙКА ВПС

#### Подключитесь к ВПС и запустите:

```bash
# Скачать скрипт настройки
curl -o setup-vps.sh https://raw.githubusercontent.com/Karridarxan-hub/NEW-NEW-TG-BOT/master/scripts/setup-vps.sh

# Сделать исполняемым
chmod +x setup-vps.sh

# Запустить настройку
sudo ./setup-vps.sh
```

**Что делает скрипт:**
- Устанавливает Docker и Docker Compose
- Создает пользователя `faceit` для деплоя
- Клонирует репозиторий в `/opt/faceit-bot`
- Настраивает SSH, firewall и логирование
- Создает systemd сервис

---

### 2. 🔑 СОЗДАНИЕ SSH КЛЮЧЕЙ

#### На вашем компьютере создайте НОВЫЙ SSH ключ для деплоя:

```bash
# Создать новый SSH ключ специально для деплоя
ssh-keygen -t rsa -b 4096 -f ~/.ssh/faceit_deploy -N ""

# Показать публичный ключ (для добавления на ВПС)
cat ~/.ssh/faceit_deploy.pub

# Показать приватный ключ (для GitHub Secrets)
cat ~/.ssh/faceit_deploy
```

#### Добавить публичный ключ на ВПС:

```bash
# На ВПС добавить публичный ключ
sudo -u faceit nano /home/faceit/.ssh/authorized_keys

# Вставить содержимое ~/.ssh/faceit_deploy.pub
# Сохранить и выйти (Ctrl+X, Y, Enter)

# Проверить права
sudo -u faceit chmod 600 /home/faceit/.ssh/authorized_keys
sudo -u faceit chmod 700 /home/faceit/.ssh
```

---

### 3. 🔐 НАСТРОЙКА GITHUB SECRETS

#### Перейдите в ваш репозиторий на GitHub:
👉 https://github.com/Karridarxan-hub/NEW-NEW-TG-BOT/settings/secrets/actions

#### Добавьте следующие secrets:

| Secret Name | Value | Описание |
|------------|-------|----------|
| `VPS_HOST` | `ваш_ip_адрес_впс` | IP адрес или домен ВПС |
| `VPS_USER` | `faceit` | Пользователь на ВПС |
| `VPS_PORT` | `22` | SSH порт (обычно 22) |
| `VPS_SSH_KEY` | `приватный_ключ` | Содержимое ~/.ssh/faceit_deploy |

#### 🔍 КАК ДОБАВИТЬ SECRETS:

1. **Откройте репозиторий** → Settings → Secrets and variables → Actions
2. **Нажмите "New repository secret"**
3. **Добавьте каждый secret:**

**VPS_HOST:**
```
# Ваш IP адрес ВПС
123.456.789.123
```

**VPS_USER:**
```
faceit
```

**VPS_PORT:**
```
22
```

**VPS_SSH_KEY:**
```
-----BEGIN RSA PRIVATE KEY-----
(содержимое приватного ключа ~/.ssh/faceit_deploy)
-----END RSA PRIVATE KEY-----
```

⚠️ **ВАЖНО**: Используйте НОВЫЙ ключ из файла `VPS_SETUP_NEW_KEYS.md`!

---

### 4. 🧪 ТЕСТИРОВАНИЕ АВТОДЕПЛОЯ

#### Создадим тестовый коммит:

```bash
# В локальной папке с проектом
git add .
git commit -m "🚀 Тест автоматического деплоя через GitHub Actions"
git push origin master
```

#### Отслеживание деплоя:

1. **Откройте GitHub** → Actions tab вашего репозитория
2. **Найдите запущенный workflow** "🚀 Production Deploy"
3. **Кликните на него** для просмотра логов в реальном времени

#### На ВПС можете также смотреть логи:

```bash
# Логи контейнеров
cd /opt/faceit-bot
docker-compose logs -f faceit-bot

# Статус сервисов
docker-compose ps

# Использование ресурсов
docker stats
```

---

### 5. 🔄 КАК РАБОТАЕТ АВТОДЕПЛОЙ

#### При каждом `git push origin master`:

1. **GitHub Actions запускается** автоматически
2. **Подключается к ВПС** по SSH
3. **Останавливает старые сервисы**
4. **Скачивает новый код** (`git pull`)
5. **Создает backup** текущей версии
6. **Пересобирает Docker образы**
7. **Запускает обновленные сервисы**
8. **Проверяет работоспособность**
9. **При ошибке - делает rollback**

#### Время деплоя: ~3-5 минут

---

## 📊 МОНИТОРИНГ И УПРАВЛЕНИЕ

### Полезные команды на ВПС:

```bash
# Статус сервисов
cd /opt/faceit-bot && docker-compose ps

# Логи в реальном времени
docker-compose logs -f faceit-bot

# Перезапуск бота (если нужно)
docker-compose restart faceit-bot

# Обновление вручную (если Actions не работает)
git pull origin master
./scripts/deploy.sh prod --rebuild

# Просмотр бэкапов
ls -la /opt/backups/

# Восстановление из бэкапа (если нужно)
cd /opt/faceit-bot
tar -xzf /opt/backups/backup_YYYYMMDD_HHMMSS.tar.gz
docker-compose up -d
```

### Логи GitHub Actions:

- 📁 **Все деплои**: https://github.com/Karridarxan-hub/NEW-NEW-TG-BOT/actions
- 📊 **Статус последнего**: Badge в README
- 📧 **Уведомления**: GitHub пришлет email при ошибках

---

## 🚨 TROUBLESHOOTING

### Частые проблемы:

#### 1. **"Permission denied (publickey)"**
```bash
# Проверить SSH ключ на ВПС
sudo -u faceit cat /home/faceit/.ssh/authorized_keys

# Проверить права
sudo -u faceit chmod 600 /home/faceit/.ssh/authorized_keys
sudo -u faceit chmod 700 /home/faceit/.ssh
```

#### 2. **"Docker not found"**
```bash
# Переустановить Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker faceit
```

#### 3. **"Port already in use"**
```bash
# Остановить старые контейнеры
cd /opt/faceit-bot
docker-compose down --remove-orphans
docker system prune -f
```

#### 4. **"Health check failed"**
```bash
# Проверить логи
docker-compose logs faceit-bot

# Проверить .env файл
cat .env

# Проверить токен бота
curl -s "https://api.telegram.org/bot${BOT_TOKEN}/getMe"
```

---

## ✅ ПРОВЕРКА ГОТОВНОСТИ

### Чек-лист перед тестированием:

- [ ] ВПС настроен скриптом `setup-vps.sh`
- [ ] SSH ключи созданы и добавлены
- [ ] GitHub Secrets настроены (4 штуки)
- [ ] Репозиторий имеет workflow файл
- [ ] Доступ к ВПС по SSH работает

### Тест готовности:

```bash
# Проверить SSH подключение
ssh -i ~/.ssh/faceit_deploy faceit@ваш_ip_впс "echo 'SSH работает!'"

# Проверить Docker на ВПС
ssh -i ~/.ssh/faceit_deploy faceit@ваш_ip_впс "docker --version"

# Проверить репозиторий на ВПС
ssh -i ~/.ssh/faceit_deploy faceit@ваш_ip_впс "cd /opt/faceit-bot && git status"
```

---

## 🎉 ГОТОВО!

После настройки деплой будет работать так:

```
📝 Коммит → 🔄 GitHub Actions → 🖥️ ВПС → 🤖 Обновленный бот!
```

**Контакты для помощи:**
- Telegram: @karriDD  
- Issues: https://github.com/Karridarxan-hub/NEW-NEW-TG-BOT/issues

**Версия инструкции:** v2.1.3 🚀