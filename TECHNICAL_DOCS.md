# FACEIT CS2 Bot - Technical Documentation

## Overview

The FACEIT CS2 Bot is a comprehensive Telegram bot designed to provide CS2 players with detailed statistics, match analysis, and performance insights from the FACEIT platform. The bot integrates with the FACEIT Data API v4 to retrieve player statistics, match history, and real-time match information.

**Version:** 2.1.0  
**Architecture:** Microservices with FastAPI + aiogram  
**Databases:** PostgreSQL + Redis  
**API Integration:** FACEIT Data API v4

---

## System Architecture

### Core Components

1. **Main Application (main.py)**
   - FastAPI application with Telegram bot integration
   - Webhook support for FACEIT match notifications
   - Health monitoring and API endpoints
   - Background task management

2. **Handler System (bot/handlers/)**
   - Modular handler architecture using aiogram routers
   - FSM (Finite State Machine) for user interactions
   - Reply and inline keyboard support
   - Error handling and logging

3. **Data Storage Layer**
   - PostgreSQL for persistent data
   - Redis for caching and session management
   - Dual-storage approach for performance optimization

4. **FACEIT API Client (faceit_client.py)**
   - Comprehensive API wrapper with rate limiting
   - Advanced statistics calculation (HLTV 2.1 rating)
   - Caching and error handling
   - Data validation and normalization

---

## Handler System Documentation

### Main Handler (main_handler.py)
**Purpose:** Core bot functionality and user onboarding  
**FSM States:** `MainStates.waiting_for_nickname`

#### Key Features:
- User registration and FACEIT profile linking
- Navigation between bot sections
- Reply keyboard integration
- Profile management

#### Endpoints:
- `/start` - Initial user registration
- Reply handlers for all main menu buttons
- Unknown message handling

### Statistics Handler (stats_handler.py)
**Purpose:** Player statistics display and analysis

#### Features:
- Overall player statistics
- Map-specific statistics
- Session analysis with match grouping
- Advanced metrics calculation

### Match History Handler (new_match_history_handler.py)
**Purpose:** Match history visualization and analysis

#### Features:
- Configurable match count (5, 10, 30, custom)
- Detailed match information
- Win/loss tracking
- Performance trends

### Last Match Handler (last_match_handler.py)
**Purpose:** Latest match details and statistics

#### Features:
- Real-time last match data
- Detailed player performance
- Match result analysis
- HLTV 2.1 rating calculation

### Comparison Handler (comparison_handler.py)
**Purpose:** Player comparison functionality  
**FSM States:** `ComparisonStates.waiting_for_nickname`

#### Features:
- Add up to 2 players for comparison
- Side-by-side statistics
- Enhanced comparison metrics
- Clear visual formatting

### Form Analysis Handler (form_analysis_handler.py)
**Purpose:** Performance trend analysis over time

#### Features:
- Configurable analysis periods (10, 20, 50 matches)
- Performance trends visualization
- Statistical improvements tracking
- Form rating system

### Current Match Handler (current_match_handler.py)
**Purpose:** Live match analysis and team comparison  
**FSM States:** `CurrentMatchStates.waiting_for_match_input`

#### Features:
- Live match detection
- Team composition analysis
- Map analysis and predictions
- Real-time updates

### Profile Handler (profile_handler.py)
**Purpose:** User profile management  
**FSM States:** `ProfileStates.waiting_for_new_nickname`

#### Features:
- Profile information display
- FACEIT account linking/changing
- User settings management

### Settings Handler (settings_handler.py)
**Purpose:** Bot configuration and preferences

#### Features:
- Notification preferences
- Subscription management
- Language settings (future)
- Privacy controls

### Help Handler (help_handler.py)
**Purpose:** User assistance and documentation

#### Features:
- Function descriptions
- HLTV 2.1 rating explanation
- Contact information
- Usage guides

---

## Database Schema

### Core Tables

#### users
```sql
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    faceit_id VARCHAR(255) UNIQUE NOT NULL,
    nickname VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### user_settings
```sql
CREATE TABLE user_settings (
    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    notifications_enabled BOOLEAN DEFAULT TRUE,
    language VARCHAR(10) DEFAULT 'ru',
    subscription_type VARCHAR(20) DEFAULT 'standard',
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### cache_data
```sql
CREATE TABLE cache_data (
    cache_key VARCHAR(500) PRIMARY KEY,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);
```

#### match_notifications
```sql
CREATE TABLE match_notifications (
    id SERIAL PRIMARY KEY,
    match_id VARCHAR(255) NOT NULL,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    match_data JSONB,
    CONSTRAINT unique_match_notification UNIQUE (match_id, user_id)
);
```

#### notification_logs
```sql
CREATE TABLE notification_logs (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    match_id VARCHAR(255),
    status VARCHAR(50) NOT NULL, -- 'sent', 'failed', 'skipped'
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### user_comparison_data
```sql
CREATE TABLE user_comparison_data (
    user_id BIGINT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    player1_data JSONB,
    player2_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Database Functions

#### clean_expired_cache()
Automatically removes expired cache entries from PostgreSQL.

#### clean_old_notifications(days INTEGER)
Removes notification records older than specified days.

#### update_user_activity(p_user_id BIGINT)
Updates user's last activity timestamp.

---

## API Integration Details

### FACEIT Data API v4

**Base URL:** `https://open.faceit.com/data/v4`  
**Authentication:** Bearer token in Authorization header

#### Core Endpoints Used:

1. **Player Search**
   - `GET /search/players?nickname={nickname}&game=cs2`
   - Rate limit: 1 req/sec
   - Cache TTL: 1 hour

2. **Player Details**
   - `GET /players/{player_id}`
   - Rate limit: 1 req/sec
   - Cache TTL: 6 hours

3. **Player Statistics**
   - `GET /players/{player_id}/stats/cs2`
   - Rate limit: 1 req/sec
   - Cache TTL: 30 minutes

4. **Player History**
   - `GET /players/{player_id}/history?game=cs2&limit={limit}`
   - Rate limit: 1 req/sec
   - Cache TTL: 10 minutes

5. **Match Details**
   - `GET /matches/{match_id}`
   - Rate limit: 1 req/sec
   - Cache TTL: No expiration (immutable)

6. **Match Statistics**
   - `GET /matches/{match_id}/stats`
   - Rate limit: 1 req/sec
   - Cache TTL: 10 minutes

#### Rate Limiting Strategy:
- Base delay: 1 second between requests
- Exponential backoff on 429 errors
- Maximum retry attempts: 3
- Timeout handling: 30 seconds

#### Error Handling:
- 404: Resource not found (handled gracefully)
- 401: Invalid API key (logged and returned as error)
- 429: Rate limited (exponential backoff)
- 5xx: Server errors (retry with backoff)

---

## State Management (FSM)

### Finite State Machine Implementation

The bot uses aiogram's FSM for managing user interactions across multiple message exchanges.

#### State Groups:

1. **MainStates**
   - `waiting_for_nickname`: User registration flow

2. **ComparisonStates**
   - `waiting_for_nickname`: Adding players to comparison

3. **ProfileStates**
   - `waiting_for_new_nickname`: Profile change flow

4. **CurrentMatchStates**
   - `waiting_for_match_input`: Match URL/ID input

5. **FormAnalysisStates**
   - `waiting_for_custom_period`: Custom analysis period

#### State Storage:
- In-memory storage using aiogram's MemoryStorage
- Session data persisted in FSM context
- Automatic cleanup on completion

#### State Data Structure:
```python
{
    'comparison_players': [
        {
            'nickname': str,
            'skill_level': int,
            'faceit_elo': int,
            'profile_data': dict
        }
    ],
    'current_match_data': dict,
    'analysis_period': int
}
```

---

## Caching Strategy

### Two-Layer Caching System

#### Layer 1: Redis (Fast Access)
- **TTL Settings:**
  - Player profiles: 5 minutes
  - Player statistics: 5 minutes
  - Match details: 30 minutes
  - Match statistics: 30 minutes
  - Player matches: 3 minutes

#### Layer 2: PostgreSQL (Persistent)
- Long-term cache storage
- Backup when Redis is unavailable
- Automatic promotion to Redis on access

### Cache Service (cache_service.py)

#### Key Methods:
- `get_player_profile(nickname)`: Cached player data retrieval
- `set_player_profile(nickname, data)`: Profile caching
- `invalidate_player_cache(nickname)`: Cache invalidation
- `get_cache_stats()`: Cache usage statistics

#### Cache Key Patterns:
- `player_profile:{nickname}`: Full player profile
- `player_stats:{player_id}`: Player statistics
- `match_details:{match_id}`: Match information
- `player_matches:{player_id}:{limit}`: Match history

### Cache Invalidation:
- Manual invalidation on profile changes
- Automatic TTL expiration
- Background cleanup tasks

---

## Error Handling

### Logging Strategy

#### Log Levels:
- **ERROR**: Critical failures, API errors
- **WARNING**: Rate limits, missing data
- **INFO**: Successful operations, user actions
- **DEBUG**: Cache hits, detailed flow information

#### Sensitive Data Masking:
```python
def mask_sensitive_data(data: str, show_chars: int = 4) -> str:
    """Masks sensitive data in logs"""
    if len(data) <= show_chars * 2:
        return "*" * len(data)
    return data[:show_chars] + "*" * (len(data) - show_chars * 2) + data[-show_chars:]
```

### Error Recovery Mechanisms

#### API Failures:
- Retry with exponential backoff
- Fallback to cached data
- Graceful degradation with limited functionality

#### Database Failures:
- Connection retry logic (5 attempts, 5-second intervals)
- Redis fallback for PostgreSQL failures
- In-memory fallback for complete storage failure

#### User-Facing Errors:
- Friendly error messages
- Automatic retry suggestions
- Fallback to basic functionality

#### Background Task Resilience:
- Task restart on failure
- Error isolation (one task failure doesn't affect others)
- Graceful degradation with reduced functionality

---

## Code Architecture

### Module Organization

```
├── main.py                     # Application entry point
├── config.py                   # Configuration management
├── storage.py                  # Storage abstraction layer
├── faceit_client.py           # FACEIT API client
├── keyboards.py               # Telegram keyboard definitions
├── bot/
│   ├── handlers/              # Message handlers
│   │   ├── __init__.py
│   │   ├── main_handler.py
│   │   ├── stats_handler.py
│   │   ├── match_handler.py
│   │   ├── comparison_handler.py
│   │   ├── profile_handler.py
│   │   ├── settings_handler.py
│   │   ├── help_handler.py
│   │   └── ...
│   └── services/              # Business logic services
│       ├── database_storage.py
│       ├── cache_service.py
│       └── redis_client.py
├── migrations/                # Database migrations
└── scripts/                   # Deployment scripts
```

### Design Patterns

#### Router Pattern:
- Each handler is a separate aiogram Router
- Modular registration in main application
- Priority-based routing for FSM states

#### Repository Pattern:
- DatabaseStorage class abstracts data access
- Unified interface for PostgreSQL and Redis
- Async/await throughout for performance

#### Service Layer Pattern:
- Business logic separated from handlers
- CacheService for caching operations
- FaceitAPIClient for external API interaction

#### Factory Pattern:
- Keyboard builders for dynamic UI generation
- Configuration-based keyboard creation
- Reusable keyboard components

### Data Flow Architecture

1. **User Request → Handler**
   - Message routing via aiogram
   - FSM state validation
   - Input validation and sanitization

2. **Handler → Service Layer**
   - Business logic execution
   - Data transformation
   - Error handling

3. **Service → Storage/API**
   - Cache check (Redis)
   - Database query (PostgreSQL)
   - External API call (FACEIT)

4. **Response Assembly**
   - Data formatting
   - Message construction
   - Keyboard generation

5. **User Response**
   - Message delivery
   - State updates
   - Cache updates

---

## Configuration Options

### Environment Variables

#### Required Settings:
```python
class Settings(BaseSettings):
    bot_token: str                    # Telegram Bot Token
    faceit_api_key: str              # FACEIT API Key
    database_url: Optional[str]       # PostgreSQL connection string
    redis_url: Optional[str]         # Redis connection string
```

#### Optional Settings:
```python
    webhook_url: Optional[str] = None        # Webhook URL for FACEIT notifications
    debug: bool = False                      # Debug mode flag
    faceit_webhook_secret: Optional[str]     # Webhook signature verification
```

### Database Configuration

#### PostgreSQL Connection:
```
DATABASE_URL=postgresql://user:password@host:port/database
```

#### Redis Connection:
```
REDIS_URL=redis://host:port/db
```

### Cache TTL Configuration

```python
cache_ttl = {
    'user_cache': 300,      # 5 minutes
    'match_cache': 3600,    # 1 hour  
    'session_cache': 1800,  # 30 minutes
    'faceit_cache': 300     # 5 minutes
}
```

### API Rate Limiting

```python
rate_limit_delay = 1.0              # Base delay between requests
max_retries = 3                     # Maximum retry attempts
timeout = 30.0                      # Request timeout in seconds
```

### Background Task Settings

```python
cleanup_interval = 1800             # Cache cleanup every 30 minutes
match_monitor_interval = 300        # Match monitoring every 5 minutes
notification_retention_days = 30    # Keep notifications for 30 days
```

---

## Performance Characteristics

### Response Time Targets

- **Cached Requests:** < 200ms
- **Database Queries:** < 500ms
- **FACEIT API Calls:** < 2s (including rate limiting)
- **Complex Analysis:** < 10s (form analysis, comparisons)

### Throughput Capabilities

- **Concurrent Users:** 100+ simultaneously
- **API Requests:** 60 per minute (FACEIT rate limit)
- **Database Connections:** 20 connection pool
- **Redis Operations:** 1000+ ops/second

### Memory Usage

- **Base Application:** ~50MB
- **Redis Cache:** ~100MB (typical usage)
- **Per User Session:** ~1KB
- **Background Tasks:** ~10MB

### Bottlenecks and Optimizations

#### Identified Bottlenecks:
1. **FACEIT API Rate Limits:** 1 request/second
2. **Complex Statistics Calculation:** CPU intensive
3. **Large Match History Requests:** Memory intensive
4. **Database Query Complexity:** I/O bound

#### Optimization Strategies:
1. **Aggressive Caching:** Two-layer cache system
2. **Batch Processing:** Group similar requests
3. **Lazy Loading:** Load data on demand
4. **Database Indexing:** Optimized query performance
5. **Connection Pooling:** Efficient resource utilization

---

## Security Model

### Authentication & Authorization

#### Telegram Integration:
- Bot token authentication
- User ID verification
- Session management via FSM

#### FACEIT API Security:
- Bearer token authentication
- Request signing for webhooks
- Rate limit compliance

### Data Protection

#### Personal Data Handling:
- Minimal data collection (User ID, FACEIT nickname)
- No storage of sensitive personal information
- Automatic data cleanup policies

#### Data Encryption:
- TLS for all external communications
- Database connection encryption
- Redis AUTH when configured

#### Input Validation:
- Nickname length and character validation
- Match ID format validation
- SQL injection prevention via parameterized queries
- XSS prevention in message formatting

### Privacy Considerations

#### Data Retention:
- User data kept until account deletion
- Cache data expires automatically
- Notification logs cleaned after 30 days

#### Data Access:
- Users can only access their own data
- No cross-user data sharing
- Admin access logged and monitored

#### Compliance:
- GDPR-ready data handling
- Right to deletion support
- Data export capabilities

---

## Deployment Architecture

### Production Environment

#### Application Stack:
- **Web Server:** uvicorn with FastAPI
- **Bot Framework:** aiogram 3.x
- **Database:** PostgreSQL 13+
- **Cache:** Redis 6+
- **Reverse Proxy:** nginx

#### Infrastructure:
- **Containerization:** Docker with multi-stage builds
- **Orchestration:** Docker Compose
- **Monitoring:** Health check endpoints
- **Logging:** Structured JSON logging

### Docker Configuration

#### Main Application:
```dockerfile
FROM python:3.11-slim
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Environment Files:
- `.env.prod` - Production configuration
- `.env.dev` - Development configuration
- `.env.example` - Configuration template

### Health Monitoring

#### Health Check Endpoint:
```
GET /health
```

#### Response Format:
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z",
    "services": {
        "bot": "active",
        "api": "active", 
        "storage": "active",
        "postgres": "active",
        "redis": "active",
        "faceit_api": "ok"
    },
    "metrics": {
        "total_users": 1000,
        "total_matches": 5000,
        "cache_entries": 500
    }
}
```

### Deployment Scripts

#### Quick Start:
```bash
./quick-start.sh  # Development setup
./scripts/deploy.sh  # Production deployment
```

#### Backup Strategy:
```bash
./scripts/backup.sh  # Database backup
```

---

## API Documentation

### Internal API Endpoints

#### Health & Monitoring

**GET /** - API Information
```json
{
    "message": "FACEIT CS2 Bot API",
    "version": "2.1.0",
    "status": "active",
    "endpoints": {...}
}
```

**GET /health** - System Health Check
- Returns system status and metrics
- Includes database and external service status

#### Player Data

**GET /api/player/search/{nickname}** - Search Player
```json
{
    "player_id": "uuid",
    "nickname": "PlayerName",
    "avatar": "url",
    "country": "RU",
    "games": {...}
}
```

**GET /api/player/{player_id}/stats** - Player Statistics
```json
{
    "player_id": "uuid",
    "stats": {...},
    "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Bot Statistics

**GET /api/stats** - Bot Usage Statistics
```json
{
    "total_users": 1000,
    "uptime": "2024-01-01T12:00:00Z",
    "version": "2.1.0"
}
```

#### Webhook Integration

**POST /webhook/faceit** - FACEIT Match Notifications
- Receives match completion notifications
- Triggers user notifications
- Validates webhook signatures

---

## Troubleshooting Guide

### Common Issues

#### Bot Not Responding
1. Check bot token validity
2. Verify webhook configuration
3. Check database connectivity
4. Review error logs

#### FACEIT API Errors
1. Verify API key is valid
2. Check rate limit compliance
3. Monitor API endpoint status
4. Review network connectivity

#### Database Connection Issues
1. Verify connection string format
2. Check database server availability
3. Validate credentials
4. Review connection pool settings

#### Cache Performance
1. Monitor Redis memory usage
2. Check cache hit rates
3. Review TTL settings
4. Analyze cache key patterns

### Debugging Tools

#### Log Analysis:
```bash
# View application logs
docker logs faceit-bot

# Follow real-time logs
docker logs -f faceit-bot

# Filter specific log levels
docker logs faceit-bot 2>&1 | grep ERROR
```

#### Database Inspection:
```sql
-- Check user count
SELECT COUNT(*) FROM users;

-- Review cache statistics
SELECT COUNT(*) FROM cache_data WHERE expires_at > NOW();

-- Monitor notification logs
SELECT status, COUNT(*) FROM notification_logs GROUP BY status;
```

#### Redis Commands:
```bash
# Check Redis status
redis-cli ping

# Monitor cache usage
redis-cli info memory

# List cached keys
redis-cli keys "player_*"
```

---

## Development Guide

### Setting Up Development Environment

1. **Clone Repository:**
   ```bash
   git clone <repository-url>
   cd faceit-cs2-bot
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Database Setup:**
   ```bash
   # Run migrations
   psql -f migrations/essential_tables_complete.sql
   ```

5. **Start Development Server:**
   ```bash
   python main.py
   ```

### Code Style Guidelines

#### Python Style:
- Follow PEP 8
- Use type hints
- Document functions with docstrings
- Async/await for I/O operations

#### Database Queries:
- Use parameterized queries
- Handle exceptions gracefully
- Log query performance issues

#### Error Handling:
- Catch specific exceptions
- Log errors with context
- Provide user-friendly messages

### Testing Strategy

#### Unit Tests:
- Handler function testing
- API client testing
- Database operation testing

#### Integration Tests:
- End-to-end user flows
- Database integration
- API integration

#### Performance Tests:
- Load testing with concurrent users
- Database query performance
- Cache effectiveness

---

## Future Enhancements

### Planned Features

1. **Enhanced Analytics:**
   - Advanced performance metrics
   - Trend analysis and predictions
   - Comparative analysis with professional players

2. **Real-time Features:**
   - Live match tracking
   - Real-time notifications
   - Match prediction algorithms

3. **Social Features:**
   - Team comparison
   - Friend systems
   - Leaderboards

4. **Premium Features:**
   - Advanced statistics
   - Custom analysis periods
   - Priority support

### Technical Improvements

1. **Performance Optimization:**
   - Database query optimization
   - More aggressive caching
   - CDN integration for static content

2. **Scalability Enhancements:**
   - Horizontal scaling support
   - Load balancing
   - Database sharding

3. **Monitoring & Observability:**
   - Application metrics (Prometheus)
   - Distributed tracing
   - Advanced alerting

4. **Security Enhancements:**
   - Rate limiting per user
   - Advanced input validation
   - Audit logging

---

## Conclusion

The FACEIT CS2 Bot represents a comprehensive solution for CS2 players seeking detailed performance analytics and match insights. The modular architecture, robust caching strategy, and comprehensive error handling ensure reliable operation while maintaining excellent user experience.

The system is designed for scalability and maintainability, with clear separation of concerns and extensive documentation to support ongoing development and enhancement.

For technical support or contributions, please refer to the repository documentation and contribution guidelines.