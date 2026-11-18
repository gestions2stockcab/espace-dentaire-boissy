"""Télécharge les photos publiées par le cabinet sur sa fiche Google (pas celles des patients) dans photos-fiche/.
Lancé à la main (workflow « Photos de la fiche »), pour choisir les images du site."""
import json, os, re, urllib.parse, urllib.request

def env(k): return os.environ.get(k, "").strip()
def call(url, token=None, data=None):
    h = {"Authorization": f"Bearer {token}"} if token else {}
    body = urllib.parse.urlencode(data).encode() if data else None
    return json.load(urllib.request.urlopen(urllib.request.Request(url, data=body, headers=h), timeout=30))

tok = call("https://oauth2.googleapis.com/token", data={"client_id": env("GOOGLE_CLIENT_ID"), "client_secret": env("GOOGLE_CLIENT_SECRET"),
           "refresh_token": env("GOOGLE_REFRESH_TOKEN"), "grant_type": "refresh_token"})["access_token"]
fiche = json.load(open("boissy_fiche.json"))
os.makedirs("photos-fiche", exist_ok=True)
page, n, liste = "", 0, []
while True:
    d = call(f"https://mybusiness.googleapis.com/v4/accounts/{fiche['account']}/locations/{fiche['location']}/media?pageSize=100"
             + (f"&pageToken={page}" if page else ""), tok)
    for m in d.get("mediaItems", []):
        if m.get("mediaFormat") != "PHOTO" or not m.get("googleUrl"): continue
        cat = (m.get("locationAssociation") or {}).get("category", "AUTRE").lower()
        n += 1
        nom = f"photos-fiche/{n:02d}-{cat}.jpg"
        url = re.sub(r"=[^/]*$", "", m["googleUrl"]) + "=s2000"
        try:
            urllib.request.urlretrieve(url, nom)
        except Exception:
            urllib.request.urlretrieve(m["googleUrl"], nom)
        liste.append({"fichier": nom, "categorie": cat, "date": m.get("createTime"), "description": m.get("description", "")})
        print(nom, m.get("createTime", "")[:10], m.get("dimensions"))
    page = d.get("nextPageToken")
    if not page: break
json.dump(liste, open("photos-fiche/liste.json", "w"), ensure_ascii=False, indent=1)
print(f"{n} photo(s) du cabinet téléchargée(s)")
