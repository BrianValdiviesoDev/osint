import os
import pika
import json
from dotenv import load_dotenv
from models.queues import QueueEvent

load_dotenv()

rabbit_host = os.environ.get("RABBITMQ_HOST")
rabbit_port = os.environ.get("RABBITMQ_PORT")
rabbit_user = os.environ.get("RABBITMQ_USER")
rabbit_pass = os.environ.get("RABBITMQ_PASS")
gmail_queue = os.environ.get("GMAIL_QUEUE")

class RabbitMQ_Producer:

    def __init__(self):
        credentials = pika.PlainCredentials(rabbit_user, rabbit_pass)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_host, port=rabbit_port, credentials=credentials))
        self.channel = connection.channel()

    def sendToGmail(self, message:QueueEvent, queue:str=gmail_queue):
        string = json.dumps(message)
        print(f"Send {string} TO {queue}")
        self.channel.queue_declare(queue=queue, durable=True)
        self.channel.basic_publish(exchange='', routing_key=queue, body=string)