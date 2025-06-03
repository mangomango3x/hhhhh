"""
Configuration Settings
Centralized configuration for the Discord Fact-Checker Bot
"""

import os
from typing import List, Dict, Any

# Bot Configuration
BOT_CONFIG: Dict[str, Any] = {
    # Command settings
    'command_prefix': os.getenv('COMMAND_PREFIX', '!'),
    
    # Auto fact-checking settings
    'auto_fact_check': os.getenv('AUTO_FACT_CHECK', 'true').lower() == 'true',
    'respond_to_bots': os.getenv('RESPOND_TO_BOTS', 'false').lower() == 'true',
    
    # Rate limiting settings
    'rate_limit': {
        'max_requests': int(os.getenv('RATE_LIMIT_MAX_REQUESTS', '5')),
        'time_window': int(os.getenv('RATE_LIMIT_TIME_WINDOW', '300'))  # 5 minutes
    },
    
    # Global rate limiting
    'global_rate_limit': {
        'max_requests_per_minute': int(os.getenv('GLOBAL_RATE_LIMIT_PER_MINUTE', '30'))
    },
    
    # Trigger keywords for automatic fact-checking
    'trigger_keywords': [
        # Health misinformation
        'vaccine', 'vaccines', 'vaccination', 'covid', 'coronavirus',
        'hydroxychloroquine', 'ivermectin', 'miracle cure', 'natural immunity',
        'microchip', 'magnetic', '5g causes', 'essential oils cure',
        
        # Political misinformation
        'election fraud', 'stolen election', 'rigged election', 'voter fraud',
        'deep state', 'false flag', 'crisis actor', 'fake news media',
        
        # Science misinformation
        'climate change hoax', 'global warming fake', 'flat earth',
        'chemtrails', 'moon landing fake', 'evolution hoax',
        
        # General misinformation patterns
        'studies show', 'research proves', 'scientists say',
        'doctors hate', 'they don\'t want you to know',
        'hidden truth', 'cover up', 'government conspiracy',
        
        # Financial scams
        'get rich quick', 'guaranteed profit', 'investment opportunity',
        'crypto scam', 'ponzi scheme',
        
        # Additional health claims
        'cure cancer', 'detox', 'cleanse', 'alkaline water',
        'anti-aging', 'weight loss pill', 'burn fat fast'
    ],
    
    # Message filtering
    'min_message_length': int(os.getenv('MIN_MESSAGE_LENGTH', '20')),
    'max_message_length': int(os.getenv('MAX_MESSAGE_LENGTH', '2000')),
    
    # Response settings
    'show_confidence_score': os.getenv('SHOW_CONFIDENCE_SCORE', 'true').lower() == 'true',
    'show_sources': os.getenv('SHOW_SOURCES', 'true').lower() == 'true',
    'max_sources_display': int(os.getenv('MAX_SOURCES_DISPLAY', '3')),
    
    # Auto-moderation settings
    'auto_react_to_misinformation': os.getenv('AUTO_REACT_MISINFORMATION', 'false').lower() == 'true',
    'misinformation_reaction': os.getenv('MISINFORMATION_REACTION', '⚠️'),
    'fact_check_reaction': os.getenv('FACT_CHECK_REACTION', '🔍'),
}

# Fact-checking API Configuration
FACT_CHECK_CONFIG: Dict[str, Any] = {
    # Gemini API settings
    'model_name': os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'),
    'temperature': float(os.getenv('GEMINI_TEMPERATURE', '0.1')),
    'max_tokens': int(os.getenv('GEMINI_MAX_TOKENS', '1000')),
    
    # Request settings
    'timeout_seconds': int(os.getenv('FACT_CHECK_TIMEOUT', '30')),
    'max_retries': int(os.getenv('FACT_CHECK_MAX_RETRIES', '2')),
    'retry_delay': float(os.getenv('FACT_CHECK_RETRY_DELAY', '1.0')),
    
    # Content filtering
    'min_claim_length': int(os.getenv('MIN_CLAIM_LENGTH', '10')),
    'max_claim_length': int(os.getenv('MAX_CLAIM_LENGTH', '1000')),
    
    # Response processing
    'confidence_threshold': int(os.getenv('CONFIDENCE_THRESHOLD', '60')),
    'require_sources': os.getenv('REQUIRE_SOURCES', 'false').lower() == 'true',
}

# Discord API Configuration
DISCORD_CONFIG: Dict[str, Any] = {
    # Bot permissions (for invite URL generation)
    'permissions': [
        'read_messages',
        'send_messages',
        'embed_links',
        'add_reactions',
        'read_message_history',
        'use_slash_commands'
    ],
    
    # Embed settings
    'embed_color': int(os.getenv('EMBED_COLOR', '0x3498db'), 16),  # Blue
    'error_color': int(os.getenv('ERROR_COLOR', '0xe74c3c'), 16),  # Red
    'success_color': int(os.getenv('SUCCESS_COLOR', '0x2ecc71'), 16),  # Green
    'warning_color': int(os.getenv('WARNING_COLOR', '0xf39c12'), 16),  # Orange
    
    # Message settings
    'max_embed_length': 6000,
    'max_field_length': 1024,
    'max_description_length': 4096,
}

# Logging Configuration
LOGGING_CONFIG: Dict[str, Any] = {
    'level': os.getenv('LOG_LEVEL', 'INFO').upper(),
    'format': os.getenv('LOG_FORMAT', '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'),
    'date_format': os.getenv('LOG_DATE_FORMAT', '%Y-%m-%d %H:%M:%S'),
    'file_logging': os.getenv('FILE_LOGGING', 'true').lower() == 'true',
    'log_directory': os.getenv('LOG_DIR', 'logs'),
    'max_log_files': int(os.getenv('MAX_LOG_FILES', '7')),
    'log_rotation': os.getenv('LOG_ROTATION', 'daily'),  # daily, weekly, monthly
}

# Performance Configuration
PERFORMANCE_CONFIG: Dict[str, Any] = {
    # Memory management
    'max_cache_size': int(os.getenv('MAX_CACHE_SIZE', '1000')),
    'cache_ttl_seconds': int(os.getenv('CACHE_TTL', '3600')),  # 1 hour
    
    # Concurrent processing
    'max_concurrent_fact_checks': int(os.getenv('MAX_CONCURRENT_CHECKS', '5')),
    'fact_check_queue_size': int(os.getenv('FACT_CHECK_QUEUE_SIZE', '50')),
    
    # Cleanup intervals
    'rate_limit_cleanup_interval': int(os.getenv('RATE_LIMIT_CLEANUP_INTERVAL', '300')),  # 5 minutes
    'cache_cleanup_interval': int(os.getenv('CACHE_CLEANUP_INTERVAL', '600')),  # 10 minutes
}

# Security Configuration
SECURITY_CONFIG: Dict[str, Any] = {
    # Input validation
    'sanitize_input': os.getenv('SANITIZE_INPUT', 'true').lower() == 'true',
    'max_input_length': int(os.getenv('MAX_INPUT_LENGTH', '2000')),
    'blocked_patterns': [
        r'<script.*?>.*?</script>',  # Script tags
        r'javascript:',              # JavaScript URLs
        r'data:.*?base64',          # Base64 data URLs
        r'<iframe.*?>',             # Iframe tags
    ],
    
    # API security
    'require_api_keys': os.getenv('REQUIRE_API_KEYS', 'true').lower() == 'true',
    'validate_ssl': os.getenv('VALIDATE_SSL', 'true').lower() == 'true',
    
    # User restrictions
    'blacklisted_users': os.getenv('BLACKLISTED_USERS', '').split(',') if os.getenv('BLACKLISTED_USERS') else [],
    'admin_users': os.getenv('ADMIN_USERS', '').split(',') if os.getenv('ADMIN_USERS') else [],
}

# Feature Flags
FEATURE_FLAGS: Dict[str, bool] = {
    'enable_fact_checking': os.getenv('ENABLE_FACT_CHECKING', 'true').lower() == 'true',
    'enable_auto_checking': os.getenv('ENABLE_AUTO_CHECKING', 'true').lower() == 'true',
    'enable_manual_commands': os.getenv('ENABLE_MANUAL_COMMANDS', 'true').lower() == 'true',
    'enable_rate_limiting': os.getenv('ENABLE_RATE_LIMITING', 'true').lower() == 'true',
    'enable_logging': os.getenv('ENABLE_LOGGING', 'true').lower() == 'true',
    'enable_metrics': os.getenv('ENABLE_METRICS', 'false').lower() == 'true',
    'enable_web_interface': os.getenv('ENABLE_WEB_INTERFACE', 'false').lower() == 'true',
}

def validate_config():
    """Validate configuration settings"""
    errors = []
    
    # Check required environment variables
    required_vars = ['DISCORD_TOKEN', 'GEMINI_API_KEY']
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Validate numeric ranges
    if BOT_CONFIG['rate_limit']['max_requests'] <= 0:
        errors.append("RATE_LIMIT_MAX_REQUESTS must be greater than 0")
    
    if BOT_CONFIG['rate_limit']['time_window'] <= 0:
        errors.append("RATE_LIMIT_TIME_WINDOW must be greater than 0")
    
    if FACT_CHECK_CONFIG['temperature'] < 0 or FACT_CHECK_CONFIG['temperature'] > 1:
        errors.append("GEMINI_TEMPERATURE must be between 0 and 1")
    
    if FACT_CHECK_CONFIG['max_tokens'] <= 0:
        errors.append("GEMINI_MAX_TOKENS must be greater than 0")
    
    # Validate command prefix
    if not BOT_CONFIG['command_prefix'] or len(BOT_CONFIG['command_prefix']) > 5:
        errors.append("COMMAND_PREFIX must be 1-5 characters long")
    
    return errors

def get_config_summary() -> Dict[str, Any]:
    """Get a summary of current configuration (without sensitive data)"""
    return {
        'bot': {
            'command_prefix': BOT_CONFIG['command_prefix'],
            'auto_fact_check': BOT_CONFIG['auto_fact_check'],
            'rate_limit': BOT_CONFIG['rate_limit'],
            'trigger_keywords_count': len(BOT_CONFIG['trigger_keywords'])
        },
        'fact_check': {
            'model_name': FACT_CHECK_CONFIG['model_name'],
            'temperature': FACT_CHECK_CONFIG['temperature'],
            'max_tokens': FACT_CHECK_CONFIG['max_tokens'],
            'timeout_seconds': FACT_CHECK_CONFIG['timeout_seconds']
        },
        'features': FEATURE_FLAGS,
        'performance': PERFORMANCE_CONFIG
    }

# Load and validate configuration on import
config_errors = validate_config()
if config_errors:
    import sys
    print("Configuration errors found:")
    for error in config_errors:
        print(f"  - {error}")
    print("\nPlease fix these errors before starting the bot.")
    sys.exit(1)
