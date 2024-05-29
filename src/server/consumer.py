import os
import pika
import json
from dotenv import load_dotenv
from models.queues import EventTypes, QueueEvent
from scrappers.gmail import GmailScrapper
from server.mongo import db
import os
emails_db = db['emails']
load_dotenv()

rabbit_host = os.environ.get("RABBITMQ_HOST")
rabbit_port = os.environ.get("RABBITMQ_PORT")
rabbit_user = os.environ.get("RABBITMQ_USER")
rabbit_pass = os.environ.get("RABBITMQ_PASS")
gmail_queue = os.environ.get("GMAIL_QUEUE")

class RabbitMQ_Consumer:

    def __init__(self):
        credentials = pika.PlainCredentials(rabbit_user, rabbit_pass)
        parameters = pika.ConnectionParameters(host=rabbit_host, port=rabbit_port, credentials=credentials)
        connection = pika.BlockingConnection(parameters)
        
        self.gmail = GmailScrapper()
        
        self.channel = connection.channel()
        self.consume()



    def consume(self):
        self.channel.queue_declare(queue=gmail_queue, durable=True)
        
        def callback(ch, method, properties, body):
            try:           
                message = body.decode()
                content = json.loads(message)
                print(f"NEW MESSAGE: {message}")

                if content['event'] == EventTypes.read_email.name:
                    emailId = content['data']['emailId']
                    self.gmail.readEmail(emailId=emailId)

                if content['event'] == EventTypes.list_emails.name:
                    next_page_token = None
                    emails_read = 0
                    while emails_read < 1 or next_page_token != None: 
                        response = self.gmail.listEmails(next_page_token=next_page_token)
                        next_page_token = response["next_page_token"]
                        print(f"Emails read: {emails_read} , Next page: {next_page_token}")
            except Exception as e:
                print(f"Error: {e}")        

        self.channel.basic_consume(queue=gmail_queue, on_message_callback=callback, auto_ack=True)
        self.channel.start_consuming()

    def close_connection(self):
        self.channel.stop_consuming()
        self.connection.close()