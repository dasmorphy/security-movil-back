import json
import pika

from swagger_server.config.access import access


class RabbitMQClient:

    EXCHANGE = "zentinel.events"

    def __init__(self):
        self.connection_params = self._connection_params()

    def get_credentials(self):
        response_json = access()
        return response_json["RABBITMQ"]

    def _connection_params(self):
        credentials = self.get_credentials()

        return pika.ConnectionParameters(
            host=credentials["HOST"],
            port=credentials["PORT"],
            virtual_host=credentials["VHOST"],
            credentials=pika.PlainCredentials(
                username=credentials["USER"],
                password=credentials["PASS"]
            ),
            heartbeat=60,
        )

    def send_event(self, routing_key: str, body: dict):

        connection = pika.BlockingConnection(
            self.connection_params
        )

        try:
            channel = connection.channel()

            channel.exchange_declare(
                exchange=self.EXCHANGE,
                exchange_type="topic",
                durable=True
            )

            channel.basic_publish(
                exchange=self.EXCHANGE,
                routing_key=routing_key,
                body=json.dumps(body),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=2,
                    headers={
                        "system": "zent-logbook-api" # Add a key/value header
                    }
                )
            )

        finally:
            connection.close()