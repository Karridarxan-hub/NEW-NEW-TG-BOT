# FACEIT CS2 Bot - User Guide

Welcome to the comprehensive user guide for the **FACEIT CS2 Statistics Bot**! This bot helps Counter-Strike 2 players analyze their FACEIT performance with detailed statistics, match history, and powerful comparison tools.

---

## 🚀 Getting Started

### First Launch
1. **Start the bot**: Send `/start` command to the bot
2. **Link your FACEIT account**: Enter your FACEIT nickname when prompted
3. **Verification**: The bot will search for your profile and confirm it exists
4. **Welcome screen**: Once linked, you'll see the main menu with navigation options

### Requirements
- **FACEIT Account**: Must have an active FACEIT profile with CS2 matches
- **Correct Nickname**: Enter your exact FACEIT display name (case-sensitive)
- **Match History**: At least a few matches to display meaningful statistics

---

## 🎮 Bot Commands & Navigation

### Main Command
- `/start` - Initialize bot, link FACEIT account, or return to main menu

### Interface Types
The bot offers **two navigation methods**:
1. **Inline Buttons** - Click buttons directly in messages
2. **Reply Keyboard** - Use buttons at the bottom of your screen

### Main Menu Options
- **📊 Статистика** - Player statistics and performance metrics
- **📝 История** - Match history and detailed game logs
- **📈 Форма** - Form analysis comparing different time periods
- **🎮 Последний матч** - Latest match details and performance
- **⚔️ Сравнение** - Compare statistics between players
- **🔍 Анализ матча** - Current match analysis and predictions
- **👤 Профиль** - Account settings and profile management
- **❓ Помощь** - Help system and feature explanations

---

## 👤 Profile Management

### Linking Your FACEIT Account
1. Use `/start` command
2. Enter your **exact FACEIT nickname**
3. Bot validates the profile exists
4. Account is linked automatically

### Changing Your Profile
1. Go to **👤 Профиль** → **🔄 Сменить профиль**
2. Enter new FACEIT nickname
3. Bot validates and updates your linked account
4. All future statistics will use the new profile

### Profile Information Displayed
- **FACEIT Nickname** and profile link
- **Current ELO** and skill level
- **Region** and verification status
- **Registration date** with the bot
- **Notification settings** status
- **Subscription type** (Standard/Premium)

---

## 📊 Statistics Features

### General Statistics (📊 Общая статистика)
Displays comprehensive gameplay metrics:

**Core Performance:**
- **ELO Rating** and current skill level (1-10)
- **HLTV 2.1 Rating** - Professional-grade performance metric
- **ELO to next level** - Points needed for advancement
- **Win Rate** - Percentage of matches won

**Combat Statistics:**
- **K/D Ratio** - Kill to death ratio
- **ADR** (Average Damage per Round)
- **Average Kills/Deaths/Assists** per match
- **Headshot Percentage** - Accuracy metric
- **Total Matches Played** and wins

**Advanced Metrics:**
- **Multi-kill rounds** (3K, 4K, Ace statistics)
- **Clutch statistics** (1v1, 1v2 success rates)
- **Entry fragging** success percentage
- **Utility damage** (grenades, molotovs)
- **Flash assists** per match

### Map Statistics (🗺️ По картам)
Detailed performance breakdown by map:
- **Individual map performance** (Mirage, Inferno, Dust2, etc.)
- **Matches played** and win rate per map
- **K/D ratio** and ADR for each map
- **KAST percentage** and HLTV rating per map
- **Maps ranked** by performance and matches played

### Session Statistics (⏰ За сессию)
Groups matches by gaming sessions:
- **Session detection** - Automatically groups matches within 10-hour windows
- **Per-session metrics** - ADR, K/D, win rate for each session
- **Session duration** and match count
- **Performance trends** over multiple sessions
- **Color-coded indicators** - Green for good performance, red for poor

---

## 📝 Match History

### Viewing Match History
Choose from predefined options or enter custom amount:
- **5 матчей** - Quick overview of recent games
- **10 матчей** - Standard history view
- **30 матчей** - Extended performance analysis
- **✏️ Ввести вручную** - Custom number (1-100 matches)

### Match Details Included
For each match you'll see:
- **Date and time** of completion
- **Map name** and final score
- **Win/Loss result** with visual indicators
- **Personal statistics**:
  - Kills, Deaths, Assists (K/D/A)
  - ADR and total damage dealt
  - HLTV 2.1 rating for the match
  - KAST percentage
  - Headshot percentage
- **ELO change** (+/- points gained/lost)
- **Match duration** and rounds played

### Match History Features
- **Chronological ordering** - Most recent matches first
- **Performance indicators** - 🏆 for wins, ❌ for losses
- **Statistical averages** calculated across the period
- **Trend analysis** - Shows improving/declining performance

---

## 📈 Form Analysis

Form analysis compares your recent performance to previous periods to identify trends and improvement areas.

### Analysis Options
- **📊 Анализ 10 матчей** - Last 10 vs previous 10 matches
- **📈 Анализ 20 матчей** - Last 20 vs previous 20 matches  
- **📋 Анализ 50 матчей** - Last 50 vs previous 50 matches
- **✏️ Свой период** - Custom period (5-100 matches per period)

### Metrics Compared
The analysis compares these key performance indicators:

**Combat Performance:**
- **K/D Ratio** - Killing efficiency trends
- **ADR** - Damage output consistency
- **HLTV Rating** - Overall performance metric
- **Headshot %** - Aiming precision development

**Match Results:**
- **Win Rate** - Success rate comparison
- **Match Count** - Games played in each period
- **Performance Consistency** - Standard deviation analysis

### Form Indicators
- **🔥 Improving Form** - Recent performance better than previous
- **📈 Slight Improvement** - Marginal gains in key metrics
- **📊 Stable Form** - Consistent performance levels
- **📉 Declining Form** - Recent performance below previous
- **❄️ Poor Form** - Significant performance drop

### How to Use Form Analysis
1. Select analysis period based on your play frequency
2. Review the comparison metrics
3. Identify areas of improvement or concern
4. Use insights to focus practice and gameplay adjustments
5. Regular monitoring helps track long-term progress

---

## ⚔️ Player Comparison

Compare your statistics with other FACEIT players to understand relative performance.

### Adding Players to Comparison
1. **➕ Добавить себя** - Add your own profile to comparison
2. **👤 Добавить игрока** - Add another player by FACEIT nickname
3. **Maximum 2 players** can be compared at once

### Finding Players
- Enter **exact FACEIT nickname** of the player
- Bot validates the profile exists
- Player statistics are loaded automatically
- Invalid nicknames will show an error message

### Comparison Metrics
The detailed comparison includes:

**Basic Information:**
- **FACEIT Level** and ELO rating
- **Total matches played** and experience
- **Win rate percentage** and success metrics

**Combat Statistics:**
- **K/D Ratio** - Killing efficiency comparison
- **Average Kills/Deaths/Assists** per match
- **ADR** - Damage output analysis
- **Headshot percentage** - Accuracy comparison

**Advanced Metrics:**
- **HLTV 2.1 Rating** - Professional performance metric
- **KAST percentage** - Round impact comparison
- **Utility usage** - Grenade and flash effectiveness
- **Multi-kill frequency** - 3K, 4K, and Ace rates

### Comparison Features
- **Side-by-side format** - Easy visual comparison
- **Winner indicators** - Highlights who performs better in each category
- **Percentage differences** - Shows exact performance gaps
- **Strength/weakness analysis** - Identifies areas of advantage

### Comparison Tips
- Compare with players of similar skill level for meaningful insights
- Look for specific areas where you can improve
- Use comparisons to set realistic performance goals
- Consider different playstyles when interpreting results

---

## 🔍 Current Match Analysis

Analyze live or upcoming FACEIT matches for strategic insights and predictions.

### How to Use
1. **🔍 Поиск матча** - Find match by player nickname or match URL
2. **Enter FACEIT match link** or player name
3. **Automatic analysis** of team compositions and predictions

### Analysis Features

**Team Analysis:**
- **Average ELO** of each team
- **Individual player ratings** and skill levels
- **Recent form** of each player
- **Map-specific statistics** if available

**Match Predictions:**
- **Win probability** for each team
- **Key players** to watch
- **Strategic recommendations**
- **Expected performance ranges**

**Real-time Updates:**
- **Live match tracking** if ongoing
- **Updated statistics** pulled from FACEIT
- **Form analysis** based on recent matches

### Match Analysis Benefits
- **Betting insights** - Informed decision making
- **Strategic preparation** - Know your opponents
- **Team balancing** - Understand skill gaps
- **Performance expectations** - Set realistic goals

---

## 🔔 Notifications & Settings

### Notification System
The bot can automatically notify you when matches are completed:

**Notification Features:**
- **Automatic detection** of finished matches
- **Match result** and personal performance summary
- **ELO change** and rating impact
- **Quick access** to detailed statistics

### Enabling/Disabling Notifications
1. Go to **👤 Профиль** → **🔔 Уведомления**
2. Toggle notifications **on/off**
3. Changes take effect immediately
4. Default setting is **enabled**

### Notification Content
Each notification includes:
- **Match result** (Win/Loss)
- **Final score** and map played
- **Your K/D/A** statistics
- **ADR and HLTV rating** for the match
- **ELO change** (+/- points)
- **Link to full match details**

### Privacy Settings
- **Notifications are private** - Only sent to you
- **No data sharing** with other users
- **Can be disabled** at any time
- **No spam** - Only actual match completions

---

## 🎮 Last Match Details

View comprehensive details about your most recent FACEIT match.

### Quick Access
- Use **🎮 Последний матч** from the main menu
- Automatically loads your latest completed match
- **🔄 Обновить данные** - Refresh if new match available

### Match Information Displayed

**Match Overview:**
- **Date and time** of completion
- **Map name** and mode
- **Final score** and match duration
- **Win/Loss result** with visual indicator

**Your Performance:**
- **K/D/A** (Kills/Deaths/Assists)
- **HLTV 2.1 Rating** for the match
- **ADR** and total damage dealt
- **Headshot percentage**
- **KAST percentage** (rounds with impact)
- **MVP rounds** earned

**Team Information:**
- **Both team compositions** and player names
- **ELO ratings** of all players
- **Individual statistics** of teammates and opponents
- **Team average ratings** and skill levels

**Match Impact:**
- **ELO change** (+/- rating points)
- **Effect on overall statistics**
- **Performance vs personal averages**

### Additional Actions
- **📊 Детальная статистика** - Extended match analysis
- **🔄 Обновить данные** - Check for newer matches
- **Direct link** to FACEIT match page

---

## 📖 Navigation Guide

### Using the Interface

**Reply Keyboard (Bottom of Screen):**
- **Always visible** - Buttons stay at bottom
- **Quick access** - One tap to main functions
- **Organized layout** - Grouped by category
- **🔙 Назад** - Return to previous menu

**Inline Buttons (In Messages):**
- **Context-sensitive** - Relevant to current function
- **Detailed options** - More specific choices
- **Progressive navigation** - Drill down into details

### Navigation Tips
1. **Use Reply Keyboard** for main functions
2. **Use Inline Buttons** for specific actions
3. **🔙 Назад** always returns to previous screen
4. **🏠 Главное меню** returns to main menu from anywhere
5. **State is preserved** - Bot remembers your progress

### Menu Structure
```
Main Menu
├── 📊 Statistics
│   ├── General Stats
│   ├── Map Statistics
│   └── Session Stats
├── 📝 History
│   └── Match List (5/10/30/custom)
├── 📈 Form Analysis
│   └── Period Comparison
├── 🎮 Last Match
│   └── Detailed Match View
├── ⚔️ Player Comparison
│   ├── Add Players
│   └── Comparison Results
├── 🔍 Match Analysis
│   └── Live Match Insights
└── 👤 Profile
    ├── Account Info
    ├── Change Profile
    └── Notifications
```

---

## ❓ FAQ - Frequently Asked Questions

### **Q: Why can't I link my FACEIT account?**
**A:** Common issues:
- **Nickname spelling** - Must be exact, case-sensitive
- **Private profile** - FACEIT profile must be public
- **No CS2 matches** - Need at least one CS2 match on FACEIT
- **Temporary API issues** - Try again in a few minutes

### **Q: My statistics seem outdated. How do I refresh them?**
**A:** Statistics update automatically:
- **Match completion** - Updates within 5-10 minutes after match ends
- **Manual refresh** - Some sections have "🔄 Обновить данные" button
- **Cache system** - Data may be cached for performance, usually updates within 15 minutes

### **Q: Can I track statistics for multiple accounts?**
**A:** Currently:
- **One account per user** - Bot links to one FACEIT profile
- **Easy switching** - Use "🔄 Сменить профиль" to change accounts
- **History preserved** - Previous data isn't lost when switching

### **Q: What does HLTV 2.1 Rating mean?**
**A:** HLTV 2.1 is a professional CS2 rating system:
- **1.00 is average** - Standard baseline performance
- **Above 1.00** - Above average performance
- **Below 1.00** - Below average performance
- **Factors in** - Kills, deaths, assists, ADR, and impact rounds

### **Q: Why are some match statistics missing?**
**A:** Possible reasons:
- **FACEIT API limitations** - Some data may not be available
- **Match too recent** - Statistics still being processed
- **Private match** - Some matches don't provide detailed stats
- **API errors** - Temporary issues with data retrieval

### **Q: How accurate are the match predictions?**
**A:** Match analysis provides:
- **Statistical probability** - Based on historical performance
- **Not guaranteed** - CS2 matches have many variables
- **Informational only** - Use for insights, not betting decisions
- **Updates regularly** - Based on most recent performance data

### **Q: Can other users see my statistics?**
**A:** Privacy features:
- **Personal bot** - Only you see your data
- **Comparison only** - Others can compare with your public FACEIT stats
- **No data sharing** - Bot doesn't share your information
- **FACEIT public data** - Only uses publicly available FACEIT information

### **Q: What should I do if I encounter an error?**
**A:** Troubleshooting steps:
1. **Try again** - Many errors are temporary
2. **Check spelling** - Ensure correct nicknames and commands
3. **Wait and retry** - API may be temporarily unavailable
4. **Use /start** - Reset bot state if needed
5. **Different function** - Try another feature first

### **Q: How often should I check my statistics?**
**A:** Recommendations:
- **After each session** - Track immediate performance
- **Weekly review** - Monitor trends and improvement
- **Monthly analysis** - Long-term progress evaluation
- **Before important matches** - Form analysis for preparation

---

## 💡 Tips & Tricks

### Getting the Most from Your Statistics

**1. Regular Monitoring**
- **Check after each gaming session** to track immediate performance
- **Weekly reviews** help identify trends and areas for improvement
- **Monthly deep dives** provide long-term progress insights

**2. Using Form Analysis Effectively**
- **Match sample sizes** - Use 20+ matches for reliable trends
- **Period selection** - Choose periods that match your playing frequency
- **Focus on consistency** - Look for stable improvement rather than volatile swings

**3. Smart Comparisons**
- **Compare with similar skill levels** for realistic benchmarks
- **Focus on specific metrics** rather than overall comparison
- **Use as motivation** - Set goals based on stronger players' performance

**4. Understanding Your Data**
- **ADR consistency** is often more important than K/D spikes
- **KAST percentage** shows round impact beyond kills
- **Map-specific performance** reveals strengths and weaknesses

### Performance Improvement Tips

**1. Identify Weak Points**
- **Map statistics** show which maps need practice
- **Session analysis** reveals when you perform best/worst
- **Form trends** indicate if specific skills are declining

**2. Set Realistic Goals**
- **Incremental improvement** - Focus on 2-3% improvements
- **Metric-specific goals** - Target ADR, KAST, or headshot % improvements
- **Timeline expectations** - Allow 20-30 matches to see meaningful changes

**3. Use Historical Data**
- **Peak performance periods** - Analyze what made those sessions successful
- **Consistency tracking** - Monitor performance stability over time
- **Recovery patterns** - Learn how you bounce back from poor matches

### Advanced Features Usage

**1. Session Statistics**
- **Identify optimal playing times** - When you perform best
- **Fatigue monitoring** - Notice performance drops in long sessions
- **Warmup effectiveness** - Track first vs later match performance

**2. Match History Analysis**
- **Map rotation patterns** - See which maps you play most/least
- **Opponent difficulty tracking** - Monitor performance vs different skill levels
- **Streak analysis** - Understand win/loss pattern impacts

**3. Comparison Strategies**
- **Role-based comparisons** - Compare with players who have similar roles
- **Skill progression tracking** - Compare with players slightly above your level
- **Playstyle analysis** - Learn from players with complementary strengths

### Bot Optimization

**1. Notification Management**
- **Enable for important periods** - Turn on during active improvement phases
- **Disable during breaks** - Avoid spam during inactive periods
- **Use for motivation** - Immediate feedback after matches

**2. Data Quality**
- **Regular profile checks** - Ensure correct account is linked
- **Refresh when needed** - Update data before important analyses
- **Historical consistency** - Don't switch accounts frequently for better trends

**3. Feature Combination**
- **Pre-match preparation** - Use current match analysis before games
- **Post-match review** - Check last match details after games
- **Weekly planning** - Use form analysis for practice focus

---

## 🔧 Troubleshooting

### Common Issues and Solutions

**Problem: "Profile not found" error**
- **Check nickname spelling** - Must match exactly as shown on FACEIT
- **Verify public profile** - FACEIT profile must be publicly visible
- **Try alternative spellings** - Some players have multiple name variations
- **Recent name changes** - FACEIT names may have been recently updated

**Problem: Statistics not updating**
- **Wait for processing** - FACEIT data can take 10-15 minutes to update
- **Check match completion** - Ensure match fully finished on FACEIT
- **API delays** - FACEIT API may have temporary delays
- **Use refresh buttons** - Some sections have manual refresh options

**Problem: "No matches found" for analysis**
- **Verify CS2 matches** - Only Counter-Strike 2 matches count
- **Check match privacy** - Some tournament/private matches may not appear
- **Account activity** - Ensure recent matches were played on the linked account
- **API availability** - FACEIT data may be temporarily unavailable

**Problem: Comparison not working**
- **Validate both nicknames** - Both players must have public profiles
- **Check CS2 activity** - Both accounts need CS2 match history
- **API rate limits** - Too many requests may cause temporary blocks
- **Data completeness** - Some profiles may lack sufficient statistics

**Problem: Bot not responding**
- **Check internet connection** - Ensure stable internet connectivity
- **Restart with /start** - Reset bot state and try again
- **Wait and retry** - Server may be experiencing temporary issues
- **Try different features** - Test if specific function is affected

### When to Contact Support

**Technical Issues:**
- Persistent errors that don't resolve after 30 minutes
- Data inconsistencies that seem incorrect
- Features completely non-functional for extended periods

**Account Issues:**
- Unable to link correct FACEIT account after multiple attempts
- Statistics showing wrong player or incorrect data
- Profile changes not taking effect

**Feature Requests:**
- Ideas for new statistics or analysis features
- Suggestions for improved user interface
- Requests for additional data sources

---

## 🎯 Best Practices

### Daily Usage
- **Quick morning check** - Review overnight match results
- **Post-session analysis** - Immediate performance feedback
- **Goal tracking** - Monitor progress toward specific targets

### Weekly Review
- **Form analysis** - Compare recent vs previous performance
- **Map focus** - Identify maps needing practice
- **Trend monitoring** - Track long-term improvement patterns

### Monthly Assessment
- **Comprehensive statistics** - Full performance review
- **Goal adjustment** - Update targets based on progress
- **Comparison updates** - Find new players to benchmark against

### Continuous Improvement
- **Data-driven decisions** - Let statistics guide practice focus
- **Regular comparisons** - Stay motivated with peer analysis
- **Balanced perspective** - Don't over-analyze short-term fluctuations

---

**Bot Version:** 2.1.0  
**Last Updated:** January 2025  
**Support:** Use the help system within the bot for additional assistance

Welcome to improved CS2 performance with data-driven insights! 🚀