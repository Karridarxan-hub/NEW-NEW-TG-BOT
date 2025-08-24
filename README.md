# FACEIT CS2 Telegram Bot

A comprehensive Telegram bot for CS2 players to track their FACEIT statistics, compare performance, analyze matches, and monitor game progress with real-time notifications.

[![Version](https://img.shields.io/badge/version-2.1.1-blue.svg)](https://github.com/your-repo/faceit-cs2-bot)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![FACEIT API](https://img.shields.io/badge/FACEIT-API%20v4-orange.svg)](https://developers.faceit.com/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://docker.com)

## 🎯 Overview

This bot provides CS2 players with comprehensive FACEIT statistics tracking, including detailed match analysis, player comparisons, form analysis, and automated match notifications. Built with modern async Python using aiogram 3.x, FastAPI, PostgreSQL, and Redis.

## ✨ Key Features

### 📊 Player Statistics
- **Detailed FACEIT Profile**: ELO, level, K/D ratio, win rate, ADR, headshot percentage
- **HLTV 2.1 Rating**: Advanced performance calculation
- **Career Statistics**: Total matches, wins/losses, recent performance trends
- **Profile Management**: Link/change FACEIT accounts, view linked profile

### 🆚 Player Comparison
- **Head-to-Head Analysis**: Compare any two FACEIT players
- **15+ Performance Metrics**: Comprehensive comparison across all key statistics
- **Visual Indicators**: Emoji-based performance comparison (📈📉➡️)
- **Smart Categorization**: Grouped metrics (Core Performance, Damage & Efficiency, Career)

### 📈 Match Analysis
- **Last Match Details**: Complete statistics from most recent game
- **Match History**: Browse through recent matches with detailed stats
- **Form Analysis**: Performance trends over recent games
- **Map-Specific Stats**: Performance breakdown by map

### 🔔 Live Notifications
- **Auto Match Detection**: Automatic monitoring of finished matches
- **Real-time Updates**: Get notified when your matches complete
- **Detailed Match Results**: Win/loss, stats, HLTV rating, opponent info
- **Customizable Settings**: Enable/disable notifications per user

### 🎮 Advanced Features
- **Current Match Status**: Monitor ongoing matches (in development)
- **Form Analysis**: Performance trends and consistency tracking
- **Interactive Keyboards**: User-friendly button-based navigation
- **Multi-language Support**: Russian and English interfaces

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (recommended)
- Telegram Bot Token (from @BotFather)
- FACEIT API Key (from [FACEIT Developers](https://developers.faceit.com/))

### Option 1: Docker Deployment (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd faceit-cs2-bot
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start the bot**
   ```bash
   docker-compose up -d
   ```

4. **Verify deployment**
   ```bash
   # Check container status
   docker-compose ps
   
   # View logs
   docker-compose logs -f faceit-bot
   
   # Health check
   curl http://localhost:8080/health
   ```

### Option 2: Manual Installation

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up databases**
   ```bash
   # PostgreSQL
   createdb faceit_bot
   psql faceit_bot < migrations/init.sql
   
   # Redis
   redis-server
   ```

3. **Configure environment**
   ```bash
   export BOT_TOKEN="your_bot_token"
   export FACEIT_API_KEY="your_faceit_api_key"
   export DATABASE_URL="postgresql://user:password@localhost/faceit_bot"
   export REDIS_URL="redis://localhost:6379/0"
   ```

4. **Run the bot**
   ```bash
   python main.py
   ```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `BOT_TOKEN` | ✅ | Telegram Bot API token | - |
| `FACEIT_API_KEY` | ✅ | FACEIT Data API key | - |
| `DATABASE_URL` | ✅ | PostgreSQL connection string | - |
| `REDIS_URL` | ✅ | Redis connection string | - |
| `DEBUG` | ❌ | Enable debug mode | `false` |
| `WEBHOOK_URL` | ❌ | Webhook URL for production | - |
| `CACHE_TTL` | ❌ | Cache time-to-live (seconds) | `300` |

### Getting API Keys

#### Telegram Bot Token
1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow instructions
3. Copy the provided token to `BOT_TOKEN`

#### FACEIT API Key
1. Visit [FACEIT Developers](https://developers.faceit.com/)
2. Create an account or sign in
3. Create a new application
4. Generate a Server-side API key
5. Copy the key to `FACEIT_API_KEY`

## 📱 Bot Usage

### Getting Started
1. Start the bot: `/start`
2. Enter your FACEIT nickname when prompted
3. Use the button menu to navigate features

### Main Commands

| Command | Description |
|---------|-------------|
| `/start` | Initialize bot and link FACEIT profile |
| **📊 Статистика** | View your detailed FACEIT statistics |
| **🆚 Сравнение** | Compare two players' performance |
| **📈 История матчей** | Browse match history with filters |
| **🔍 Последний матч** | View your most recent match details |
| **📋 Анализ формы** | Analyze performance trends |
| **👤 Профиль** | Manage your linked FACEIT account |
| **⚙️ Настройки** | Configure bot preferences |

### Player Comparison Workflow
1. Select **🆚 Сравнение**
2. Choose **➕ Добавить себя** or **👤 Добавить игрока**
3. Add second player using **👤 Добавить игрока**
4. Click **📊 Сравнить!** to see detailed comparison
5. Use **🗑️ Очистить** to reset and start over

## 🏗️ Architecture

### Technology Stack
- **Backend**: Python 3.11, aiogram 3.x, FastAPI
- **Databases**: PostgreSQL (primary), Redis (caching)
- **API**: FACEIT Data API v4
- **Deployment**: Docker, Docker Compose
- **Monitoring**: Health checks, logging, metrics

### Project Structure
```
faceit-cs2-bot/
├── bot/
│   ├── handlers/          # Telegram command handlers
│   └── services/          # Business logic services
├── migrations/            # Database schema
├── nginx/                 # Reverse proxy config
├── scripts/              # Deployment scripts
├── main.py               # Application entry point
├── faceit_client.py      # FACEIT API client
├── storage.py            # Database abstraction
├── keyboards.py          # Telegram keyboards
└── config.py             # Configuration management
```

### Key Components

#### Handler System
- **main_handler.py**: Core navigation and user flow
- **stats_handler.py**: Player statistics display
- **comparison_handler.py**: Player comparison with FSM
- **match_handler.py**: Match analysis and history
- **profile_handler.py**: Account management
- **notifications_handler.py**: Match notification system

#### API Integration
- **FaceitAPIClient**: Async HTTP client with rate limiting
- **Caching Layer**: Redis-backed response caching
- **Error Handling**: Comprehensive retry and fallback logic

#### Data Storage
- **PostgreSQL**: User profiles, match history, settings
- **Redis**: API response caching, session storage
- **Migration System**: Versioned database schemas

## 🔔 Notification System

The bot includes an advanced match monitoring system:

### Features
- **Automatic Detection**: Monitors FACEIT for completed matches
- **Real-time Notifications**: Instant alerts when matches finish
- **Detailed Results**: Complete match statistics and performance
- **User Preferences**: Enable/disable notifications per user
- **Webhook Support**: FACEIT webhook integration for instant updates

### Notification Flow
1. **Match Monitoring**: Background task checks for new matches every 5 minutes
2. **Match Detection**: Identifies completed matches for registered users
3. **Data Enrichment**: Fetches detailed match statistics and results
4. **Smart Notifications**: Sends formatted results with performance analysis
5. **History Storage**: Automatically saves matches to user history

## 📊 API Endpoints

The bot includes a FastAPI web server with REST endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API information and status |
| `/health` | GET | System health check |
| `/api/player/search/{nickname}` | GET | Search player by nickname |
| `/api/player/{player_id}/stats` | GET | Get player statistics |
| `/api/stats` | GET | Bot usage statistics |
| `/webhook/faceit` | POST | FACEIT webhook receiver |

## 🐳 Docker Deployment

### Production Setup

1. **Production Configuration**
   ```bash
   # Use production compose file
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Scaling**
   ```bash
   # Scale bot instances
   docker-compose up -d --scale faceit-bot=3
   ```

3. **Monitoring**
   ```bash
   # Container stats
   docker stats faceit_cs2_bot
   
   # Application health
   curl http://localhost:8080/health
   ```

### Development Setup

```bash
# Development environment with hot reload
docker-compose -f docker-compose.dev.yml up
```

## 🔍 Monitoring & Maintenance

### Health Checks
- **Container Health**: Docker health checks every 30 seconds
- **API Health**: `/health` endpoint with service status
- **Database Health**: Connection and query validation
- **FACEIT API**: External API availability checking

### Logging
- **Structured Logging**: JSON format with severity levels
- **Log Rotation**: Automatic cleanup of old log files
- **Sensitive Data**: Automatic masking of API keys and tokens
- **Performance Metrics**: Response times and error rates

### Backup & Recovery
```bash
# Database backup
docker exec faceit_postgres pg_dump -U faceit_user faceit_bot > backup.sql

# Redis backup  
docker exec faceit_redis redis-cli SAVE
```

## 🛠️ Development

### Local Development

1. **Setup development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Run tests**
   ```bash
   pytest
   pytest --cov=. --cov-report=html
   ```

3. **Code quality**
   ```bash
   flake8 .
   black .
   mypy .
   ```

### Contributing Guidelines

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite
5. Submit a pull request

## 📋 Version History

### v2.1.1 (Latest)
- ✅ Enhanced player comparison with 15+ metrics
- ✅ Improved UI with emoji indicators
- ✅ Fixed profile management and display
- ✅ Added current match analysis placeholder

### v2.1.0
- ✅ Complete player comparison system overhaul
- ✅ FSM-based conversation flow
- ✅ Reply keyboard interface improvements
- ✅ Enhanced error handling and user feedback

### v2.0.0
- ✅ Major architecture refactoring
- ✅ Async/await throughout codebase
- ✅ Docker containerization
- ✅ PostgreSQL + Redis integration
- ✅ Real-time match notifications

## 🚧 Roadmap

### Planned Features
- **Advanced Analytics**: Historical performance trends and predictions
- **Team Statistics**: Support for team-based analysis
- **Tournament Tracking**: Monitor ongoing tournaments and events
- **Custom Alerts**: User-defined notification triggers
- **Web Dashboard**: Browser-based statistics interface

### Technical Improvements  
- **GraphQL API**: More flexible data querying
- **Microservices**: Split into smaller, focused services
- **ML Integration**: Performance prediction and analysis
- **Multi-language**: Support for additional languages

## 🆘 Troubleshooting

### Common Issues

#### Bot Not Responding
```bash
# Check container status
docker-compose ps

# View recent logs
docker-compose logs --tail 50 faceit-bot

# Restart the bot
docker-compose restart faceit-bot
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready -U faceit_user

# Reset database
docker-compose down -v
docker-compose up -d
```

#### API Rate Limiting
- **Symptoms**: Slow responses, timeout errors
- **Solution**: The bot includes automatic rate limiting and retry logic
- **Monitoring**: Check logs for "rate limit" messages

### Getting Help

1. **Check the logs**: `docker-compose logs faceit-bot`
2. **Verify configuration**: Ensure all required environment variables are set
3. **Test API keys**: Use the health endpoint to verify API connectivity
4. **Create an issue**: Include logs and configuration details (remove sensitive data)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [FACEIT](https://faceit.com) for providing the CS2 statistics API
- [aiogram](https://github.com/aiogram/aiogram) for the excellent Telegram Bot framework
- [FastAPI](https://fastapi.tiangolo.com/) for the modern web framework
- The CS2 community for feedback and feature requests

---

**Built with ❤️ for the CS2 community**

For questions, feature requests, or bug reports, please create an issue in the repository.