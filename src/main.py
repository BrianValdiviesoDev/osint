from scrappers.gmail import GmailScrapper
from server.mongo import db
from server.consumer import RabbitMQ_Consumer
from server.producer import RabbitMQ_Producer
from models.queues import EventTypes
emails_db = db['emails']

def listEmails():
    try:
        rabbitProducer = RabbitMQ_Producer()
        gmail = GmailScrapper()
        next_page_token = None
        emails_read = 0
        while emails_read < 1 or next_page_token != None: 
            response = gmail.listEmails(next_page_token=next_page_token)
            next_page_token = response["next_page_token"]
            emails_db.insert_many(response["emails"])
            for email in response["emails"]:
                rabbitProducer.sendToGmail({
                    "event": EventTypes.read_email.name,
                    "data": {"emailId":email["emailId"]}
                })
            print(f"Emails read: {emails_read} , Next page: {next_page_token}")
    except Exception as e:
        print(f"Error: {e}")

def readEmail():
    try:
        emailId= "18f95cfbb7617da7"
        gmail = GmailScrapper()
        response = gmail.readEmail(emailId=emailId)
        print(response)
        saved = emails_db.find_one_and_update(
            {'emailId': emailId},           # Filtro para encontrar el documento
            {'$set': response}, 
        )
        print(f"SAVED: {saved}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == '__main__':
    rabbit = RabbitMQ_Consumer()
    #listEmails()
    #readEmail()