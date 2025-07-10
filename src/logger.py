from loguru import logger

logger.add("logs/app.log", rotation="1 week", retention="4 weeks", level="INFO")
