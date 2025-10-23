import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI()

# Autoriser toutes les origines (pour test)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou liste des domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Récupération des variables d'environnement
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASS = os.environ.get("SMTP_PASS")
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))

# Vérification minimale
if not SMTP_USER or not SMTP_PASS:
    raise RuntimeError("Veuillez définir SMTP_USER et SMTP_PASS dans les variables d'environnement.")

# Modèles de mail (clé = nom du template)
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

@app.post("/send-email")
async def send_email(request: Request):
    try:
        data = await request.json()
        key = data.get("key")
        template_name = data.get("template")
        to_email = data.get("to")
        variables = data.get("variables", {})

        # Vérification de la clé d'API interne
        if key != "10876":
            raise HTTPException(status_code=401, detail="Clé API invalide")

        # Vérification du template
        html_template = templates.get(template_name)
        if not html_template:
            raise HTTPException(status_code=400, detail="Template non trouvé")

        # Remplacement des variables
        for k, v in variables.items():
            html_template = html_template.replace(f"{{{{{k}}}}}", v)

        # Préparer le mail
        message = MIMEMultipart("alternative")
        message["From"] = SMTP_USER
        message["To"] = to_email
        message["Subject"] = "Votre compte-rendu d’hospitalisation"

        part = MIMEText(html_template, "html")
        message.attach(part)

        # Envoi via SMTP avec TLS
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            start_tls=True,
            username=SMTP_USER,
            password=SMTP_PASS
        )

        return {"status": "success", "message": "Email envoyé avec succès !"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
