"""Conseil du mois — Espace dentaire Boissy (indépendant de Savigny et Malakoff).
1) choisit la fiche conseil suivante (ordre ci-dessous) ;
2) la publie en « actualité » sur la fiche Google Boissy (sauf PAS_GOOGLE=1) ;
3) crée l'article du mois sur le site (FR + EN), met à jour la page Actualités et le sitemap.
actu_last.json mémorise le dernier mois publié. Secrets : ceux de avis.yml."""
import datetime as dt, html as H, json, os, re, sys, urllib.parse, urllib.request

SITE = "https://espacedentaireboissy.fr/"
ORDRE = ["gencives", "enfants", "sensibilite", "mauvaise-haleine", "tabac", "diabete", "sport-protege-dents", "grossesse",
         "apres-detartrage", "blanchiment", "gouttiere-bruxisme", "apres-soin-carie", "couronne-provisoire",
         "apres-devitalisation", "apres-implant", "apres-extraction", "prothese-amovible", "apres-couronne"]
MOIS_FR = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
MOIS_EN = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]

def env(k): return os.environ.get(k, "").strip().strip('"').strip("'").strip()

def lire(slug, en=False):
    s = open(f"{'en/' if en else ''}c/conseil-{slug}/index.html", encoding="utf-8").read()
    titre = H.unescape(re.sub(r"<[^>]+>", "", re.search(r"<h1>(.*?)</h1>", s, re.S).group(1))).strip()
    chap = H.unescape(re.sub(r"<[^>]+>", "", re.search(r'<p class="chapeau-article">(.*?)</p>', s, re.S).group(1))).strip()
    puces = [H.unescape(re.sub(r"<[^>]+>", "", x)).strip() for x in re.findall(r"<li>(.*?)</li>", s[s.find('class="chapeau-article"'):s.find('class="sources"')], re.S)]
    return {"titre": titre, "chapeau": chap, "puces": puces}

def page(slug, en, title, desc, h1, crumbs, body):
    tpl = open(f"{'en/' if en else ''}c/honoraires/index.html", encoding="utf-8").read()
    pre = "../../../en/" if en else "../../"
    root = "../../../" if en else "../../"
    url_fr, url_en = f"{SITE}c/{slug}/", f"{SITE}en/c/{slug}/"
    e = H.escape
    s = tpl.replace(f"{SITE}c/honoraires/", url_fr).replace(f"{SITE}en/c/honoraires/", url_en)
    s = re.sub(r"<title>.*?</title>", lambda m: f"<title>{e(title)}</title>", s, count=1)
    for k in ('name="description"', 'property="og:title"', 'property="og:description"'):
        v = desc if "desc" in k else title
        s = re.sub(rf'<meta {k} content="[^"]*">', lambda m: f'<meta {k} content="{e(v)}">', s, count=1)
    home = "Home" if en else "Accueil"
    items = [{"@type": "ListItem", "position": 1, "name": home, "item": SITE + ("en/" if en else "")}]
    for cs, cl in crumbs:
        items.append({"@type": "ListItem", "position": len(items) + 1, "name": cl, "item": SITE + ("en/" if en else "") + f"c/{cs}/"})
    items.append({"@type": "ListItem", "position": len(items) + 1, "name": h1})
    bc = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}, ensure_ascii=False) + "</script>"
    s = re.sub(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "BreadcrumbList".*?</script>', lambda m: bc, s, count=1)
    fil = f'<a href="{root}{"en/" if en else "./"}">{home}</a> / ' + "".join(f'<a href="{pre}c/{cs}/">{cl}</a> / ' for cs, cl in crumbs) + f'<span aria-current="page">{e(h1)}</span>'
    main = (f'<main id="contenu"><div class="page on" data-page="{slug}" data-title="{e(title)}">\n'
            f'<div class="page-titre pt-attente"><div class="wrap"><nav class="fil" aria-label="{"Breadcrumb" if en else "Fil d’Ariane"}">{fil}</nav><h1>{e(h1)}</h1></div></div>\n'
            f'<section style="padding-top:32px"><div class="wrap"><div class="contenu">\n{body}\n</div></div></section>\n</div></main>')
    s = re.sub(r'<main id="contenu">.*?</main>', lambda m: main, s, count=1, flags=re.S)
    s = re.sub(r'(<nav class="lang-sw".*?</nav>)', lambda m: m.group(1).replace("c/honoraires/", f"c/{slug}/"), s, flags=re.S)
    d = f"{'en/' if en else ''}c/{slug}"
    os.makedirs(d, exist_ok=True)
    open(f"{d}/index.html", "w", encoding="utf-8").write(s)

def rendre(arts):
    """Pages d'articles + page Actualités (FR/EN) + bloc Actualités de l'accueil + sitemap."""
    extra = json.load(open("articles.json", encoding="utf-8")) if os.path.exists("articles.json") else []
    for en in (False, True):
        pre = "../../../en/" if en else "../../"
        entrees = []  # (date de tri, slug, libellé, date affichée)
        for a in arts:
            f = lire(a["slug"], en)
            an, mo = int(a["mois"][:4]), int(a["mois"][5:])
            lab = (f"{MOIS_EN[mo-1]} {an} tip" if en else f"Conseil de {MOIS_FR[mo-1]} {an}")
            slug = f"actu-{a['mois']}-{a['slug']}"
            h1 = f"{lab}: {f['titre']}" if en else f"{lab} : {f['titre']}"
            body = (f'<p class="chapeau-article">{H.escape(f["chapeau"])}</p>'
                    + ("<h2>Key advice</h2>" if en else "<h2>Les conseils essentiels</h2>")
                    + "<ul>" + "".join(f"<li>{H.escape(p)}</li>" for p in f["puces"][:4]) + "</ul>"
                    + f'<p><a class="btn btn-trait" href="{pre}c/conseil-{a["slug"]}/">{"Read the full advice sheet" if en else "Lire la fiche complète"}</a></p>'
                    + f'<p class="avert">{"This is general advice and does not replace your practitioner’s instructions." if en else "Ces conseils sont généraux et ne remplacent pas les consignes données par votre praticien."}</p>')
            page(slug, en, f"{h1} | Espace dentaire Boissy", f["chapeau"], h1,
                 [("actualites", "News" if en else "Actualités")], body)
            entrees.append((a.get("date", a["mois"] + "-01"), slug, h1, f"{MOIS_EN[mo-1]} {an}" if en else f"{MOIS_FR[mo-1].capitalize()} {an}"))
        for x in extra:  # articles rédigés (pages déjà présentes)
            y, m, d = x["date"].split("-")
            dd = f"{int(d)} {MOIS_EN[int(m)-1]} {y}" if en else f"{int(d)} {MOIS_FR[int(m)-1]} {y}"
            entrees.append((x["date"], x["slug"], x["titre_en"] if en else x["titre"], dd))
        entrees.sort(reverse=True)
        body = ("<p class=\"chapeau-article\">" + ("Articles and a monthly tip from the centre to keep your teeth and gums healthy." if en else "Articles et conseil du mois : les infos du centre pour garder des dents et des gencives en bonne santé.") + "</p>"
                + '<ul class="liens-liste">' + "".join(f'<li><a href="{pre}c/{s_}/"><span>{H.escape(t)}</span><span aria-hidden="true">›</span></a></li>' for _, s_, t, _d in entrees) + "</ul>")
        page("actualites", en, ("News" if en else "Actualités") + " | Espace dentaire Boissy-Saint-Léger",
             "Articles and a monthly tip from Espace dentaire Boissy to keep your teeth and gums healthy." if en else "Articles et conseil du mois de l’Espace dentaire Boissy pour garder des dents et des gencives en bonne santé.",
             "News" if en else "Actualités", [], body)
        # bloc de l'accueil
        hp = "en/index.html" if en else "index.html"
        hs = open(hp, encoding="utf-8").read()
        hpre = "../en/" if en else ""
        bloc = ('<section class="actu-home"><div class="wrap"><div class="chapeau"><h2>' + ("News" if en else "Actualités") + '</h2></div><div class="grille">'
                + "".join(f'<a class="carte" href="{hpre}c/{s_}/"><h3>{H.escape(t)}</h3><p>{d_}</p></a>' for _, s_, t, d_ in entrees[:3])
                + f'</div><p style="margin-top:28px"><a class="btn btn-trait" href="{hpre}c/actualites/">' + ("All news" if en else "Toutes les actualités") + "</a></p></div></section>\n")
        if '<section class="actu-home">' in hs:
            hs = re.sub(r'<section class="actu-home">.*?</section>\n', lambda m: bloc, hs, count=1, flags=re.S)
        else:
            hs = hs.replace('<section class="cp-home">', bloc + '<section class="cp-home">', 1)
        open(hp, "w", encoding="utf-8").write(hs)
    # sitemap
    sm = open("sitemap.xml", encoding="utf-8").read()
    for slug in ["actualites"] + [f"actu-{a['mois']}-{a['slug']}" for a in arts] + [x["slug"] for x in extra]:
        if f"{SITE}c/{slug}/</loc>" in sm: continue
        u, ue = f"{SITE}c/{slug}/", f"{SITE}en/c/{slug}/"
        x = f'<url><loc>{u}</loc><xhtml:link rel="alternate" hreflang="fr" href="{u}"/><xhtml:link rel="alternate" hreflang="en" href="{ue}"/><priority>0.6</priority></url>\n'
        xe = f'<url><loc>{ue}</loc><xhtml:link rel="alternate" hreflang="fr" href="{u}"/><xhtml:link rel="alternate" hreflang="en" href="{ue}"/><priority>0.5</priority></url>\n'
        sm = sm.replace("</urlset>", x + xe + "</urlset>")
    open("sitemap.xml", "w", encoding="utf-8").write(sm)

def call(url, data=None, token=None, method=None):
    h = {"Accept": "application/json"}; body = None
    if token: h["Authorization"] = f"Bearer {token}"
    if isinstance(data, dict) and token: h["Content-Type"] = "application/json"; body = json.dumps(data).encode()
    elif data: body = urllib.parse.urlencode(data).encode()
    try: return json.load(urllib.request.urlopen(urllib.request.Request(url, data=body, headers=h, method=method), timeout=40))
    except urllib.error.HTTPError as e: sys.exit(f"Erreur Google {e.code} : {e.read().decode()[:600]}")

if __name__ == "__main__":
    arts = json.load(open("actualites.json")) if os.path.exists("actualites.json") else []
    if os.environ.get("MODE") == "rendre":
        rendre(arts); print("Rendu :", len(arts), "article(s)"); sys.exit(0)
    mois = dt.date.today().strftime("%Y-%m")
    last = json.load(open("actu_last.json")) if os.path.exists("actu_last.json") else {"mois": None, "n": -1}
    if last.get("mois") == mois and env("FORCER") != "1":
        print("Déjà publié ce mois-ci :", mois); sys.exit(0)
    liste = [s for s in ORDRE if os.path.exists(f"c/conseil-{s}/index.html")]
    n = (last.get("n", -1) + 1) % len(liste)
    slug = liste[n]
    f = lire(slug)
    post_name = None
    if env("PAS_GOOGLE") != "1":
        fiche = json.load(open("boissy_fiche.json"))
        puces = "\n".join("• " + c for c in f["puces"][:3])
        # règles Google : ni téléphone ni e-mail dans le texte
        texte = (f"Conseil du mois : {f['titre']}\n\n{f['chapeau']}\n\n{puces}\n\nLa fiche complète est sur notre site.")[:1450]
        tok = call("https://oauth2.googleapis.com/token", {"client_id": env("GOOGLE_CLIENT_ID"), "client_secret": env("GOOGLE_CLIENT_SECRET"),
                   "refresh_token": env("GOOGLE_REFRESH_TOKEN"), "grant_type": "refresh_token"})["access_token"]
        base = f"https://mybusiness.googleapis.com/v4/accounts/{fiche['account']}/locations/{fiche['location']}/localPosts"
        r = call(base, {"languageCode": "fr", "topicType": "STANDARD", "summary": texte,
                        "callToAction": {"actionType": "LEARN_MORE", "url": f"{SITE}c/actu-{mois}-{slug}/"},
                        "media": [{"mediaFormat": "PHOTO", "sourceUrl": f"{SITE}assets/og.jpg"}]}, tok, "POST")
        post_name = r.get("name"); print("Publié sur Google :", f["titre"], "| état :", r.get("state"))
    json.dump({"mois": mois, "n": n, "slug": slug, "post": post_name}, open("actu_last.json", "w"))
    if not any(a["mois"] == mois for a in arts):
        arts.append({"mois": mois, "date": str(dt.date.today()), "slug": slug})
        json.dump(arts, open("actualites.json", "w"), ensure_ascii=False)
    rendre(arts); print("Article du mois :", slug)
