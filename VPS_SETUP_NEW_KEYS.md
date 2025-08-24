# 🔑 Настройка ВПС с новыми SSH ключами

## 📋 ШАГ 1: КОМАНДЫ ДЛЯ ВЫПОЛНЕНИЯ НА ВПС

### Вы уже зашли на ВПС, выполните эти команды по порядку:

#### 1. Создание пользователя для деплоя
```bash
# Создать пользователя faceit
sudo useradd -m -s /bin/bash faceit

# Добавить в группу sudo
sudo usermod -aG sudo faceit

# Создать директорию SSH
sudo mkdir -p /home/faceit/.ssh
sudo chmod 700 /home/faceit/.ssh

# Создать файл authorized_keys и добавить публичный ключ
sudo tee /home/faceit/.ssh/authorized_keys << 'EOF'
ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDDyU4BhFFbLwUFfsd9ydFPnt6NetsGgoKpHbs3wjBs4GdRAKstUAWYxlQYLeQh2Fpg0YrY2TJmVkFxkavFfupaVapguzKWPovirDO7Pw1B5Imzh/Ww8oU4411eRwSJsGf/NdHByhNnsy7AFBECkEpixYIHmbtM9Jz4MtZvkSpMboPGMSO2quiSsFqqW/J3cih/1oIQXT9yDnjrT805rniO4PmI95IhclPQbqhm3kh/gVcoHXr/BrlWVpE2lCIuxGJ31qNM/v7oBfF36PZbviLJ97xDJwFZDnQEd/9oZbdx5A+o2rusIKhZ9mjVdgJMgp/KuxsZBzgkb3pIK7kwxdgf
EOF

# Установить правильные права
sudo chown -R faceit:faceit /home/faceit/.ssh
sudo chmod 600 /home/faceit/.ssh/authorized_keys

# Настроить sudo без пароля для Docker команд
echo "faceit ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/local/bin/docker-compose, /bin/systemctl" | sudo tee /etc/sudoers.d/faceit
```

#### 2. Обновление системы и установка необходимых пакетов
```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить необходимые пакеты
sudo apt install -y curl git wget unzip software-properties-common python3-pip
```

#### 3. Установка Docker
```bash
# Удалить старые версии Docker (если есть)
sudo apt remove -y docker docker-engine docker.io containerd runc || true

# Установить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh

# Добавить пользователей в группу docker
sudo usermod -aG docker $USER
sudo usermod -aG docker faceit

# Запустить и включить Docker
sudo systemctl enable docker
sudo systemctl start docker
```

#### 4. Установка Docker Compose
```bash
# Установить через pip
sudo pip3 install docker-compose

# Проверить установку
docker-compose --version

# Если не работает через pip, альтернативная установка:
if ! command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep -Po '"tag_name": "\K.*?(?=")')
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi
```

#### 5. Создание директорий и клонирование репозитория
```bash
# Создать директории
sudo mkdir -p /opt/faceit-bot
sudo mkdir -p /opt/backups
sudo mkdir -p /var/log/faceit-cs2-bot

# Установить права на директории
sudo chown -R faceit:faceit /opt/faceit-bot
sudo chown -R faceit:faceit /opt/backups
sudo chmod 755 /opt/faceit-bot /opt/backups

# Переключиться на пользователя faceit и клонировать репозиторий
sudo -u faceit git clone https://github.com/Karridarxan-hub/NEW-NEW-TG-BOT.git /opt/faceit-bot

# Перейти в директорию проекта
cd /opt/faceit-bot

# Настроить Git для пользователя faceit
sudo -u faceit git config user.name "VPS Deploy"
sudo -u faceit git config user.email "deploy@vps"
```

#### 6. Настройка firewall (опционально)
```bash
# Установить и настроить UFW
sudo apt install -y ufw

# Базовые правила
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Разрешить SSH
sudo ufw allow ssh

# Разрешить HTTP/HTTPS (если планируется веб-интерфейс)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Разрешить порт для API бота
sudo ufw allow 8000/tcp

# Активировать firewall
sudo ufw --force enable
```

#### 7. Проверка установки
```bash
# Проверить Docker
docker --version
sudo systemctl status docker

# Проверить Docker Compose  
docker-compose --version

# Проверить права пользователя faceit
sudo -u faceit docker ps

# Проверить репозиторий
ls -la /opt/faceit-bot

# Проверить SSH ключи
sudo -u faceit ls -la /home/faceit/.ssh/
```

---

## 🔐 ШАГ 2: НАСТРОЙКА GITHUB SECRETS

### Перейдите в ваш GitHub репозиторий:
👉 https://github.com/Karridarxan-hub/NEW-NEW-TG-BOT/settings/secrets/actions

### Обновите/добавьте следующие secrets:

| Secret Name | Value | 
|-------------|-------|
| `VPS_HOST` | `IP_адрес_вашего_ВПС` |
| `VPS_USER` | `faceit` |
| `VPS_PORT` | `22` |
| `VPS_SSH_KEY` | `новый_приватный_ключ` |

### 🔑 Приватный ключ для GitHub (VPS_SSH_KEY):
```
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAw8lOAYRRWy8FBX7HfcnRT57ejXrbBoKCqR27N8IwbOBnUQCr
LVAFmMZUGC3kIdhaYNGK2NkyZlZBcZGrxX7qWlWqYLsylj6L4qwzuz8NQeSJs4f1
sPKFOONdXkcEibBn/zXRwcoTZ7MuwBQRApBKYsWCB5m7TPSc+DLWb5EqTG6DxjEj
tqrokrBaqlvyd3Iof9aCEF0/cg5460/NOa54juD5iPeSIXJT0G6oZt5If4FXKB16
/wa5VlaRNpQiLsRid9ajTP7+6AXxd+j2W74iyfe8QycBWQ50BHf/aGW3ceQPqNq7
rCCoWfZo1XYCTIKfyrsbGQc4JG96SCu5MMXYHwIDAQABAoIBAAzsDOt5tbrsdArk
TrtlJhz4sdyppqob1A7gaPpppTOSbg9BGYswlGX8dRFxefSn6HMqcV0VnMd3WvNp
d2peEY6rx8aBpHmZIDdyQSnTJAdc05/XUeZ/Yz6ZdxChZFHIJF0KStFdCoHWKDhC
OssuBdLWEVp6EYwnOvMAu/l6Hc4UgZuDLWZAl+4vdaZKJbCP7e6VptBh+6rMWw/z
w2BcStRPC8HGB+ktG+VpQ6ZJt3Z2TFd7/v4nqV7LHE0/qPYWx3sWbX2gdEIjDRpT
IRZ9iSL3At3RsiDVueqjbC4D8fzPG22SU/Cb1wsNCGKu/xmz0nj2nPR+BJPVHUxk
J67iXdkCgYEA791kevyKDmS+C/wARMwD3sDInBwZ0yj0AOm7zXZl7vwjzhKBfVOW
WbBb95QblmLBJ5KtsawnaGfRerJGmMl2KY9rn5x1zY/IXfoR1rBi652mksfWFWsz
FTlFF6NxNQvsJMUsQgWNn+n4yF2b0IK3f4sF7tq3uPYHqlV1wscW9RkCgYEA0PTb
KhPhkufR8YpbUxOHPAPKnLZHvY7Zq69hyqrjvGf8Z2WqY5DPVkYAGnamEMQyNxzr
EV8GhiQF9I23I1F+irU6tziDouI1oZ1A1NMAkV6OMM0Lns+IpVlWqccjNI5x0oZN
xJxgznGVjkGeBGl56lC/YwqdcBklqqHeSr9g5fcCgYAL0W+q85hlvybx9jeZLCgg
qIT51BSdp83l4Z5EMEozbS7ib1z77MtineLaHu0BCtqTdZGjSGUkqsDSd8gsrPhq
ccuOsKnJOAVaRADu///PthPH9ZqhsYdxy0GROZdRUsYOxbw5gIaK039Td/E+Y8Jg
wVvIefRFY7Ha/ZzwvNhvuQKBgQC4Io3fjpWBd3eyelHv642IfW7WmmqtyGxYtrxe
dCkrphbuptB33OxZAmak61l7/OijWIBtVmfRXX1B/IAeR3pTkVCklNCrgNvyBzlS
Un51m/WBW6+ZyxiHXSrZgfqsHbp/4oo1b/h+8+ju6zPsf2ZH7dA53ujOF9rxeqMB
C5TAEQKBgBm8QCN6o7fyIX8eMZGTkzn4H5c8ouKzTdXpPLeTQNYdGwQikCa7FtX2
nCHvaexuuOrL5IdLDTRM9YiRs41Fkl7gDndwWFSysym+cBOI+m0UUc41osBZ4atH
SO0765vqXD2zNIK18riHePpjAs96BMHCLoY+B4q3pPmb8CzaptVU
-----END RSA PRIVATE KEY-----
```

---

## 🧪 ШАГ 3: ТЕСТИРОВАНИЕ АВТОДЕПЛОЯ

### После выполнения всех команд на ВПС и настройки GitHub Secrets:

1. **Сделать тестовый коммит:**
```bash
# В локальной папке проекта
git add .
git commit -m "🧪 Тест автодеплоя с новыми SSH ключами"
git push origin master
```

2. **Отследить процесс:**
- Откройте: https://github.com/Karridarxan-hub/NEW-NEW-TG-BOT/actions
- Найдите запущенный workflow "🚀 Production Deploy"
- Следите за логами в реальном времени

3. **Проверить на ВПС:**
```bash
# Проверить статус контейнеров
cd /opt/faceit-bot
docker-compose ps

# Проверить логи бота
docker-compose logs -f faceit-bot

# Проверить API
curl http://localhost:8000/health
```

---

## ❗ TROUBLESHOOTING

### Если что-то пошло не так:

#### 1. Проверить SSH подключение:
```bash
# На вашем локальном компьютере (тест подключения)
ssh -i ~/.ssh/your_key faceit@ВАШ_IP_ВПС "echo 'SSH работает!'"
```

#### 2. Проверить Docker:
```bash
# На ВПС
sudo systemctl status docker
docker --version
sudo -u faceit docker ps
```

#### 3. Проверить права:
```bash
# На ВПС
ls -la /home/faceit/.ssh/
cat /home/faceit/.ssh/authorized_keys
```

#### 4. Проверить репозиторий:
```bash
# На ВПС
cd /opt/faceit-bot
sudo -u faceit git status
sudo -u faceit git pull origin master
```

---

## ✅ ГОТОВО!

После успешного выполнения всех команд:
- ✅ ВПС настроен для автоматического деплоя
- ✅ SSH ключи настроены 
- ✅ Docker и Docker Compose установлены
- ✅ Репозиторий склонирован
- ✅ GitHub Actions готов к работе

**Автодеплой будет работать при каждом `git push origin master`!** 🚀