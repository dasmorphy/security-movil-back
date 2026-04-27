

from datetime import datetime, timezone
from user_agents import parse

import jwt

from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.db.user_sessions import UserSessions
from swagger_server.models.db.users import Users
from swagger_server.models.request_login import RequestLogin
from swagger_server.models.request_logout import RequestLogout
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
        with open("private.pem", "r") as f:
            self.private_key = f.read()

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


    def form_expo(self, data, internal, external):
        self.user_repository.post_form_expo(data, internal, external)

    def login(self, body: RequestLogin, channel: str, internal, external):
        pass_hash = self.user_repository.get_pass_hash(body.login.user, internal, external)
        pass_verify = pwd_context.verify(body.login.password, pass_hash)

        if not pass_verify:
            raise CustomAPIException(message="Credenciales incorrectas", status_code=401)
        
        user_autenticated = self.user_repository.get_user(body.login.user, internal, external)

        if (channel == 'ZENTINEL'):
            return user_autenticated
        
        # verify_user_session = self.user_repository.search_user_session(user_autenticated['id_user'], internal, external)

        # if verify_user_session:
        #     raise CustomAPIException(message="El usuario ya tiene una sesión activa", status_code=401)

        token = self.generate_jwt(user_autenticated)

        return {
            "token": token,
            "user_id": user_autenticated['id_user']
        }
    
    def logout(self, body: RequestLogout, internal, external):
        self.user_repository.logout(body.logout.token, internal, external)


    def save_session(self, authenticated_user, headers, internal, external):
        ip_user = headers.get("X-Forwarded-For", "")
        ua_string = headers.get("User-Agent", "")

        device = None
        os = None

        try:
            if ua_string:
                user_agent = parse(ua_string)

                # OS
                os = user_agent.os.family if user_agent.os and user_agent.os.family else None

                # DEVICE
                if user_agent.device and user_agent.device.family:
                    device_family = user_agent.device.family

                    if device_family == "Other":
                        if user_agent.is_pc:
                            device = "PC"
                        else:
                            device = "Other"
                    else:
                        device = device_family
                else:
                    device = None

        except Exception:
            device = None
            os = None

        # print(user_agent.os.family)       # Windows, Android, iOS
        # print(user_agent.os.version_string)

        # print(user_agent.browser.family)  # Chrome, Firefox
        # print(user_agent.browser.version_string)

        # print(user_agent.device.family)   # iPhone, Samsung, etc.

        # print(user_agent.is_mobile)
        # print(user_agent.is_tablet)
        # print(user_agent.is_pc)

        # print(user_agent)

        session = UserSessions(
            token_session=authenticated_user["token"],
            user_id=authenticated_user["user_id"],
            ip_user=ip_user,
            device=device,
            os=os
        )

        self.user_repository.save_session(session, internal, external)
        
    

    def generate_jwt(self, user_data, expires_minutes=60) -> str:
        user_data['sub'] = user_data['id_user']
        user_data['iat'] = datetime.now(timezone.utc)
        # int(datetime.datetime.utcnow().timestamp())
        # user_data['exp'] = datetime.now() + timedelta(minutes=expires_minutes)
        
        token = jwt.encode(user_data, self.private_key, algorithm="RS256")

        return token


