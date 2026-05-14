

from datetime import datetime, timezone
from uuid import UUID
from loguru import logger
from user_agents import parse
from rapidfuzz import fuzz
from io import BytesIO
import pandas as pd

import jwt

from swagger_server.exception.custom_error_exception import CustomAPIException
from swagger_server.models.db.user_sessions import UserSessions
from swagger_server.models.db.users import Users
from swagger_server.models.form_expo_data import FormExpoData
from swagger_server.models.request_login import RequestLogin
from swagger_server.models.request_logout import RequestLogout
from swagger_server.models.request_post_new_user import RequestPostNewUser
from swagger_server.repository.user_repository import UserRepository
from passlib.context import CryptContext

from swagger_server.utils.utils import CONTACTS_BY_CLIENT, PREFIX_RE

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


    def form_expo(self, data: FormExpoData, internal, external):
        form_saved = self.user_repository.post_form_expo(data, internal, external)

        if data.is_coincidence:
            try:
                result = self.validate_contact(data.business, data.names)
                
                if result["status"] == 'Enviado':
                    self.user_repository.send_email(data.email, external)

                self.user_repository.update_form(form_saved["id_form"], result["status"], internal, external)
            
            except Exception as exception:
                logger.error('Error: {}', str(exception), internal=internal, external=external)
                raise CustomAPIException("Error al enviar el correo", 500)
            

    def send_email_qr(self, id_form, internal, external):
        self.user_repository.validate_send_email(id_form, internal, external)

        

    def get_form_expo(self, internal, external):
        return self.user_repository.get_form_expo(internal, external)
    
    def validate_qr(self, token, internal, external):
        try:
            UUID(token)
            return self.user_repository.validate_qr(token, internal, external)

        except ValueError:
            raise CustomAPIException("Formato de QR inválido", 400)
        

    def get_report_history(self, internal, external):      
        history_data = self.user_repository.get_form_expo(internal, external)
        
        if len(history_data) == 0:
            raise CustomAPIException("No se han encontrado resultados", 404)
        
        df = pd.DataFrame(history_data)

        df["is_assist"] = df["is_assist"].map({True: "Si", False: "No"}).fillna("")
        df["scanned"] = df["scanned"].map({True: "Si", False: "No"}).fillna("")

        df = df.rename(columns={
            "created_at": "Fecha",
            "names": "Nombres",
            "email": "Correo",
            "phone": "Celular",
            "position": "Cargo",
            "business": "Empresa",
            "type_industry": "Tipo industria",
            "is_assist": "Asistirá",
            "status_email": "Estado email",
            "scanned": "Qr escaneado",
        })

        df = df[
            ["Fecha", "Nombres", "Correo",
            "Celular", "Cargo", "Empresa",
            "Tipo industria", "Asistirá", "Estado email", "Qr escaneado"]
        ]

        # Formato de fecha
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")\
            .dt.strftime("%Y-%m-%d %H:%M:%S")
                
        
        # Escrbir el buffer
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Historial")

        output.seek(0)

        filename = f"reporte_registros_{datetime.now().date().isoformat()}.xlsx"

        return {
            "filename": filename,
            "content": output.read(),
            "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        }
        

    def _clean(self, name: str) -> str:
        """Elimina prefijos académicos/militares y normaliza espacios."""
        return PREFIX_RE.sub('', name).strip()
    
    
    def _best_name_score(self, input_name: str, candidates: list[str]) -> tuple[int, str]:
        """
        Retorna (mejor_score, nombre_candidato) comparando input_name
        contra cada nombre del listado usando token_sort_ratio, que maneja
        diferente orden de palabras (ej: 'Franco Carlos' vs 'Carlos Franco').
        """
        cleaned_input = self._clean(input_name).lower()
        best_score = 0
        best_match = ""
        for candidate in candidates:
            cleaned_candidate = self._clean(candidate).lower()
            score = fuzz.token_sort_ratio(cleaned_input, cleaned_candidate)
            if score > best_score:
                best_score = score
                best_match = candidate
        return best_score, best_match
    
    
    def _best_company_score(self, input_business: str) -> tuple[int, str]:
        """
        Compara input_business contra todas las empresas del whitelist.
        Retorna (mejor_score, empresa_key).
        """
        cleaned = input_business.strip().lower()
        best_score = 0
        best_key = ""
        for company in CONTACTS_BY_CLIENT:
            score = fuzz.token_sort_ratio(cleaned, company.lower())
            if score > best_score:
                best_score = score
                best_key = company
        return best_score, best_key
    
    
    # ---------------------------------------------------------------------------
    # Función principal de validación
    # ---------------------------------------------------------------------------
    
    def validate_contact(self, business: str, name: str) -> dict:
        """
        Valida si la persona (name) pertenece a la empresa (business)
        según el whitelist del evento.
    
        Retorna un dict con:
            - status:       'approved' | 'pending' | 'rejected'
            - company_score: score de coincidencia de empresa (0-100)
            - name_score:    score de coincidencia de nombre (0-100)
            - matched_company: empresa encontrada en el whitelist
            - matched_name:  nombre encontrado en el whitelist
        """
        company_score, matched_company = self._best_company_score(business)
    
        # Empresa no reconocida
        if company_score < 60:
            return {
                'status': 'rejected',
                'company_score': company_score,
                'name_score': 0,
                'matched_company': None,
                'matched_name': None,
            }
    
        candidates = CONTACTS_BY_CLIENT.get(matched_company, [])
        name_score, matched_name = self._best_name_score(name, candidates)
    
        # Lógica de decisión
        # Empresa clara (>= 85) + nombre claro (>= 80) → aprobado automático
        if company_score >= 85 and name_score >= 80:
            status = 'Enviado'
        # Empresa reconocible pero nombre con duda → revisión manual
        elif company_score >= 60 and name_score >= 60:
            status = 'Pendiente'
        else:
            status = 'Rechazado'
    
        return {
            'status': status,
            'company_score': company_score,
            'name_score': name_score,
            'matched_company': matched_company,
            'matched_name': matched_name,
        }


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


