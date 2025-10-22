from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.cloud import firestore

app = FastAPI()

GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASS = os.environ.get("GMAIL_PASS")
API_KEY = os.environ.get("API_KEY")


# Connexion Firestore
db = firestore.Client.from_service_account_json("firebase-key.json")

# Schéma de données pour la requête POST
class EmailRequest(BaseModel):
    key: str
    template: str
    to: str
    variables: dict

@app.post("/send-email")
async def send_email(data: EmailRequest):
    # Vérifier la clé
    if data.key != API_KEY:
        return JSONResponse(content={"error": "Clé API invalide"}, status_code=401)
    
    # Récupérer le modèle dans Firestore
    doc = db.collection("email_templates").document(data.template).get()
    if not doc.exists:
        return {"status": "error", "message": "Modèle introuvable"}
    
    html = doc.to_dict().get("html", "")
    subject = doc.to_dict().get("subject", "Message automatique")

    # Remplacer les {{variables}}
    for key, value in data.variables.items():
        html = html.replace(f"{{{{{key}}}}}", str(value))

    msg = MIMEMultipart("alternative")
    msg["From"] = expediteur
    msg["To"] = data.to
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as serveur:
            serveur.starttls()
            serveur.login(expediteur, mot_de_passe)
            serveur.send_message(msg)
        return {"status": "success", "sent_to": data.to}
    except Exception as e:
        return {"status": "error", "message": str(e)}
