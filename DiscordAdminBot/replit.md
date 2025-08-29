# Discord Administration Bot

## Overview

This is a modular Discord administration bot built with Python and discord.py. The bot provides 28 slash commands for comprehensive server management, including standard moderation features and special administrative tools. It uses an SQLite database for persistent data storage and features a structured cog-based architecture for organized command management.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Bot Architecture
- **Framework**: discord.py with slash commands implementation
- **Architecture Pattern**: Cog-based modular design for command organization
- **Command System**: Discord slash commands with proper permission checking
- **Configuration**: JSON-based configuration system with runtime loading/saving capabilities

### Database Layer
- **Database**: SQLite via aiosqlite for asynchronous operations
- **Schema**: Relational tables for warnings, mutes, and moderation logs
- **ORM**: Custom database abstraction layer without external ORM dependencies
- **Data Persistence**: Local file-based storage for reliability and simplicity

### Permission System
- **Access Control**: Decorator-based permission checking for admin and moderation roles
- **Hierarchy Validation**: Bot role position validation before executing commands
- **Permission Types**: Separate decorators for admin permissions and general moderation permissions
- **Security**: Owner bypass functionality with fallback permission checks

### Logging and Audit System
- **Moderation Logging**: Comprehensive logging of all moderation actions to database
- **Channel Logging**: Optional mod log channel integration for real-time notifications
- **Audit Trail**: Timestamped action logs with moderator, target, and reason tracking
- **Error Handling**: Graceful failure handling with user-friendly error messages

### Command Organization
- **Moderation Cog**: Core punishment commands (ban, kick, mute, warn, etc.)
- **Server Management Cog**: Channel and server-wide management tools
- **Utility Cog**: Information commands (serverinfo, userinfo, avatar)
- **Special Commands Cog**: Advanced administrative tools (echo, mass operations, lockdown)

### Data Management
- **Configuration**: Runtime-editable bot configuration with JSON persistence
- **User Data**: Warning system with configurable thresholds and auto-actions
- **Temporary Actions**: Time-based muting system with automatic expiration
- **Bulk Operations**: Mass role assignment and channel lockdown capabilities

## External Dependencies

### Core Libraries
- **discord.py**: Main Discord API wrapper for bot functionality
- **aiosqlite**: Asynchronous SQLite database operations
- **asyncio**: Asynchronous programming support for concurrent operations

### System Dependencies
- **logging**: Built-in Python logging for error tracking and debugging
- **json**: Configuration file parsing and management
- **datetime**: Time-based operations for mutes and logging timestamps
- **os**: File system operations for configuration and database management

### Discord Integrations
- **Slash Commands**: Modern Discord command interface
- **Embed System**: Rich message formatting for responses and logs
- **Permission System**: Integration with Discord's role-based permissions
- **Member Management**: User targeting, role manipulation, and server actions