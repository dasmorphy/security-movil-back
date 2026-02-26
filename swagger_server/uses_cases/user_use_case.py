

from datetime import datetime, timedelta

import jwt

from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.db.users import Users
from swagger_server.models.request_login import RequestLogin
from swagger_server.models.request_post_new_user import RequestPostNewUser
from swagger_server.repository.user_repository import UserRepository
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

class UserUseCase:

    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    def post_new_user(self, body: RequestPostNewUser, internal, external) -> None:        
        hashed_password = pwd_context.hash(body.new_user.password)
        
        new_user = Users(
            user=body.new_user.user,
            email=body.new_user.email,
            password=hashed_password,
            role_id=body.new_user.role_id,
            attributes=body.new_user.attributes,
        )

        self.user_repository.post_new_user(new_user, internal, external)

    def login(self, body: RequestLogin, internal, external):
        pass_hash = self.user_repository.get_pass_hash(body.login.user, internal, external)
        pass_verify = pwd_context.verify(body.login.password, pass_hash)

        if not pass_verify:
            raise CustomAPIException(message="Credenciales incorrectas", status_code=401)
        
        user_autenticated = self.user_repository.get_user(body.login.user, internal, external)
        verify_user_session = self.user_repository.search_user_session(user_autenticated['id_user'], internal, external)

        if verify_user_session:
            raise CustomAPIException(message="El usuario ya tiene una sesión activa", status_code=401)

        token = self.generate_jwt(user_autenticated)
        self.user_repository.save_token(token, user_autenticated['id_user'], internal, external)

        return token
    

    def generate_jwt(self, user_data, expires_minutes=60) -> str:
        user_data['sub'] = user_data['id_user']
        user_data['iat'] = datetime.now()
        user_data['exp'] = datetime.now() + timedelta(minutes=expires_minutes)
        
        with open("private.pem", "r") as f:
            private_key = f.read()
        
        token = jwt.encode(user_data, private_key, algorithm="RS256")

        return token


