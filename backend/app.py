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
    if num.startswith("CB") and num.endswith("FR") and len(num) == 13:
        transporteur = "Colissimo"
    elif num.startswith("6A") and len(num) == 13:
        transporteur = "Colissimo"
    elif num.startswith("JJD"):
        transporteur = "DHL"
    elif re.match(r"^X[A-Z0-9]{13}$", num):
        transporteur = "Chronopost"
    elif re.match(r"^100\d{11}$", num) or re.match(r"^0\d{13}$", num) or re.match(r"^053\d{11}$", num) or re.match(r"^019\d{11}$", num) or re.match(r"^134\d{11}$", num):
        transporteur = "DPD"
    elif re.match(r"^318\d{6}$", num):
        transporteur = "Agediss"
    elif re.match(r"^\d{11}$", num):
        transporteur = "GLS"
    elif len(num) in [15, 20] and num.isdigit():
        transporteur = "FedEx"
    elif re.match(r"^[A-Z0-9]{8,}$", num) and not num.startswith("JJD"):
        transporteur = "GLS"

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        if transporteur == "GLS":
            gls_url = f"https://gls-group.eu/EU/en/parcel-tracking?match={num}"
            r = requests.get(gls_url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            statut = soup.select_one(".status")
            historique = [el.text.strip() for el in soup.select(".history")]
            if not statut and contient_livraison(r.text):
                statut = "Livré"
            return jsonify({
                "transporteur": transporteur,
                "tracking": num,
                "statut": statut.text.strip() if hasattr(statut, 'text') else statut if statut else "Livré" if contient_livraison(r.text) else "",
                "date_livraison": "",
                "historique": historique,
                "lien": gls_url
            })

        if transporteur == "Colissimo":
            colissimo_url = f"https://www.laposte.fr/outils/suivre-vos-envois?code={num}"
            r = requests.get(colissimo_url, headers=headers)
            statut = "Livré" if contient_livraison(r.text) else ""
            return jsonify({
                "transporteur": transporteur,
                "tracking": num,
                "statut": statut,
                "date_livraison": "",
                "historique": [],
                "lien": colissimo_url
            })

        if transporteur == "DHL":
            dhl_url = f"https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={num}"
            r = requests.get(dhl_url, headers=headers)
            statut = "Livré" if contient_livraison(r.text) else ""
            return jsonify({
                "transporteur": transporteur,
                "tracking": num,
                "statut": statut,
                "date_livraison": "",
                "historique": [],
                "lien": dhl_url
            })

        if transporteur == "DPD":
            dpd_url = f"https://www.dpdgroup.com/be/mydpd/my-parcels/incoming?parcelNumber={num}"
            r = requests.get(dpd_url, headers=headers)
            statut = "Livré" if contient_livraison(r.text) else ""
            return jsonify({
                "transporteur": transporteur,
                "tracking": num,
                "statut": statut,
                "date_livraison": "",
                "historique": [],
                "lien": dpd_url
            })

        if transporteur == "FedEx":
            fedex_url = f"https://www.fedex.com/fedextrack/?tracknumbers={num}"
            r = requests.get(fedex_url, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            statut = soup.select_one(".statusChevron")
            historique = [el.text.strip() for el in soup.select(".statusBar")]
            if not statut and contient_livraison(r.text):
                statut = "Livré"
            return jsonify({
                "transporteur": transporteur,
                "tracking": num,
                "statut": statut.text.strip() if hasattr(statut, 'text') else statut if statut else "Livré" if contient_livraison(r.text) else "",
                "date_livraison": "",
                "historique": historique,
                "lien": fedex_url
            })

        if transporteur == "Chronopost":
            chrono_url = f"https://www.chronopost.fr/tracking-no-cms/suivi-page?listeNumerosLT={num}"
            r = requests.get(chrono_url, headers=headers)
            statut = "Livré" if contient_livraison(r.text) else ""
            return jsonify({
                "transporteur": transporteur,
                "tracking": num,
                "statut": statut,
                "date_livraison": "",
                "historique": [],
                "lien": chrono_url
            })

        if transporteur == "Agediss":
            agediss_url = f"https://www.agediss.com/fr/suivi/{num}"
            r = requests.get(agediss_url, headers=headers)
            statut = "Livré" if contient_livraison(r.text) else ""
            return jsonify({
                "transporteur": transporteur,
                "tracking": num,
                "statut": statut,
                "date_livraison": "",
                "historique": [],
                "lien": agediss_url
            })

    except Exception as e:
        return jsonify({"error": f"Erreur {transporteur}: {str(e)}"}), 500

    lien_defaut = {
        "Colissimo": f"https://www.laposte.fr/outils/suivre-vos-envois?code={num}",
        "DHL": f"https://www.dhl.de/de/privatkunden/pakete-empfangen/verfolgen.html?piececode={num}",
        "DPD": f"https://www.dpdgroup.com/be/mydpd/my-parcels/incoming?parcelNumber={num}",
        "GLS": f"https://gls-group.eu/EU/en/parcel-tracking?match={num}",
        "FedEx": f"https://www.fedex.com/fedextrack/?tracknumbers={num}",
        "Chronopost": f"https://www.chronopost.fr/tracking-no-cms/suivi-page?listeNumerosLT={num}",
        "Agediss": f"https://www.agediss.com/fr/suivi/{num}"
    }.get(transporteur, f"https://www.google.com/search?q=suivi+colis+{num}")

    return jsonify({
        "transporteur": transporteur,
        "tracking": num,
        "statut": "",
        "date_livraison": "",
        "historique": [],
        "lien": lien_defaut
    })

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
