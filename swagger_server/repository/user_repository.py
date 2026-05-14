import base64
import os
import io

from loguru import logger
from sqlalchemy import Integer, and_, cast, exists, func, select, text
from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.db.business import Business
from swagger_server.models.db.company_modules import CompanyModules
from swagger_server.models.db.group_business import GroupBusiness
from swagger_server.models.db.modules import Modules
from swagger_server.models.db.permissions import Permission
from swagger_server.models.db.role_permissions import RolePermission
from swagger_server.models.db.roles import Roles
from swagger_server.models.db.unity_weight import UnityWeight
from swagger_server.models.db.user_sessions import UserSessions
from swagger_server.models.db.users import Users
from swagger_server.models.form_expo_data import FormExpoData
from swagger_server.resources.databases.postgresql import PostgreSQLClient
from sqlalchemy.dialects.postgresql import JSONB
import resend
import qrcode

from swagger_server.resources.databases.redis import RedisClient

resend.api_key = os.getenv('RESEND_API_KEY')

class UserRepository:
    
    def __init__(self):
        self.db = PostgreSQLClient("POSTGRESQL")
        self.redis_client = RedisClient()


    def post_form_expo(self, data: FormExpoData, internal, external):
        with self.db.session_factory() as session:
            try:

                register_exist = text("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM public.form_expo
                        WHERE email = :email
                    )
                """)

                if session.execute(register_exist, {"email": data.email}).scalar():
                    raise CustomAPIException(message="El correo ya se encuentra registrado", status_code=400)

                query = text("""
                    INSERT INTO public.form_expo 
                    (names, email, business, position, type_industry, is_assist, phone, token_qr, status_email)
                    VALUES 
                    (:names, :email, :business, :position, :type_industry, :is_assist, :phone, :token_qr, 'No Aplica')
                    RETURNING *
                """)

                result = session.execute(query, {
                    "names": data.names,
                    "email": data.email,
                    "business": data.business,
                    "position": data.position,
                    "type_industry": data.type_industry,
                    "is_assist": data.is_assist,
                    "phone": data.phone,
                    "token_qr": external,
                })

                created_register = result.mappings().first()
                session.commit()
                return created_register

            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)

                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al insertar en la base de datos", 500)

            finally:
                session.close()

    
    def update_form(self, id_form, status, internal, external):
        with self.db.session_factory() as session:
            try:

                register_exist = text("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM public.form_expo
                        WHERE id_form = :id_form
                    )
                """)

                exists = session.execute(
                    register_exist,
                    {
                        "id_form": id_form
                    }
                ).scalar()

                if not exists:
                    raise CustomAPIException(
                        message="El registro no existe",
                        status_code=404
                    )

                # =========================
                # UPDATE
                # =========================

                query = text("""
                    UPDATE public.form_expo
                    SET status_email = :status_email
                    WHERE id_form = :id_form
                    RETURNING *
                """)

                session.execute(query, {
                    "id_form": id_form,
                    "status_email": status
                })

                session.commit()

            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)

                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al insertar en la base de datos", 500)

            finally:
                session.close()


    def send_email(self, email: str, external):
        qr = qrcode.make(external)
        buffer = io.BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

        resend.Emails.send({
            "from": "Alianza Centinela <noreply@telearseg.net>",
            "to": email,
            "cc": "desarrolladortlsg@telearseg.net",
            "subject": "¡Gracias por registrar en el Primer Evento de Interseguridad!",
            "template": {
                "id": "template-v3",
            },
            "attachments": [
                {
                    "filename": "qr.png",
                    "content": qr_base64,
                    "content_id": "qr_code"
                }
            ]
        })

    def validate_qr(self, token, internal, external):
        with self.db.session_factory() as session:
            try:
                query = text("""
                    SELECT *
                    FROM public.form_expo
                    WHERE token_qr = :token_qr
                    LIMIT 1
                """)

                token_exist = session.execute(query, {"token_qr": token}).mappings().first()

                if not token_exist:
                    raise CustomAPIException("Qr no existe", 404)
                
                if token_exist["scanned"]:
                    raise CustomAPIException("Qr ya escaneado", 400)

                
                query = text("""
                    UPDATE public.form_expo
                    SET scanned = :scanned
                    WHERE token_qr = :token_qr
                """)

                session.execute(query, {
                    "token_qr": token,
                    "scanned": True,
                })

                session.commit()
                
                return {
                    "id_form": token_exist["id_form"],
                    "names": token_exist["names"],
                    "email": token_exist["email"],
                    "business": token_exist["business"],
                    "position": token_exist["position"],
                    "type_industry": token_exist["type_industry"],
                    "is_assist": token_exist["is_assist"],
                    "phone": token_exist["phone"],
                    "token_qr": token_exist["token_qr"],
                    "scanned": True,
                    "created_at": token_exist["created_at"]
                }

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)
            

    def validate_send_email(self, id, internal, external):
        with self.db.session_factory() as session:
            try:
                query = text("""
                    SELECT *
                    FROM public.form_expo
                    WHERE id_form = :id_form
                """)

                form_exist = session.execute(query, {"id_form": id}).mappings().first()

                if not form_exist:
                    raise CustomAPIException("Invitación no existe", 404)
                
                if form_exist["status_email"] == "Enviado":
                    raise CustomAPIException("El correo ya fue enviado", 400)

                self.send_email(form_exist["email"], external)
                
                query = text("""
                    UPDATE public.form_expo
                    SET status_email = :status_email
                    WHERE id_form = :id_form
                """)

                session.execute(query, {
                    "status_email": "Enviado",
                    "id_form": id
                })

                session.commit()

            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)

    def get_form_expo(self, internal, external):
        with self.db.session_factory() as session:
            try:
                query = text("""
                    SELECT * 
                    FROM public.form_expo
                    ORDER BY created_at desc
                """)

                rows = session.execute(query).mappings().all()

                data = [
                    {
                        "id_form": row["id_form"],
                        "names": row["names"],
                        "email": row["email"],
                        "business": row["business"],
                        "position": row["position"],
                        "type_industry": row["type_industry"],
                        "is_assist": row["is_assist"],
                        "phone": row["phone"],
                        "token_qr": row["token_qr"],
                        "scanned": row["scanned"],
                        "created_at": row["created_at"],
                        "status_email": row["status_email"]
                    }
                    for row in rows
                ]

                return data
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)


    def post_new_user(self, new_user_body: Users, internal, external) -> None:
        with self.db.session_factory() as session:
            try:
                business_id = new_user_body.attributes.get("business")
                group_business_id = new_user_body.attributes.get("group_business")
                role_name = new_user_body.role_id

                user_exist = session.execute(
                    select(
                        exists().where(
                            Users.user == new_user_body.user
                        )
                    )
                ).scalar()

                if user_exist:
                    raise CustomAPIException(message="Usuario ya existe", status_code=400)

                role = session.execute(
                    select(Roles).where(Roles.name == role_name)
                ).scalar_one_or_none()

                if not role:
                    raise CustomAPIException(
                        message=f"Rol '{role_name}' no existe",
                        status_code=404
                    )

                if business_id:
                    business_exists = session.execute(
                        select(
                            exists().where(
                                Business.id_business == business_id
                            )
                        )
                    ).scalar()

                    if not business_exists:
                        raise CustomAPIException(message="No existe la empresa", status_code=404)

                if group_business_id:
                    group_business_exists = session.execute(
                        select(
                            exists().where(
                                GroupBusiness.id_group_business == group_business_id
                            )
                        )
                    ).scalar()

                    if not group_business_exists:
                        raise CustomAPIException(message="No existe el grupo de empresa", status_code=404)

                new_user = Users(
                    user=new_user_body.user,
                    email=new_user_body.email,
                    password= new_user_body.password,
                    role_id= role.id_rol,
                    attributes=new_user_body.attributes,
                )

                session.add(new_user)
                session.commit()

            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al insertar en la base de datos", 500)

            finally:
                session.close()


    def get_pass_hash(self, user: str, internal, external):
        with self.db.session_factory() as session:
            try:
                user_found = session.execute(
                    select(Users.password).where(Users.user == user)
                ).scalar_one_or_none()

                if not user_found:
                    raise CustomAPIException(message="Credenciales incorrectas", status_code=401)

                return user_found
            
            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)

            finally:
                session.close()


    def get_user(self, user: str, internal, external):
        with self.db.session_factory() as session:
            try:
                stmt = (
                    select(
                        Users.id_user,
                        Users.user,
                        Users.email,
                        Users.is_active,
                        Roles.name.label("role"),
                        func.jsonb_set(
                            func.coalesce(Users.attributes, cast("{}", JSONB)),
                            '{permissions}',
                            func.jsonb_agg(func.to_jsonb(Permission.name)),
                            True
                        ).label("attributes")
                    )
                    .join(Roles, Roles.id_rol == Users.role_id)
                    .join(RolePermission, RolePermission.role_id == Roles.id_rol)
                    .join(Permission, Permission.id_permission == RolePermission.permission_id)
                    .join(Modules, Modules.id_module == Permission.module_id)
                    .join(
                        CompanyModules,
                        and_(
                            CompanyModules.module_id == Modules.id_module,
                            CompanyModules.business_id == cast(
                                Users.attributes["id_business"].astext,
                                Integer
                            )
                        )
                    )
                    .where(Users.user == user)
                    .group_by(
                        Users.id_user,
                        Users.user,
                        Users.email,
                        Users.attributes,
                        Roles.name
                    )
                )

                user_found = session.execute(stmt).one_or_none()

                if not user_found:
                    raise CustomAPIException(message="Credenciales incorrectas", status_code=401)
                

                if not user_found.is_active:
                    raise CustomAPIException(message="Usuario no activo", status_code=401)
                

                user_autenticated = {
                    "id_user": str(user_found.id_user),
                    "role": user_found.role,
                    "user": user_found.user,
                    "email": user_found.email,
                    "is_active": user_found.is_active,
                    "attributes": user_found.attributes
                }
                

                return user_autenticated
            
            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)

            finally:
                session.close()


    def logout(self, token: str, internal: str, external: str):
        with self.db.session_factory() as session:
            try:
                session_user = session.execute(
                    select(UserSessions).where(UserSessions.token_session == token)
                ).scalar_one_or_none()

                if not session_user:
                    raise CustomAPIException("Sesión no encontrada", 404)

                self.delete_session_redis(token)
                session.delete(session_user)
                session.commit()
            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                raise CustomAPIException("Error al obtener en la base de datos", 500)
            finally:
                session.close()

    def delete_session_redis(self, token):
        user_id = self.redis_client.client.get(f"token:{token}")
        if user_id:
            self.redis_client.client.delete(
                f"token:{token}",
            )


    def save_session(self, data: UserSessions, internal, external):
        with self.db.session_factory() as session:
            try:
                self.save_token_cache(data.token_session, str(data.user_id), internal, external)
                session.add(data)
                session.commit()
            except Exception as exception:
                session.rollback()
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                if isinstance(exception, CustomAPIException):
                    raise exception
                
                raise CustomAPIException("Error al obtener en la base de datos", 500)

            finally:
                session.close()

    def save_token_cache(self, token: str, usr_id: str, internal, external):
        try:
            ttl = 60 * 60 * 24  # 24 horas
            self.redis_client.client.set(
                f"token:{token}",
                usr_id,
                ex=ttl
            )
                        
        except Exception as exception:
            logger.error('Error: {}', str(exception), internal=internal, external=external)                
            raise CustomAPIException("Error al guardar el token del usuario", 500)
        
        
    def search_user_session(self, id_user: str, internal, external):
        with self.db.session_factory() as session:
            try:
                session_user = session.execute(
                    select(UserSessions).where(UserSessions.user_id == id_user)
                ).scalar_one_or_none()

                if not session_user:
                    return False

                exists_in_redis = self.redis_client.client.get(
                    f"token:{session_user.token_session}"
                )

                if not exists_in_redis:
                    session.delete(session_user)
                    session.commit()
                    return False

                return True
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                raise CustomAPIException("No se encontro la sesion del usuario", 401)