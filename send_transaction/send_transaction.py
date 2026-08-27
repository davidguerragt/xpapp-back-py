
import sys
import warnings
import firebase_admin  
from firebase_admin import credentials, firestore, messaging 
from google.cloud.firestore_v1.base_query import FieldFilter


cred = credentials.Certificate("./secrets/service_account_key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# variable to hold the transaction ID
transactionId = "cxqra1QWHMXkwEORsONe"
userId = "david.guerra@gmail.com"


# Get the collection reference

from settings.constants import collections_transactions
collection_ref = db.collection(collections_transactions)
transaction = collection_ref.document(transactionId).get()
if not transaction.exists:
    print(f"Transaction with ID {transactionId} does not exist.")
    sys.exit(1)
transaction_data = transaction.to_dict()

# Get user ID from the users collection
collection_ref_users = db.collection("users")
user_info_doc = collection_ref_users.where(filter=FieldFilter("user", "==", userId)).limit(1).get()
if not user_info_doc:
    print(f"User with ID {userId} does not exist.")
    sys.exit(1)
user_data = user_info_doc[0].to_dict() or {}
tokens = user_data.get("tokens", [])

if user_data.get("user") != userId:
    sys.exit(f"User ID {userId} does not match the transaction's user ID {user_data.get('user')}.")

try:
    message_id = messaging.send_each_for_multicast(
        messaging.MulticastMessage(
            tokens=tokens,
            notification=messaging.Notification(
                title="Transaction Information",
                body=f"Your transaction {transactionId} has been processed."
            ),
            data={
                "view": "transaction_detail",
                "transactionId": transactionId,
                "total": str(transaction_data.get("total")),
            }
        )
    )
    print(f"Message sent with ID: {message_id}")
except messaging.UnregisteredError as e:
    user_collection_ref = db.collection("users")
    user_doc_ref = user_collection_ref.where(filter=FieldFilter("user", "==", userId)).limit(1).get()[0].reference
    user_doc_ref.update({
        "tokens": firestore.ArrayRemove([e.token])
    })
    sys.exit(f"Token {e.token} is unregistered and has been removed from the user's tokens.")

print (f"Transaction {transactionId} processed successfully for user {userId}.")
print(f"Message ID: {message_id}")