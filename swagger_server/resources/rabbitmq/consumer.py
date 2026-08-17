import json
import pika

from swagger_server.config.access import access
from loguru import logger

from swagger_server.repository.user_repository import UserRepository
from swagger_server.uses_cases.user_use_case import UserUseCase


class NotificationConsumer:

    EXCHANGE = "zentinel.events"

    def __init__(self):
        credentials = access()["RABBITMQ"]
        user_repository = UserRepository()
        self.user_use_case = UserUseCase(user_repository)


        self.connection_params = pika.ConnectionParameters(
            host=credentials["HOST"],
            port=credentials["PORT"],
            virtual_host=credentials["VHOST"],
            credentials=pika.PlainCredentials(
                username=credentials["USER"],
                password=credentials["PASS"]
            ),
            heartbeat=60
        )

    def start(self):

        connection = pika.BlockingConnection(
            self.connection_params
        )

        channel = connection.channel()

        channel.exchange_declare(
            exchange=self.EXCHANGE,
            exchange_type="topic",
            durable=True
        )

        channel.queue_declare(
            queue="zentinel.logout.queue",
            durable=True
        )

        channel.queue_bind(
            exchange=self.EXCHANGE,
            queue="zentinel.logout.queue",
            routing_key="zentinel.logout.session"
        )


        channel.basic_qos(
            prefetch_count=1
        )

        channel.basic_consume(
            queue="zentinel.logout.queue",
            on_message_callback=self.logout_session,
            auto_ack=False
        )

        print("Notification consumer esperando mensajes...")

        channel.start_consuming()

    def logout_session(self, channel, method, properties, body):
        try:
            payload = json.loads(body)

            print("Evento recibido:")
            print(payload)

            self.logout(payload)

            channel.basic_ack(
                delivery_tag=method.delivery_tag
            )

        except Exception as error:
            external = payload.get("externalTransactionId")
            print(f"Error procesando evento: {error}")
            logger.error("Error procesando cola notificación: {}", str(error), internal=external, external=external)

            channel.basic_nack(
                delivery_tag=method.delivery_tag,
                requeue=False
            )

    def logout(self, payload):
        # notification_request = PushNotificationData.from_dict(payload.get("data"))
        self.user_use_case.logout(payload.get("channel"), payload.get("data"))
