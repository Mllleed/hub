from authx import AuthX, AuthXConfig

from app.service import settings

from app.DAO import UserDAO

config = AuthXConfig(
    JWT_ALGORITHM="HS256",
    JWT_SECRET_KEY=settings.SECRET_KEY,
    JWT_TOKEN_LOCATION=["cookies"],
    JWT_COOKIE_CSRF_PROTECT=True,
)

auth = AuthX(config=config)

auth.set_callback_get_model_instance(UserDAO.get_user_by_id)