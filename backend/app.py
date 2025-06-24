from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
CORS(app)

# Mots-clés pour détecter le statut Livré
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
    elif re.match(r"^(?:100|0|053|019|134)\d{11}$", num):
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
            r = requests.get(gls_url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            statut = soup.select_one(".status")
            historique = [el.text.strip() for el in soup.select(".history")]
            if not statut and contient_livraison(r.text):
                statut = "Livré"
            text_statut = statut.text.strip() if getattr(statut, 'text', None) else (statut or ("Livré" if contient_livraison(r.text) else ""))
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": text_statut, "date_livraison": "", "historique": historique, "lien": gls_url})

        # Colissimo
        if transporteur == "Colissimo":
            url = f"https://www.laposte.fr/outils/suivre-vos-envois?code={num}"
            r = requests.get(url, headers=headers)
            statut = "Livré" if contient_livraison(r.text) else ""
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": statut, "date_livraison": "", "historique": [], "lien": url})

        # DHL
        if transporteur == "DHL":
            url = f"https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={num}"
            r = requests.get(url, headers=headers)
            statut = "Livré" if contient_livraison(r.text) else ""
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": statut, "date_livraison": "", "historique": [], "lien": url})

        # DPD
        if transporteur == "DPD":
            url = f"https://www.dpdgroup.com/be/mydpd/my-parcels/incoming?parcelNumber={num}"
            r = requests.get(url, headers=headers)
            statut = "Livré" if contient_livraison(r.text) else ""
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": statut, "date_livraison": "", "historique": [], "lien": url})

        # FedEx
        if transporteur == "FedEx":
            url = f"https://www.fedex.com/fedextrack/?tracknumbers={num}"
            r = requests.get(url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            statut_el = soup.select_one(".statusChevron")
            historique = [el.text.strip() for el in soup.select(".statusBar")]
            if not statut_el and contient_livraison(r.text): statut_el = "Livré"
            text_statut = statut_el.text.strip() if getattr(statut_el, 'text', None) else (statut_el or ("Livré" if contient_livraison(r.text) else ""))
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": text_statut, "date_livraison": "", "historique": historique, "lien": url})

        # Chronopost
        if transporteur == "Chronopost":
            url = f"https://www.chronopost.fr/tracking-no-cms/suivi-page?listeNumerosLT={num}"
            r = requests.get(url, headers=headers)
            statut = "Livré" if contient_livraison(r.text) else ""
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": statut, "date_livraison": "", "historique": [], "lien": url})

        # Agediss
        if transporteur == "Agediss":
            url = f"https://www.agediss.com/fr/suivi/{num}"
            r = requests.get(url, headers=headers)
            statut = "Livré" if contient_livraison(r.text) else ""
            return jsonify({"transporteur": transporteur, "tracking": num, "statut": statut, "date_livraison": "", "historique": [], "lien": url})

    except Exception as e:
        return jsonify({"error": f"Erreur {transporteur}: {str(e)}"}), 500

    # Fallback
    url_fallback = f"https://www.google.com/search?q=suivi+colis+{num}"
    return jsonify({"transporteur": transporteur, "tracking": num, "statut": "", "date_livraison": "", "historique": [], "lien": url_fallback})

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
