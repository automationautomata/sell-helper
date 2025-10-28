from dataclasses import dataclass


@dataclass
class User:
    email: str
    salt: str
    password_hash: str
