from loguru import logger
from sqlalchemy import cast, exists, func, select
from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.db.business import Business
from swagger_server.models.db.group_business import GroupBusiness
from swagger_server.models.db.permissions import Permission
from swagger_server.models.db.role_permissions import RolePermission
from swagger_server.models.db.roles import Roles
from swagger_server.models.db.unity_weight import UnityWeight
from swagger_server.models.db.users import Users
from swagger_server.resources.databases.postgresql import PostgreSQLClient
from sqlalchemy.dialects.postgresql import JSONB


class UserRepository:
    
    def __init__(self):
        self.db = PostgreSQLClient("POSTGRESQL")


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
                    .join(RolePermission, RolePermission.role_id == Users.role_id)
                    .join(Permission, Permission.id_permission == RolePermission.permission_id)
                    .join(Roles, Roles.id_rol == Users.role_id)
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
                    "id_user": user_found.id_user,
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