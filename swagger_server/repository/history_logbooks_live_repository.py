from swagger_server.resources.databases.redis import RedisClient


class LogbookRepository:
    
    def __init__(self):
        self.redis_client = RedisClient()


    # def post_logbook_entry(self, logbook_entry_body: LogbookEntry, images, internal, external) -> None:
    #     pass