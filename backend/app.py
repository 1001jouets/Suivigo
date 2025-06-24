from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

STATUT_LIVRE_MOTS_CLES = [
    "livré", "remis", "votre colis est livré", "delivered", "delivré", "livree"
]

def contient_livraison(text):
    text = text.lower()
    return any(mot in text for mot in STATUT_LIVRE_MOTS_CLES)

@app.route("/track")
def track():
    num = request.args.get("num", "").strip()
    if not num:
        return jsonify({"error": "Aucun numéro de suivi fourni."}), 400

    num = num.upper()
    transporteur = "Inconnu"

    # Détection du transporteur
    if re.match(r"^CB\d{9}FR$", num) or re.match(r"^6A\d{11}$", num):
        transporteur = "Colissimo"
    elif re.match(r"^JJD\d{20,24}$", num):
        transporteur = "DHL"
    elif re.match(r"^[A-Z]{2}\d{9}[A-Z]{2}$", num):
        transporteur = "Chronopost"
    elif re.match(r"^(?:100|0|01|015|053|019|134)\d{11,12}$", num):
        transporteur = "DPD"
    elif re.match(r"^318\d{6}$", num):
        transporteur = "Agediss"
    elif re.match(r"^(?:\d{12}|\d{15}|\d{20})$", num):
        transporteur = "FedEx"
    elif re.match(r"^\d{11}$", num):
        transporteur = "GLS"

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        # GLS
        if transporteur == "GLS":
            gls_url = f"https://gls-group.eu/EU/en/parcel-tracking?match={num}"
            message_client = (
                f"Votre colis est pris en charge par {transporteur} et sera livré dans les prochains jours. "
                f"Vous pouvez consulter le suivi ici : {gls_url}"
            )
            return jsonify({"transporteur": transporteur, "tracking": num, "lien": gls_url, "message_client": message_client})

        # Colissimo
        if transporteur == "Colissimo":
            url = f"https://www.laposte.fr/outils/suivre-vos-envois?code={num}"
            message_client = (
                f"Votre colis est pris en charge par {transporteur} et sera livré dans les prochains jours. "
                f"Vous pouvez consulter le suivi ici : {url}"
            )
            return jsonify({"transporteur": transporteur, "tracking": num, "lien": url, "message_client": message_client})

        # DHL
        if transporteur == "DHL":
            url = f"https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={num}"
            message_client = (
                f"Votre colis est pris en charge par {transporteur} et sera livré dans les prochains jours. "
                f"Vous pouvez consulter le suivi ici : {url}"
            )
            return jsonify({"transporteur": transporteur, "tracking": num, "lien": url, "message_client": message_client})

        # DPD
        if transporteur == "DPD":
            url = f"https://www.dpdgroup.com/be/mydpd/my-parcels/incoming?parcelNumber={num}"
            message_client = (
                f"Votre colis est pris en charge par {transporteur} et sera livré dans les prochains jours. "
                f"Vous pouvez consulter le suivi ici : {url}"
            )
            return jsonify({"transporteur": transporteur, "tracking": num, "lien": url, "message_client": message_client})

        # FedEx
        if transporteur == "FedEx":
            url = f"https://www.fedex.com/fedextrack/?tracknumbers={num}"
            message_client = (
                f"Votre colis est pris en charge par {transporteur} et sera livré dans les prochains jours. "
                f"Vous pouvez consulter le suivi ici : {url}"
            )
            return jsonify({"transporteur": transporteur, "tracking": num, "lien": url, "message_client": message_client})

        # Chronopost
        if transporteur == "Chronopost":
            url = f"https://www.chronopost.fr/tracking-no-cms/suivi-page?listeNumerosLT={num}"
            message_client = (
                f"Votre colis est pris en charge par {transporteur} et sera livré dans les prochains jours. "
                f"Vous pouvez consulter le suivi ici : {url}"
            )
            return jsonify({"transporteur": transporteur, "tracking": num, "lien": url, "message_client": message_client})

        # Agediss
        if transporteur == "Agediss":
            url = f"https://www.agediss.com/fr/suivi/{num}"
            message_client = (
                f"Votre colis est pris en charge par {transporteur} et sera livré dans les prochains jours. "
                f"Vous pouvez consulter le suivi ici : {url}"
            )
            return jsonify({"transporteur": transporteur, "tracking": num, "lien": url, "message_client": message_client})

    except Exception as e:
        return jsonify({"error": f"Erreur {transporteur}: {str(e)}"}), 500

    # Fallback
    url_fallback = f"https://www.google.com/search?q=suivi+colis+{num}"
    message_client = (
        f"Votre colis est pris en charge par {transporteur} et sera livré dans les prochains jours. "
        f"Vous pouvez consulter le suivi ici : {url_fallback}"
    )
    return jsonify({"transporteur": transporteur, "tracking": num, "lien": url_fallback, "message_client": message_client})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
