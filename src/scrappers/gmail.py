import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from server.producer import RabbitMQ_Producer
from models.queues import EventTypes
from server.mongo import db

emails_db = db['emails']


class GmailScrapper:
    def __init__(self):
        self.rabbit = RabbitMQ_Producer()
        credentials_path = os.path.join(os.path.dirname(__file__), 'gmail_credentials.json')
        # If modifying these scopes, delete the file token.json.
        SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

        self.creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when| the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            print("There is a token file")
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                print("Refreshing token")
                self.creds.refresh(Request())
            else:
                print("Request access token")
                flow = InstalledAppFlow.from_client_secrets_file(
                   credentials_path, SCOPES
                )
                self.creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                print("Token saved")
                token.write(self.creds.to_json())
    

    def listEmails(self, next_page_token=None):
        print("Listing emails...")
        try:
            service = build("gmail", "v1", credentials=self.creds)
            response = service.users().messages().list(userId="me", maxResults=500,includeSpamTrash="true", pageToken=next_page_token).execute()
            try:
                next_page_token = response['nextPageToken']
            except:
                next_page_token = None

            messages = response["messages"]

            if not messages:
                print("No mails found.")

            print(f"There are {len(messages)} mails")

            emails = []

            for email in messages:
                exists = emails_db.find_one({"emailId": email["id"]})
                if not exists:
                    emails.append({
                        "emailId": email["id"]
                    })
                    emails_db.insert_one({"emailId": email["id"]})

                    self.rabbit.sendToGmail({
                        "event": EventTypes.read_email.name,
                        "data": {"emailId":email["id"]}
                    })

            return {
                "emails":emails,
                "next_page_token":next_page_token,
            }
        except HttpError as error:
            print(f"An error occurred: {error}")

    def readEmail(self, emailId):
        try:
            service = build("gmail", "v1", credentials=self.creds)
            data = service.users().messages().get(userId="me", id=emailId).execute()
            headers = data["payload"]["headers"]
            subject = ""
            fromEmail = ""
            toEmail = ""
            date = ""
            body = ""
            for header in headers:
                if "Subject" in header["name"]:
                    subject = header["value"]
                elif "Date" in header["name"]:
                    date = header["value"]
                elif "From" in header["name"]:
                    fromEmail = header["value"]   
                elif "To" in header["name"]:
                    toEmail = header["value"]    
            
            try:
                parts = data["payload"]["parts"]
                body = parts[0]["body"]["data"]
                body = base64.urlsafe_b64decode(body)
            except Exception as e:
                print(f"Error parsing body {e}")
            
            response = {
                "to": toEmail,
                "from": fromEmail,
                "date": date,
                "subject": subject,
                "body": body,
                "status": "COMPLETED"
            }

            emails_db.find_one_and_update(
                {'emailId': emailId},           # Filtro para encontrar el documento
                {'$set': response}, 
            )
            print(f"Email {emailId} saved")
            return response
        except HttpError as error:
            print(f"Error reading email: {error}")
            emails_db.find_one_and_update(
                {'emailId': emailId},           # Filtro para encontrar el documento
                {'$set': {"status": "ERROR"}}, 
            )