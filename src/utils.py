import random
import string

token_64_sample = string.ascii_letters + string.digits + '-_'


def generate_token(length: int = 10):  # 64
    return ''.join(random.choices(token_64_sample, k=length))
