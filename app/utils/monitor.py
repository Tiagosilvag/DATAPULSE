from flask_login import current_user
import time
from app.utils.logger import logger

def monitor(func):

    def wrapper(*args, **kwargs):

        start = time.time()

        usuario = getattr(current_user, "login", "anon")

        try:
            result = func(*args, **kwargs)

            elapsed = round((time.time() - start) * 1000, 2)

            logger.info(
                f"[OK] {func.__name__} | user={usuario} | tempo={elapsed}ms"
            )

            return result

        except Exception as e:

            elapsed = round((time.time() - start) * 1000, 2)

            logger.error(
                f"[ERRO] {func.__name__} | user={usuario} | tempo={elapsed}ms | erro={str(e)}"
            )

            raise

    return wrapper