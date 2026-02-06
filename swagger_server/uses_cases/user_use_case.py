

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
        
        return self.user_repository.get_user(body.login.user, internal, external)


