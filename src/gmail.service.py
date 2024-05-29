from server.mongo import db
from server.producer import RabbitMQ_Producer
from models.queues import EventTypes
from bson import ObjectId
emails_db = db["emails"]
def getPendingEmails():
    rabbit = RabbitMQ_Producer()
    pendings = emails_db.find({"to":{"$exists":False}})
    for pending in pendings:
        exists = emails_db.find_one({"emailId":pending["emailId"], "to":{"$exists":True}, "status":{"$ne":"ERROR"}})
        if not exists:
            rabbit.sendToGmail({
                "event": EventTypes.read_email.name,
                "data":{
                    "emailId":pending["emailId"]
                }
            })
        else:
            emails_db.delete_one({"_id":pending["_id"]})




if __name__ == '__main__':
    getPendingEmails()