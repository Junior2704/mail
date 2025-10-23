import os
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib

app = FastAPI()

# Autoriser toutes les origines (pour test)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables d'environnement
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

if not SMTP_USER or not SMTP_PASS:
    raise RuntimeError("Définir SMTP_USER et SMTP_PASS dans les variables d'environnement")

# Templates
templates = {
    "CR": """
    <html>
    <body style="font-family: Arial, sans-serif; color:#333;">
        <p>Bonjour {{patient_prenom}} {{patient_nom}},</p>
        <p>Votre compte-rendu d’hospitalisation est disponible :</p>
        <p><a href="{{lien_compte_rendu}}">{{lien_compte_rendu}}</a></p>
        <p>⚠️ Ce document est valable 7 jours.</p>
    </body>
    </html>
    """
}

@app.post("/")
async def send_email(request: Request):
    data = await request.json()
    key = data.get("key")
    template_name = data.get("template")
    to_email = data.get("to")
    variables = data.get("variables", {})

    # Vérification clé API
    if key != "10876":
        raise HTTPException(status_code=401, detail="Clé API invalide")

    html_template = templates.get(template_name)
    if not html_template:
        raise HTTPException(status_code=400, detail="Template non trouvé")

    # Remplacement des variables
    for k, v in variables.items():
        html_template = html_template.replace(f"{{{{{k}}}}
