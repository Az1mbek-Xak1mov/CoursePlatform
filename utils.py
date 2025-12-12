import random
import orjson
from redis import Redis
import os
from dotenv import load_dotenv

load_dotenv()

# Build Redis URL from individual env vars or use REDIS_URL directly
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = os.getenv('REDIS_PORT', '6379')
REDIS_DB = os.getenv('REDIS_DB', '0')
REDIS_URL = os.getenv('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')


def generate_code(length: int = 6):
    return "".join(str(random.randint(0, 9)) for _ in range(length))


class OtpService:
    def __init__(self):
        self.redis_client = Redis.from_url(REDIS_URL, decode_responses=False)

    def _otp_key(self, phone: str, purpose: str = "login") -> str:
        return f"otp:{purpose}:{phone}"

    def get_otp(self, phone: str, purpose: str = "register"):
        otp_key = self._otp_key(phone, purpose)
        val = self.redis_client.get(otp_key)
        if not val:
            return None
        if isinstance(val, bytes):
            try:
                return val.decode()
            except Exception:
                return val.decode('utf-8', errors='ignore')
        return str(val)

    def _user_data_key(self, phone: str) -> str:
        return f"user_temp:{phone}"

    def save_user_temp(self, phone: str, user_data: dict, expire: int = 300):
        key = f"user_temp:{phone}"
        self.redis_client.setex(key, expire, orjson.dumps(user_data))
        return True, 0

    def send_otp(self, phone: str, code: str, purpose="register", expire: int = 300):
        key = f"otp:{purpose}:{phone}"
        self.redis_client.setex(key, expire, code)
        print(f"[DEBUG] OTP для {phone} ({purpose}): {code}")
        return True, 0

    def verify_otp(self, phone: str, code: str, purpose="register"):
        otp_key = f"otp:{purpose}:{phone}"
        saved_code = self.redis_client.get(otp_key)
        if not saved_code or saved_code.decode() != code:
            return False, None

        user_data = None
        if purpose == "register":
            user_key = f"user_temp:{phone}"
            raw = self.redis_client.get(user_key)
            if raw:
                user_data = orjson.loads(raw)
        return True, user_data

    def delete_otp(self, phone: str, purpose: str = "login") -> None:
        otp_key = self._otp_key(phone, purpose)
        self.redis_client.delete(otp_key)

        if purpose == "register":
            user_data_key = self._user_data_key(phone)
            self.redis_client.delete(user_data_key)
