from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import os
import re
import time
import json
import html as html_lib
import httpx
import resend
from datetime import datetime, timedelta, timezone
try:
    from zoneinfo import ZoneInfo
    LOCAL_TZ = ZoneInfo("Europe/Paris")
except Exception:  # pas de base de fuseaux : heure de Paris approximative
    LOCAL_TZ = timezone(timedelta(hours=1))

from dotenv import load_dotenv
from openai import OpenAI

from database import SessionLocal, engine
from models import Base, Client, Conversation, Message as MessageModel, Event, ReportLog

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
resend.api_key = os.getenv("RESEND_API_KEY")
SUPERADMIN_PASSWORD = os.getenv("SUPERADMIN_PASSWORD", "superadmin123")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)


# ── Migration automatique ─────────────────────────────────────────────────────
MIGRATIONS = [
    ("conversations.state", "ALTER TABLE conversations ADD COLUMN state VARCHAR DEFAULT 'normal'"),
    ("clients.shop_url",    "ALTER TABLE clients ADD COLUMN shop_url VARCHAR"),
    ("clients.widget_config", "ALTER TABLE clients ADD COLUMN widget_config TEXT"),
    ("conversations.handled", "ALTER TABLE conversations ADD COLUMN handled BOOLEAN DEFAULT FALSE"),
]

def run_migrations():
    # Une connexion par migration : sous Postgres, un ALTER qui echoue (colonne
    # deja presente) annule toute la transaction, ce qui ferait echouer les suivants.
    for name, sql in MIGRATIONS:
        try:
            with engine.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
                print("Migration OK:", name)
        except Exception:
            pass  # colonne deja presente

run_migrations()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── États de conversation ─────────────────────────────────────────────────────
STATE_NORMAL   = "normal"
STATE_PROPOSED = "proposed"
STATE_ASKING   = "asking"
STATE_DONE     = "done"

MSG_PROPOSAL  = "Souhaitez-vous être contacté par notre équipe ?"
MSG_ASKING    = "Parfait ! Donnez-moi votre prénom et votre numéro de téléphone, notre équipe vous contactera rapidement."
MSG_CONFIRMED = "Merci ! Notre équipe va vous contacter très rapidement. À bientôt !"
MSG_DECLINED  = "Pas de problème, je reste à votre disposition si besoin !"


# ── Détection demande humain ──────────────────────────────────────────────────
HUMAN_REGEX = re.compile(
    r'\b(humain|assistant|conseiller|agent|rappel|rappeler|rendez.?vous|rdv|'
    r'devis|intervention|technicien|quelqu.un|votre equipe|'
    r'human|someone|somebody|callback|call me|speak to|talk to|'
    r'appointment|quote|technician|real person|your team|'
    r'umano|qualcuno|richiamare|richiamarmi|appuntamento|preventivo|tecnico|'
    r'humano|alguien|llamarme|cita|presupuesto|tecnico|'
    r'mensch|jemand|zuruckrufen|termin|angebot|techniker|'
    r'humano|alguem|ligar|orcamento|tecnico|'
    r'mens|iemand|terugbellen|afspraak|offerte|monteur)\b',
    re.IGNORECASE
)

GPT_PROPOSES_HUMAN = re.compile(
    r'(mettre en relation|vous contacter|vous rappeler|prendre rendez|'
    r'un devis|un technicien|notre equipe|nos conseillers|un expert|contactez.nous|'
    r'arrange for|put you in touch|contact you|call you back|'
    r'our team|a technician|an expert|schedule|get in touch|'
    r'metterti in contatto|contattarti|richiamarti|il nostro team|'
    r'ponernos en contacto|contactarte|nuestro equipo|'
    r'kontaktieren|unser team|in verbindung)',
    re.IGNORECASE
)


# ── Fonctions GPT ─────────────────────────────────────────────────────────────
def get_visitor_messages(conv_id: str, db: Session) -> list:
    msgs = db.query(MessageModel).filter(
        MessageModel.conversation_id == conv_id,
        MessageModel.role == "user"
    ).order_by(MessageModel.created_at).all()
    return [m.content for m in msgs]

# Mots qui suffisent a reconnaitre un visiteur francophone, sans appel a l'IA
FR_HINTS = re.compile(
    r"\b(je|j|vous|nous|elle|est|des|une|pour|avec|dans|pas|oui|bonjour|bonsoir|salut|merci|svp|stp|"
    r"francais|français|avez|avoir|quels|quelles|combien|taille|tailles|livraison|livrer|commande|commander|"
    r"produit|produits|prix|retour|retours|rappeler|appeler|parler|humain|voudrais|veux|peux|pouvez|"
    r"moi|mon|votre|vos|quand|pourquoi|aussi|encore|ça|ca|c'est|qu'est|est-ce|dispo)\b",
    re.IGNORECASE,
)


KNOWN_LANGS = {"fr", "en", "es", "it", "de", "pt", "nl", "ar", "zh", "ja", "ru", "pl", "tr", "ro",
               "sv", "da", "no", "fi", "cs", "el", "he", "ko", "uk", "hu", "vi", "th", "id", "hi"}


def page_lang_hint(value) -> str:
    """Langue de la page ou se trouve le widget (attribut lang du site)."""
    code = (value or "").strip().lower()[:2]
    return code if code in KNOWN_LANGS else "fr"


def detect_visitor_language(visitor_messages: list, default: str = "fr") -> str:
    """Code langue (ISO 639-1) du visiteur. Sans indice clair, on garde la
    langue de la page (francais par defaut : c'est le marche de Replai)."""
    recent = [m for m in visitor_messages[-3:] if m and m.strip()]
    if not recent:
        return default
    # On juge sur le message le plus recent qui contient de vrais mots : un
    # simple "Gianluca 0612345678" ou un email ne dit rien de la langue.
    for msg in reversed(recent):
        if FR_HINTS.search(msg):
            return "fr"
        words = re.findall(r"[^\W\d_]{2,}", re.sub(r"\S+@\S+", " ", msg))
        if len(words) >= 2:
            break
    else:
        # Que des "ok", noms ou numeros : rien ne dit la langue
        return default
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            max_tokens=5,
            messages=[
                {"role": "system", "content": (
                    "You identify the language a website visitor writes in. "
                    "Messages are separated by |, the last one is the most recent. "
                    "Ignore names, phone numbers, emails and one-word answers like ok, yes/no: "
                    "judge from the most recent message that contains real words. "
                    "If the visitor asks for a language (e.g. 'francais?', 'english please'), return that language. "
                    "Answer ONLY with the ISO 639-1 code (e.g. fr, en, it, es, de). If unsure, answer %s." % default
                )},
                {"role": "user", "content": " | ".join(recent)[:500]}
            ]
        )
        code = response.choices[0].message.content.strip().lower()[:2]
        return code if code in KNOWN_LANGS else default
    except Exception as e:
        print("LANG DETECT ERROR:", e)
        return default


def translate_to_visitor_language(canonical_msg: str, visitor_messages: list, page_lang: str = "fr") -> str:
    """Les messages fixes sont ecrits en francais : on ne les traduit que si le
    visiteur ecrit dans une autre langue (ou, a defaut, si la page n'est pas en francais)."""
    lang = detect_visitor_language(visitor_messages or [], page_lang)
    if lang == "fr":
        return canonical_msg
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            max_tokens=150,
            messages=[
                {"role": "system", "content": (
                    "Translate the following French customer-service message into the language whose "
                    "ISO 639-1 code is '%s'. Keep the same tone and meaning. "
                    "Return ONLY the translation, nothing else." % lang
                )},
                {"role": "user", "content": canonical_msg}
            ]
        )
        result = response.choices[0].message.content.strip()
        return result if result else canonical_msg
    except Exception as e:
        print("TRANSLATE ERROR:", e)
        return canonical_msg


YES_FAST = re.compile(r"^\s*(oui|ouais|ouep|ok|okay|d'?accord|dac|volontiers|avec plaisir|bien s[uû]r|carr[ée]ment|"
                      r"oui (svp|stp|merci|volontiers|bien s[uû]r|avec plaisir)|go|yes|yep|yeah|sure|s[iì]|ja|claro)\s*[!.]*\s*$", re.I)
NO_FAST = re.compile(r"^\s*(non|nan|no|nope|non merci|pas besoin|pas pour l'instant|pas maintenant|plus tard|"
                     r"no thanks|nein)\s*[!.]*\s*$", re.I)

CLASSIFY_CONTEXT = {
    "proposal": "The visitor was asked whether they want to be contacted by a team member.",
    "asking": "The visitor was asked to give their first name and phone number so the team can call them back.",
}


def classify_reply(visitor_message: str, step: str) -> str:
    """YES / NO / OTHER. OTHER = le visiteur pose une autre question ou change
    de sujet : on sort alors du parcours de rappel au lieu de boucler."""
    t = (visitor_message or "").strip()
    if YES_FAST.match(t):
        return "YES"
    if NO_FAST.match(t):
        return "NO"
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            max_tokens=5,
            messages=[
                {"role": "system", "content": (
                    CLASSIFY_CONTEXT.get(step, CLASSIFY_CONTEXT["proposal"]) + " "
                    "Classify their reply, in any language. Answer ONLY with YES, NO or OTHER. "
                    "YES = they accept or go along with it (agreeing, giving part of their details, "
                    "asking how long it takes, saying they look for their number). "
                    "NO = they decline or refuse. "
                    "OTHER = they ask a different question or talk about something else "
                    "(a product, stock, delivery, sizes, how to get news, etc.)."
                )},
                {"role": "user", "content": t[:300]}
            ]
        )
        label = response.choices[0].message.content.strip().upper()
        for option in ("OTHER", "YES", "NO"):
            if option in label:
                return option
        return "OTHER"
    except Exception as e:
        print("CLASSIFY ERROR:", e)
        if re.search(r"\b(non|no|nope|nein|jamais|never)\b", t, re.I):
            return "NO"
        if "?" in t or len(t.split()) > 6:
            return "OTHER"
        return "YES"


EMAIL_RE = re.compile(r"[^@\s<>]+@[^@\s<>]+\.[a-zA-Z]{2,}")


def contains_contact_info(message: str) -> bool:
    """Un numero (6 chiffres ou plus) ou une adresse email."""
    digits = re.sub(r'\D', '', message)
    return len(digits) >= 6 or bool(EMAIL_RE.search(message))


# ── Gestion état ──────────────────────────────────────────────────────────────
def get_state(conv_id: str, db: Session) -> str:
    try:
        row = db.execute(
            text("SELECT state FROM conversations WHERE id = :id"),
            {"id": conv_id}
        ).fetchone()
        return row[0] if row and row[0] else STATE_NORMAL
    except Exception:
        return STATE_NORMAL


def set_state(conv_id: str, state: str, db: Session):
    try:
        db.execute(
            text("UPDATE conversations SET state = :s WHERE id = :id"),
            {"s": state, "id": conv_id}
        )
        db.commit()
    except Exception as e:
        print("SET_STATE ERROR:", e)


def save_message(conv_id: str, role: str, content: str, db: Session):
    db.add(MessageModel(
        id=str(uuid.uuid4()),
        conversation_id=conv_id,
        role=role,
        content=content
    ))
    db.commit()


def bot_reply(text_content: str, conv_id: str, needs_human: bool = False, products: Optional[list] = None):
    out = {"reply": text_content, "conversation_id": conv_id, "needs_human": needs_human}
    if products:
        out["products"] = products
    return out


# ── Email ─────────────────────────────────────────────────────────────────────
def send_human_email(conv_id: str, contact_info: str, client_obj: Client):
    print("EMAIL START")
    if not client_obj.client_email:
        print("EMAIL SKIP: pas d email configure")
        return
    try:
        params = {
            "from": "Replai <noreply@gianluca-ai.fr>",
            "to": [client_obj.client_email],
            "subject": "Nouveau client a rappeler - " + client_obj.business_name,
            "html": (
                "<div style='font-family:Arial,sans-serif;max-width:600px'>"
                "<h2 style='color:#6366f1'>Nouveau client a rappeler</h2>"
                "<p><strong>Business :</strong> " + client_obj.business_name + "</p>"
                "<p><strong>Conversation :</strong> " + conv_id[:8] + "</p>"
                "<p><strong>Coordonnees :</strong> "
                "<span style='color:#4f8eff;font-weight:bold;font-size:16px'>"
                + html_lib.escape(contact_info) +
                "</span></p>"
                "<p>Recontactez ce client rapidement !</p>"
                "<hr style='border:none;border-top:1px solid #eee'>"
                "<p style='color:#888;font-size:12px'>Replai — AI Widget pour TPEs</p>"
                "</div>"
            )
        }
        email = resend.Emails.send(params)
        print("EMAIL SENT:", email['id'])
    except Exception as e:
        print("EMAIL ERROR:", str(e))


# ── Catalogue automatique (Shopify et WooCommerce) ───────────────────────────
# Shopify expose publiquement /products.json, WooCommerce /wp-json/wc/store/v1/products
# (sans cle API). On lit le catalogue, on le normalise dans un format commun
# (fiches produit du chat + texte pour le prompt) et on le met en cache.
CATALOG_TTL = 1800          # secondes (30 min)
CATALOG_MAX_CHARS = 40000   # ~10k tokens : ~150 produits avec description courte
CATALOG_CACHE = {}          # shop_url -> (timestamp, {"platform", "products", "text"})
EMPTY_CATALOG = {"platform": "", "products": [], "text": ""}
SIZE_OPTION_RE = re.compile(r"taille|size|pointure|talla|gr(o|ö)(ss|ß)e|misura", re.I)
FIT_RE = re.compile(r"[^.!?\n]*(mannequin|mod[eè]le (mesure|porte|fait)|porte (un|une|du|la|le) |mesure \d|oversize|coupe |taille (grand|petit|normalement)|"
                    r"runs (small|large)|true to size|fits|prenez|prendre (une|la) taille|cm de|"
                    r"model'?s?\b|wears? size|height \d|boxy|relaxed fit|regular fit|slim fit|loose fit)[^.!?\n]*[.!?]?", re.I)


def normalize_shop_url(url: str) -> str:
    url = (url or "").strip().rstrip("/")
    if not url:
        return ""
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return url


def get_shop_url(token: str, db: Session) -> str:
    try:
        row = db.execute(
            text("SELECT shop_url FROM clients WHERE token = :t"), {"t": token}
        ).fetchone()
        return row[0] if row and row[0] else ""
    except Exception as e:
        print("GET_SHOP_URL ERROR:", e)
        db.rollback()
        return ""


def set_shop_url(token: str, url: str, db: Session):
    db.execute(
        text("UPDATE clients SET shop_url = :u WHERE token = :t"),
        {"u": normalize_shop_url(url) or None, "t": token}
    )
    db.commit()


def strip_html(raw: str) -> str:
    no_tags = re.sub(r"<[^>]+>", " ", raw or "")
    return re.sub(r"\s+", " ", html_lib.unescape(no_tags)).strip()


def _uniq(values):
    seen, out = set(), []
    for v in values:
        if v is not None and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _fit_notes(desc: str) -> str:
    """Phrases de la description utiles pour conseiller une taille."""
    found = [m.group(0).strip() for m in FIT_RE.finditer(desc or "")]
    return " ".join(_uniq(found))[:220]


def _shopify_image(src: str) -> str:
    if not src:
        return ""
    return src + ("&" if "?" in src else "?") + "width=240"


def normalize_shopify(products: list, shop_url: str) -> list:
    out = []
    for p in products:
        variants = p.get("variants") or []
        if not variants:
            continue
        options = [{"name": o.get("name") or "Option", "values": o.get("values") or []}
                   for o in (p.get("options") or [])]
        simple = len(variants) == 1 and variants[0].get("title") == "Default Title"
        vs = []
        for v in variants:
            try:
                vprice = float(v["price"]) if v.get("price") not in (None, "") else None
            except (TypeError, ValueError):
                vprice = None
            vs.append({
                "id": str(v.get("id")),
                "title": "" if simple else (v.get("title") or ""),
                "options": [v.get("option%d" % i) for i in (1, 2, 3) if v.get("option%d" % i)],
                "available": bool(v.get("available")),
                "price": vprice,
            })
        prices = [v["price"] for v in vs if v["price"] is not None]
        compares = []
        for v in variants:
            try:
                if v.get("compare_at_price"):
                    compares.append(float(v["compare_at_price"]))
            except (TypeError, ValueError):
                pass
        price = min(prices) if prices else None
        images = p.get("images") or []
        desc = strip_html(p.get("body_html", ""))
        out.append({
            "id": str(p.get("id")),
            "title": p.get("title") or "Produit",
            "url": shop_url + "/products/" + p["handle"] if p.get("handle") else "",
            "image": _shopify_image(images[0].get("src", "")) if images else "",
            "price": price,
            "compare_at": max(compares) if compares and price is not None and max(compares) > price else None,
            "currency": "EUR",
            "options": [] if simple else options,
            "variants": vs,
            "available": any(v["available"] for v in vs),
            "desc": desc,
            "fit": _fit_notes(desc),
        })
    return out


def _woo_money(prices: dict, key: str):
    raw = (prices or {}).get(key)
    if raw in (None, ""):
        return None
    try:
        return int(raw) / (10 ** int((prices or {}).get("currency_minor_unit", 2)))
    except (TypeError, ValueError):
        return None


def normalize_woocommerce(products: list, shop_url: str) -> list:
    out = []
    for p in products:
        prices = p.get("prices") or {}
        price = _woo_money(prices, "price")
        regular = _woo_money(prices, "regular_price")
        attrs = [a for a in (p.get("attributes") or []) if a.get("has_variations")]
        # Les variations donnent le "slug" de la valeur (ex. "m") : on retrouve le nom affiche ("M")
        names = {}
        for a in attrs:
            for t in (a.get("terms") or []):
                if t.get("slug") and t.get("name"):
                    names[t["slug"].lower()] = t["name"]
        options = [{"name": a.get("name") or "Option",
                    "values": [t.get("name") for t in (a.get("terms") or []) if t.get("name")]} for a in attrs]
        in_stock = bool(p.get("is_in_stock", True)) and bool(p.get("is_purchasable", True))
        vs = []
        for v in (p.get("variations") or []):
            vals = [names.get(str(a.get("value")).lower(), a.get("value"))
                    for a in (v.get("attributes") or []) if a.get("value")]
            vs.append({"id": str(v.get("id")), "title": " / ".join(vals), "options": vals,
                       "available": in_stock, "price": price})
        if not vs:
            vs = [{"id": str(p.get("id")), "title": "", "options": [], "available": in_stock, "price": price}]
            options = []
        images = p.get("images") or []
        desc = strip_html(p.get("short_description") or p.get("description") or "")
        out.append({
            "id": str(p.get("id")),
            "title": html_lib.unescape(p.get("name") or "Produit"),
            "url": p.get("permalink") or "",
            "image": (images[0].get("thumbnail") or images[0].get("src") or "") if images else "",
            "price": price,
            "compare_at": regular if regular and price is not None and regular > price else None,
            "currency": prices.get("currency_code") or "EUR",
            "options": options,
            "variants": vs,
            "available": in_stock,
            "desc": desc,
            "fit": _fit_notes(desc),
        })
    return out


def _stock_text(p: dict) -> str:
    variants = p["variants"]
    if not p["options"]:
        return "en stock" if p["available"] else "RUPTURE DE STOCK"
    if not p["available"]:
        return "RUPTURE DE STOCK (toutes tailles)"
    if len(p["options"]) == 1:
        dispo = _uniq(v["title"] for v in variants if v["available"])
        epuise = _uniq(v["title"] for v in variants if not v["available"])
        txt = "%s disponible : %s" % (p["options"][0]["name"], ", ".join(dispo[:40]))
        return txt + (" | epuise : " + ", ".join(epuise[:40]) if epuise else "")
    # Plusieurs options (ex : taille x couleur) : on resume option par option,
    # sinon une bague en 15 tailles x 4 pierres ferait 60 variantes sur une ligne.
    parts = []
    for i, opt in enumerate(p["options"][:3]):
        dispo = _uniq(v["options"][i] for v in variants if v["available"] and len(v["options"]) > i)
        all_vals = _uniq(list(opt["values"]) + [v["options"][i] for v in variants if len(v["options"]) > i])
        epuise = [x for x in all_vals if x not in dispo]
        part = "%s dispo : %s" % (opt["name"], ", ".join(dispo[:30]))
        if epuise:
            part += " (epuise : %s)" % ", ".join(epuise[:30])
        parts.append(part)
    return " | ".join(parts)


def catalog_to_text(products: list, shop_url: str) -> str:
    cores, descs = [], []
    for p in products:
        line = "- " + p["title"]
        if p["price"] is not None:
            line += " : %.2f %s" % (p["price"], p["currency"])
            if p["compare_at"]:
                line += " (au lieu de %.2f %s)" % (p["compare_at"], p["currency"])
        line += " | " + _stock_text(p)
        if p["url"]:
            line += " | " + p["url"]
        if p["fit"]:
            line += " | INFO TAILLE : " + p["fit"]
        cores.append(line)
        desc = p["desc"]
        for m in FIT_RE.finditer(desc or ""):      # deja repris dans INFO TAILLE
            desc = desc.replace(m.group(0), " ")
        descs.append(re.sub(r"\s+", " ", desc).strip())

    # Priorite : que TOUS les produits tiennent dans le prompt. On raccourcit
    # les descriptions avant de supprimer des produits.
    lines = cores
    out = "\n".join(cores)
    for desc_len in (250, 120, 60, 0):
        lines = [c + (" | " + d[:desc_len] if d and desc_len else "") for c, d in zip(cores, descs)]
        out = "\n".join(lines)
        if len(out) <= CATALOG_MAX_CHARS:
            return out
    kept = out[:CATALOG_MAX_CHARS].rsplit("\n", 1)[0]
    missing = len(lines) - kept.count("\n") - 1
    return kept + "\n(... %d autres produits non listes ici : voir le site %s)" % (missing, shop_url)


# Compatibilite : ancien nom utilise par les tests et outils
def format_catalog(products: list, shop_url: str) -> str:
    return catalog_to_text(normalize_shopify(products, shop_url), shop_url)


def _fetch_shopify(shop_url: str) -> list:
    r = httpx.get(shop_url + "/products.json", params={"limit": 250}, timeout=5.0, follow_redirects=True,
                  headers={"User-Agent": "Replai-Catalog/1.0"})
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, dict) or "products" not in data:
        raise ValueError("pas un catalogue Shopify")
    return normalize_shopify(data.get("products", []), shop_url)


def _fetch_woocommerce(shop_url: str) -> list:
    products = []
    for page in range(1, 4):        # 300 produits maximum
        r = httpx.get(shop_url + "/wp-json/wc/store/v1/products", params={"per_page": 100, "page": page},
                      timeout=6.0, follow_redirects=True, headers={"User-Agent": "Replai-Catalog/1.0"})
        r.raise_for_status()
        batch = r.json()
        if not isinstance(batch, list):
            raise ValueError("pas un catalogue WooCommerce")
        products += batch
        if len(batch) < 100:
            break
    return normalize_woocommerce(products, shop_url)


def get_catalog(shop_url: str) -> dict:
    """Catalogue normalise, avec cache. En cas d'erreur, renvoie la derniere
    version connue (ou un catalogue vide) : le chat ne doit jamais planter a cause de la boutique."""
    if not shop_url:
        return EMPTY_CATALOG
    now = time.time()
    cached = CATALOG_CACHE.get(shop_url)
    if cached and now - cached[0] < CATALOG_TTL:
        return cached[1]
    order = ["woocommerce", "shopify"] if cached and cached[1].get("platform") == "woocommerce" else ["shopify", "woocommerce"]
    errors = []
    for platform in order:
        try:
            products = _fetch_shopify(shop_url) if platform == "shopify" else _fetch_woocommerce(shop_url)
            catalog = {"platform": platform, "products": products, "text": catalog_to_text(products, shop_url)}
            CATALOG_CACHE[shop_url] = (now, catalog)
            print("CATALOG OK:", shop_url, platform, len(products), "produits")
            return catalog
        except Exception as e:
            errors.append("%s: %s" % (platform, e))
    print("CATALOG ERROR:", shop_url, " | ".join(errors))
    # On garde l'ancienne version (ou rien) et on ne reessaie que dans 5 min,
    # pour ne pas ralentir chaque message si la boutique est injoignable.
    previous = cached[1] if cached else EMPTY_CATALOG
    CATALOG_CACHE[shop_url] = (now - CATALOG_TTL + 300, previous)
    return previous


def get_catalog_text(shop_url: str) -> str:
    return get_catalog(shop_url)["text"]


def _url_key(url: str) -> str:
    """Cle de comparaison d'URL produit : hote sans www + chemin, sans parametres."""
    try:
        u = httpx.URL(url)
        return u.host.lower().removeprefix("www.") + u.path.rstrip("/").lower()
    except Exception:
        return ""


PRODUCT_URL_RE = re.compile(r"https?://[^\s<>\"')\]]+")


def product_cards(reply: str, catalog: dict, limit: int = 3) -> list:
    """Produits cites dans la reponse (par leur lien), au format des fiches du widget."""
    by_url = {}
    for p in catalog.get("products", []):
        if p.get("url"):
            by_url[_url_key(p["url"])] = p
    cards, seen = [], set()
    for raw in PRODUCT_URL_RE.findall(reply or ""):
        p = by_url.get(_url_key(raw.rstrip(".,;:!?»")))
        if not p or p["id"] in seen:
            continue
        seen.add(p["id"])
        size_idx = next((i for i, o in enumerate(p["options"]) if SIZE_OPTION_RE.search(o["name"])), None)
        cards.append({
            "id": p["id"],
            "title": p["title"],
            "url": p["url"],
            "image": p["image"],
            "price": p["price"],
            "compare_at": p["compare_at"],
            "currency": p["currency"],
            "platform": catalog.get("platform", ""),
            "option_label": (p["options"][size_idx]["name"] if size_idx is not None
                             else (" / ".join(o["name"] for o in p["options"]) if p["options"] else "")),
            "variants": [{"id": v["id"], "title": v["title"], "available": v["available"]} for v in p["variants"][:60]],
            "available": p["available"],
        })
        if len(cards) >= limit:
            break
    return cards


# ── Infos generales de la boutique (accueil + conditions) ────────────────────
# Le catalogue ne dit rien de la newsletter, des reseaux sociaux ou des
# conditions de livraison : on lit la page d'accueil et les pages de conditions
# Shopify, avec un cache long (ces infos changent rarement).
SITE_INFO_TTL = 6 * 3600
SITE_INFO_CACHE = {}        # shop_url -> (timestamp, texte)
SOCIAL_RE = re.compile(r"href=[\"'](https?://(?:www\.)?(instagram\.com|tiktok\.com|facebook\.com|youtube\.com|x\.com|twitter\.com|pinterest\.[a-z.]+)/[^\"'?#]*)", re.I)
POLICY_PAGES = [("Livraison", "/policies/shipping-policy"), ("Retours et remboursements", "/policies/refund-policy")]
# Guide des tailles : lien trouve sur la page d'accueil, sinon adresses courantes
SIZE_LINK_RE = re.compile(r"href=[\"']([^\"'#]*(?:guide[-_]?(?:des[-_]?)?tailles?|size[-_]?(?:guide|chart)|tailles|sizing)[^\"'#]*)[\"']", re.I)
SIZE_GUIDE_PATHS = ["/pages/guide-des-tailles", "/pages/size-guide", "/pages/guide-tailles", "/pages/size-chart",
                    "/guide-des-tailles", "/size-guide"]


def html_to_text(page: str) -> str:
    page = re.sub(r"(?is)<(script|style|noscript|svg|template|iframe)[^>]*>.*?</\1>", " ", page or "")
    page = re.sub(r"(?is)<!--.*?-->", " ", page)
    return strip_html(page)


def _fetch(url: str, timeout: float = 4.0) -> str:
    r = httpx.get(url, timeout=timeout, follow_redirects=True,
                  headers={"User-Agent": "Mozilla/5.0 (compatible; Replai-Info/1.0)"})
    r.raise_for_status()
    return r.text


def build_site_info(shop_url: str) -> str:
    parts = []
    home = ""
    try:
        home = _fetch(shop_url)
        socials = []
        for url, net in SOCIAL_RE.findall(home):
            if url.rstrip("/").count("/") >= 3 and url not in socials:
                socials.append(url.rstrip("/"))
        text = html_to_text(home)
        # Le haut (bandeau, accroche) et le bas (newsletter, contact) sont les plus utiles
        excerpt = text if len(text) <= 2800 else text[:1200] + " (...) " + text[-1600:]
        parts.append("PAGE D'ACCUEIL (extrait) : " + excerpt)
        if re.search(r"newsletter|contact\[tags\]|inscri(vez|ption)|subscribe|abonnez", home, re.I):
            parts.append("NEWSLETTER : le site propose une inscription a la newsletter (formulaire sur le site, generalement en bas de page).")
        if socials:
            parts.append("RESEAUX SOCIAUX : " + ", ".join(socials[:6]))
    except Exception as e:
        print("SITE INFO HOME ERROR:", shop_url, e)
    for label, path in POLICY_PAGES:
        try:
            t = html_to_text(_fetch(shop_url + path))
            if len(t) > 40:
                parts.append(label.upper() + " (conditions officielles) : " + t[:2000])
        except Exception:
            pass
    guide = size_guide_text(shop_url, home)
    if guide:
        parts.append("GUIDE DES TAILLES DE LA BOUTIQUE : " + guide)
    return "\n".join(parts)[:9500]


def size_guide_text(shop_url: str, home: str) -> str:
    candidates = []
    for href in SIZE_LINK_RE.findall(home or ""):
        url = href if href.startswith("http") else shop_url + "/" + href.lstrip("/")
        if _host(url) == _host(shop_url) and url not in candidates:
            candidates.append(url)
    candidates += [shop_url + p for p in SIZE_GUIDE_PATHS]
    for url in candidates[:6]:
        try:
            t = html_to_text(_fetch(url, timeout=3.0))
            if len(t) > 80 and re.search(r"\b(XS|S|M|L|XL|cm|tour de|poitrine|taille)\b", t, re.I):
                return t[:2000]
        except Exception:
            continue
    return ""


def get_site_info(shop_url: str) -> str:
    if not shop_url:
        return ""
    now = time.time()
    cached = SITE_INFO_CACHE.get(shop_url)
    if cached and now - cached[0] < SITE_INFO_TTL:
        return cached[1]
    info = build_site_info(shop_url)
    if info:
        SITE_INFO_CACHE[shop_url] = (now, info)
        return info
    previous = cached[1] if cached else ""
    SITE_INFO_CACHE[shop_url] = (now - SITE_INFO_TTL + 1800, previous)   # reessai dans 30 min
    return previous


def _host(url: str) -> str:
    try:
        return httpx.URL(url).host.lower().removeprefix("www.")
    except Exception:
        return ""


# ── Apparence du widget par client ────────────────────────────────────────────
# Stockee en JSON dans clients.widget_config :
#   color (#rrggbb), mode ("light" | "dark"), assistant_name, welcome
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def get_widget_config(token: str, db: Session) -> dict:
    try:
        row = db.execute(
            text("SELECT widget_config FROM clients WHERE token = :t"), {"t": token}
        ).fetchone()
        return json.loads(row[0]) if row and row[0] else {}
    except Exception as e:
        print("GET_WIDGET_CONFIG ERROR:", e)
        db.rollback()
        return {}


def set_widget_config(token: str, cfg: dict, db: Session):
    clean = {k: v for k, v in cfg.items() if v not in (None, "")}
    db.execute(
        text("UPDATE clients SET widget_config = :c WHERE token = :t"),
        {"c": json.dumps(clean, ensure_ascii=False) if clean else None, "t": token}
    )
    db.commit()


def _to_hex(value: str) -> Optional[str]:
    v = value.strip()
    if v.startswith("#"):
        h = v[1:]
        if len(h) in (3, 4):
            h = "".join(ch * 2 for ch in h[:3])
        elif len(h) in (6, 8):
            h = h[:6]
        else:
            return None
        return "#" + h.lower() if re.fullmatch(r"[0-9a-fA-F]{6}", h) else None
    m = re.fullmatch(r"rgba?\(\s*(.*?)\s*\)", v, re.I)
    if m:
        # rgb(18, 18, 18) / rgba(18,18,18,0.5) / rgb(18 18 18 / 1.0)  (themes Horizon)
        inner = m.group(1).replace("/", " ").replace(",", " ").split()
        if len(inner) >= 3 and all(x.isdigit() for x in inner[:3]):
            if len(inner) >= 4:
                try:
                    alpha = float(inner[3].rstrip("%")) / (100 if inner[3].endswith("%") else 1)
                    if alpha < 0.5:
                        return None
                except ValueError:
                    return None
            v = ",".join(inner[:3])
        else:
            return None
    parts = [p.strip() for p in v.split(",")]
    if len(parts) == 3 and all(p.isdigit() and int(p) <= 255 for p in parts):
        return "#" + "".join("%02x" % int(p) for p in parts)
    return None


def _luminance(hex_color: str) -> float:
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


CSS_VAR_RE = re.compile(r"--([A-Za-z0-9_-]+)\s*:\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3})\s*(?:!important\s*)?[;}]", re.I)
# Themes plus anciens : pas de variables, une regle .btn { background: ... } dans le CSS
BTN_RULE_RE = re.compile(r"\.(?:btn|button|shopify-payment-button__button)(?:--primary|-primary)?\b[^{,]*\{[^}]*?background(?:-color)?\s*:\s*(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\))", re.I)
STYLESHEET_RE = re.compile(r"<link[^>]+href=[\"']([^\"']+\.css[^\"']*)[\"']", re.I)
META_THEME_RE = re.compile(r"<meta[^>]+name=[\"']theme-color[\"'][^>]*content=[\"']([^\"']+)[\"']", re.I)
ACCENT_EXCLUDE = ("text", "label", "border", "shadow", "secondary", "outline", "hover",
                  "foreground", "link", "disabled", "badge", "sale", "error", "success")
BACKGROUND_NAMES = ("color-background", "colorbody", "color-body", "body-background",
                    "color-body-bg", "background", "color-bg", "bg-color")


def detect_theme_from_html(page: str) -> dict:
    """Devine la couleur principale (boutons) et le fond (clair/sombre) d'une
    boutique a partir des variables CSS de son theme Shopify."""
    css_vars = [(n.lower(), _to_hex(v)) for n, v in CSS_VAR_RE.findall(page)]
    css_vars = [(n, v) for n, v in css_vars if v]

    def first(pred):
        for n, v in css_vars:
            if pred(n) and not any(x in n for x in ACCENT_EXCLUDE) and _luminance(v) < 0.92:
                return v
        return None

    color = (first(lambda n: "button" in n) or first(lambda n: "btn" in n))
    if not color:
        m = META_THEME_RE.search(page)
        meta = _to_hex(m.group(1)) if m else None
        if meta and _luminance(meta) < 0.92:
            color = meta
    color = color or first(lambda n: "accent" in n) or first(lambda n: "primary" in n)
    if not color:
        for raw in BTN_RULE_RE.findall(page):
            hx = _to_hex(raw)
            if hx and _luminance(hx) < 0.92:
                color = hx
                break

    mode = "light"
    for wanted in BACKGROUND_NAMES:
        bg = next((v for n, v in css_vars if n == wanted), None)
        if bg:
            mode = "light" if _luminance(bg) > 0.5 else "dark"
            break
    return {"color": color, "mode": mode}


def detect_shop_theme(shop_url: str) -> dict:
    r = httpx.get(shop_url, timeout=8.0, follow_redirects=True,
                  headers={"User-Agent": "Mozilla/5.0 (compatible; Replai-Theme/1.0)"})
    r.raise_for_status()
    page = r.text
    found = detect_theme_from_html(page)
    if found["color"]:
        return found
    # Couleurs absentes de la page : on regarde les feuilles de style du theme
    css = []
    for href in STYLESHEET_RE.findall(page)[:12]:
        if not ("/cdn/shop/" in href or "/assets/" in href or "cdn.shopify.com" in href):
            continue
        url = "https:" + href if href.startswith("//") else str(httpx.URL(str(r.url)).join(href))
        try:
            rc = httpx.get(url, timeout=6.0, follow_redirects=True,
                           headers={"User-Agent": "Mozilla/5.0 (compatible; Replai-Theme/1.0)"})
            if rc.status_code == 200:
                css.append(rc.text[:400000])
        except Exception:
            pass
        if len(css) >= 3:
            break
    if css:
        extra = detect_theme_from_html("\n".join(css))
        if extra["color"]:
            found["color"] = extra["color"]
    return found


# ── Pydantic models ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    page_content: Optional[str] = None
    page_url: Optional[str] = None
    client_token: Optional[str] = None
    page_lang: Optional[str] = None

class ContactHumanRequest(BaseModel):
    conversation_id: Optional[str] = None
    client_token: Optional[str] = None
    page_lang: Optional[str] = None

class CreateClientRequest(BaseModel):
    business_name: str
    admin_password: str
    client_email: Optional[str] = None
    shop_url: Optional[str] = None
    superadmin_password: str

class UpdateClientRequest(BaseModel):
    token: str
    superadmin_password: str
    system_prompt: Optional[str] = None
    business_name: Optional[str] = None
    admin_password: Optional[str] = None
    client_email: Optional[str] = None
    shop_url: Optional[str] = None  # "" pour desactiver le catalogue
    # Apparence du widget ("" pour revenir a la valeur par defaut)
    widget_color: Optional[str] = None      # ex : "#111111"
    widget_mode: Optional[str] = None       # "light" ou "dark"
    assistant_name: Optional[str] = None    # ex : "Assistant Dreamer"
    welcome_message: Optional[str] = None   # premier message affiche
    teaser: Optional[str] = None            # bulle d'accroche : texte perso, "off" pour la couper, "" = automatique

class DetectThemeRequest(BaseModel):
    token: str
    superadmin_password: str
    assistant_name: Optional[str] = None
    welcome_message: Optional[str] = None


# ── Super-admin ───────────────────────────────────────────────────────────────
@app.post("/superadmin/create-client")
def create_client(req: CreateClientRequest, db: Session = Depends(get_db)):
    if req.superadmin_password != SUPERADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Non autorise")
    token = req.business_name.lower().replace(" ", "_") + "_" + str(uuid.uuid4())[:6]
    new_client = Client(
        token=token,
        business_name=req.business_name,
        admin_password=req.admin_password,
        client_email=req.client_email
    )
    db.add(new_client)
    db.commit()
    if req.shop_url:
        set_shop_url(token, req.shop_url, db)
    return {
        "token": token,
        "business_name": req.business_name,
        "shop_url": normalize_shop_url(req.shop_url or "") or None,
        "admin_url": "/admin?token=" + token,
        "widget_script": '<script src="https://ai-assistant-backend-clean-iz6y.onrender.com/static/ai-widget.js?token=' + token + '"></script>'
    }


@app.post("/superadmin/update-client")
def update_client(req: UpdateClientRequest, db: Session = Depends(get_db)):
    if req.superadmin_password != SUPERADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Non autorise")
    c = db.query(Client).filter(Client.token == req.token).first()
    if not c:
        raise HTTPException(status_code=404, detail="Client introuvable")
    if req.system_prompt is not None:
        c.system_prompt = req.system_prompt
    if req.business_name is not None:
        c.business_name = req.business_name
    if req.admin_password is not None:
        c.admin_password = req.admin_password
    if req.client_email is not None:
        c.client_email = req.client_email
    db.commit()
    if req.shop_url is not None:
        set_shop_url(c.token, req.shop_url, db)

    if any(x is not None for x in (req.widget_color, req.widget_mode, req.assistant_name, req.welcome_message, req.teaser)):
        if req.widget_color and not HEX_RE.match(req.widget_color):
            raise HTTPException(status_code=400, detail="widget_color doit etre au format #rrggbb")
        if req.widget_mode and req.widget_mode not in ("light", "dark"):
            raise HTTPException(status_code=400, detail="widget_mode doit etre light ou dark")
        cfg = get_widget_config(c.token, db)
        for key, val in (("color", req.widget_color), ("mode", req.widget_mode),
                         ("assistant_name", req.assistant_name), ("welcome", req.welcome_message),
                         ("teaser", req.teaser)):
            if val is not None:
                cfg[key] = val.strip()[:300]
        set_widget_config(c.token, cfg, db)

    return {"ok": True, "token": c.token, "shop_url": get_shop_url(c.token, db) or None,
            "widget": get_widget_config(c.token, db)}


@app.post("/superadmin/detect-theme")
def detect_theme(req: DetectThemeRequest, db: Session = Depends(get_db)):
    """Lit la page d'accueil de la boutique et applique sa couleur au widget."""
    if req.superadmin_password != SUPERADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Non autorise")
    c = db.query(Client).filter(Client.token == req.token).first()
    if not c:
        raise HTTPException(status_code=404, detail="Client introuvable")
    shop_url = get_shop_url(c.token, db)
    if not shop_url:
        raise HTTPException(status_code=400, detail="Pas de shop_url pour ce client")
    try:
        found = detect_shop_theme(shop_url)
    except Exception as e:
        raise HTTPException(status_code=502, detail="Boutique injoignable : %s" % e)
    cfg = get_widget_config(c.token, db)
    cfg["mode"] = found["mode"]
    if found["color"]:
        cfg["color"] = found["color"]
    if req.assistant_name is not None:
        cfg["assistant_name"] = req.assistant_name.strip()[:60]
    if req.welcome_message is not None:
        cfg["welcome"] = req.welcome_message.strip()[:300]
    set_widget_config(c.token, cfg, db)
    return {"ok": True, "detected": found, "widget": get_widget_config(c.token, db)}


# Derniere fois que le widget a ete charge sur un site (sert a l'onglet Installation)
WIDGET_SEEN = {}    # token -> (datetime UTC, domaine du site)


@app.get("/widget-config")
def widget_config(request: Request, token: str = "", db: Session = Depends(get_db)):
    """Route publique lue par le widget au chargement : uniquement l'apparence."""
    if token:
        site = _host(request.headers.get("referer") or request.headers.get("origin") or "")
        if site and site not in ("aireply.fr", "localhost", "127.0.0.1"):
            WIDGET_SEEN[token] = (datetime.utcnow(), site)
    cfg = get_widget_config(token, db) if token else {}
    return {k: cfg.get(k) for k in ("color", "mode", "assistant_name", "welcome", "teaser") if cfg.get(k)}


@app.get("/superadmin/clients")
def list_clients(superadmin_password: str, db: Session = Depends(get_db)):
    if superadmin_password != SUPERADMIN_PASSWORD:
        raise HTTPException(status_code=401)
    return [{"token": c.token, "business_name": c.business_name, "client_email": c.client_email,
             "shop_url": get_shop_url(c.token, db) or None}
            for c in db.query(Client).all()]


@app.get("/superadmin/catalog-preview")
def catalog_preview(token: str, superadmin_password: str, refresh: bool = False,
                    db: Session = Depends(get_db)):
    """Montre exactement le catalogue que le bot recoit pour ce client."""
    if superadmin_password != SUPERADMIN_PASSWORD:
        raise HTTPException(status_code=401)
    shop_url = get_shop_url(token, db)
    if not shop_url:
        raise HTTPException(status_code=404, detail="Pas de shop_url pour ce client")
    if refresh:
        CATALOG_CACHE.pop(shop_url, None)
    catalog = get_catalog_text(shop_url)
    return {"shop_url": shop_url, "chars": len(catalog), "catalog": catalog}


# ── Dashboard Admin ───────────────────────────────────────────────────────────
# Le dashboard client est dans templates/admin.html (une page par client,
# habillee automatiquement aux couleurs de sa boutique).
ADMIN_HTML_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "admin.html")


# ── Dashboard client ──────────────────────────────────────────────────────────
@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    with open(ADMIN_HTML_PATH, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


def to_local(dt):
    """Les dates sont stockees en UTC : on les affiche a l'heure de Paris."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(LOCAL_TZ)


def fmt_local(dt) -> str:
    d = to_local(dt)
    return d.strftime("%Y-%m-%dT%H:%M") if d else ""


def check_admin(client_token: str, password: str, db: Session) -> Client:
    c = db.query(Client).filter(Client.token == client_token).first()
    if not c or not password or c.admin_password != password:
        raise HTTPException(status_code=401)
    return c


def client_brand(c: Client, db: Session) -> dict:
    """Ce qui habille le dashboard : nom, couleur, boutique."""
    cfg = get_widget_config(c.token, db)
    shop = get_shop_url(c.token, db) or ""
    domain = re.sub(r"^https?://(www\.)?", "", shop).split("/")[0] if shop else ""
    color = cfg.get("color") if HEX_RE.match(cfg.get("color") or "") else ""
    name = c.business_name or ""
    if not name or name.lower() == "mon business":
        name = re.sub(r"^assistant(e)?\s+(de\s+|d')?", "", cfg.get("assistant_name") or "", flags=re.I) or "Replai"
    return {"name": name, "color": color, "shop_url": shop, "domain": domain,
            "assistant_name": cfg.get("assistant_name") or ""}


def conversation_rows(client_token: str, db: Session) -> dict:
    """id -> (state, handled), en une seule requete."""
    try:
        rows = db.execute(text(
            "SELECT id, state, handled FROM conversations WHERE client_token = :t"
        ), {"t": client_token}).fetchall()
        return {r[0]: (r[1] or STATE_NORMAL, bool(r[2])) for r in rows}
    except Exception as e:
        print("CONV ROWS ERROR:", e)
        db.rollback()
        return {}


def messages_by_conversation(client_token: str, db: Session, since=None) -> dict:
    q = db.query(MessageModel).join(
        Conversation, MessageModel.conversation_id == Conversation.id
    ).filter(Conversation.client_token == client_token)
    if since is not None:
        q = q.filter(Conversation.created_at >= since)
    out = {}
    for m in q.order_by(MessageModel.created_at).all():
        out.setdefault(m.conversation_id, []).append(m)
    return out


def lead_contact(msgs) -> Optional[str]:
    contact = None
    for m in msgs:
        if m.role == "user" and contains_contact_info(m.content):
            contact = m.content
    return contact


def first_question(msgs) -> str:
    for m in msgs:
        if m.role == "user" and not contains_contact_info(m.content) and len(m.content.strip()) > 2:
            return m.content.strip()
    return ""


@app.get("/admin/brand")
def admin_brand(client_token: str, db: Session = Depends(get_db)):
    """Public (comme /widget-config) : sert a habiller la page de connexion."""
    c = db.query(Client).filter(Client.token == client_token).first()
    if not c:
        raise HTTPException(status_code=404)
    b = client_brand(c, db)
    return {"name": b["name"], "color": b["color"], "domain": b["domain"]}


@app.post("/admin/login")
def admin_login(data: dict, db: Session = Depends(get_db)):
    c = check_admin(data.get("client_token", ""), data.get("password", ""), db)
    b = client_brand(c, db)
    return {"ok": True, "business_name": b["name"], **b}


@app.get("/admin/conversations")
def admin_conversations(client_token: str, request: Request, db: Session = Depends(get_db)):
    check_admin(client_token, request.headers.get("X-Admin-Password", ""), db)
    convs = db.query(Conversation).filter(
        Conversation.client_token == client_token
    ).order_by(Conversation.created_at.desc()).all()
    states = conversation_rows(client_token, db)
    by_conv = messages_by_conversation(client_token, db)
    result = []
    for conv in convs:
        msgs = by_conv.get(conv.id, [])
        state, handled = states.get(conv.id, (STATE_NORMAL, False))
        needs_human = state == STATE_DONE
        result.append({
            "id": conv.id,
            "created_at": fmt_local(conv.created_at),
            "message_count": len(msgs),
            "preview": first_question(msgs)[:140],
            "needs_human": needs_human,
            "handled": handled,
            "contact_info": lead_contact(msgs) if needs_human else None,
            "state": state,
        })
    return result


@app.get("/admin/conversations/{conv_id}")
def admin_conversation_detail(conv_id: str, client_token: str, request: Request, db: Session = Depends(get_db)):
    check_admin(client_token, request.headers.get("X-Admin-Password", ""), db)
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id, Conversation.client_token == client_token
    ).first()
    if not conv:
        raise HTTPException(status_code=404)
    msgs = db.query(MessageModel).filter(
        MessageModel.conversation_id == conv_id
    ).order_by(MessageModel.created_at).all()
    return [{"role": m.role, "content": m.content, "at": fmt_local(m.created_at)} for m in msgs]


class HandledRequest(BaseModel):
    handled: bool = True


@app.post("/admin/conversations/{conv_id}/handled")
def admin_mark_handled(conv_id: str, client_token: str, req: HandledRequest, request: Request,
                       db: Session = Depends(get_db)):
    check_admin(client_token, request.headers.get("X-Admin-Password", ""), db)
    res = db.execute(text(
        "UPDATE conversations SET handled = :h WHERE id = :id AND client_token = :t"
    ), {"h": bool(req.handled), "id": conv_id, "t": client_token})
    db.commit()
    if res.rowcount == 0:
        raise HTTPException(status_code=404)
    return {"ok": True, "handled": bool(req.handled)}


# Themes des questions : calcules par l'IA, gardes 1 h en memoire par client
TOPICS_CACHE = {}   # (token, days) -> (timestamp, cle, themes)
TOPICS_TTL = 3600


def question_topics(token: str, days: int, questions: list) -> list:
    if len(questions) < 3:
        return []
    key = (len(questions), questions[0][:40])
    cached = TOPICS_CACHE.get((token, days))
    if cached and cached[1] == key and time.time() - cached[0] < TOPICS_TTL:
        return cached[2]
    sample = questions[:150]
    try:
        response = client.with_options(timeout=20, max_retries=1).chat.completions.create(
            model="gpt-4.1-mini",
            max_tokens=500,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": (
                    "Tu analyses les premieres questions posees par les visiteurs d'une boutique en ligne. "
                    "Regroupe-les en 5 themes au maximum, du plus frequent au moins frequent. "
                    "Pour chaque theme : un titre court en francais (3 a 6 mots, ex. 'Delais de livraison'), "
                    "le nombre de questions concernees, et un exemple reel tire de la liste (reformule en 12 mots max). "
                    "Ignore les salutations seules. Reponds en JSON : "
                    "{\"themes\": [{\"title\": str, \"count\": int, \"example\": str}]}"
                )},
                {"role": "user", "content": "\n".join("- " + q[:200] for q in sample)},
            ],
        )
        data = json.loads(response.choices[0].message.content or "{}")
        themes = []
        for t in data.get("themes", [])[:5]:
            title = str(t.get("title", "")).strip()[:60]
            if not title:
                continue
            themes.append({
                "title": title,
                "count": max(0, min(int(t.get("count") or 0), len(sample))),
                "example": str(t.get("example", "")).strip()[:120],
            })
        TOPICS_CACHE[(token, days)] = (time.time(), key, themes)
        return themes
    except Exception as e:
        print("TOPICS ERROR:", e)
        return cached[2] if cached else []


@app.get("/admin/overview")
def admin_overview(client_token: str, request: Request, days: int = 30, db: Session = Depends(get_db)):
    """Chiffres de la periode : conversations, clients a rappeler, heures, themes."""
    check_admin(client_token, request.headers.get("X-Admin-Password", ""), db)
    days = max(1, min(int(days or 30), 365))
    now_utc = datetime.utcnow()
    since = now_utc - timedelta(days=days)
    prev_since = since - timedelta(days=days)

    states = conversation_rows(client_token, db)
    convs = db.query(Conversation).filter(
        Conversation.client_token == client_token, Conversation.created_at >= prev_since
    ).all()
    by_conv = messages_by_conversation(client_token, db, since=prev_since)

    current = [c for c in convs if c.created_at and c.created_at >= since]
    previous_count = sum(
        1 for c in convs if c.created_at and c.created_at < since and by_conv.get(c.id)
    )

    hours = [0] * 24
    local_today = to_local(now_utc).date()
    day_keys = [(local_today - timedelta(days=i)).isoformat() for i in range(days - 1, -1, -1)]
    per_day = {k: 0 for k in day_keys}
    conversations = 0
    visitor_messages = 0
    after_hours = 0
    leads_period = 0
    questions = []

    for conv in sorted(current, key=lambda c: c.created_at, reverse=True):
        msgs = by_conv.get(conv.id, [])
        user_msgs = [m for m in msgs if m.role == "user"]
        if not user_msgs:
            continue
        conversations += 1
        visitor_messages += len(user_msgs)
        start = to_local(user_msgs[0].created_at or conv.created_at)
        hours[start.hour] += 1
        if start.hour >= 20 or start.hour < 8 or start.weekday() >= 5:
            after_hours += 1
        k = start.date().isoformat()
        if k in per_day:
            per_day[k] += 1
        if states.get(conv.id, (STATE_NORMAL, False))[0] == STATE_DONE:
            leads_period += 1
        q = first_question(msgs)
        if q:
            questions.append(q)

    # Clients a rappeler : toutes periodes confondues, les non traites d'abord
    lead_ids = [cid for cid, (st, _) in states.items() if st == STATE_DONE]
    leads = []
    if lead_ids:
        lead_convs = db.query(Conversation).filter(Conversation.id.in_(lead_ids)).all()
        lead_msgs = {}
        for m in db.query(MessageModel).filter(
            MessageModel.conversation_id.in_(lead_ids)
        ).order_by(MessageModel.created_at).all():
            lead_msgs.setdefault(m.conversation_id, []).append(m)
        for conv in lead_convs:
            msgs = lead_msgs.get(conv.id, [])
            leads.append({
                "id": conv.id,
                "created_at": fmt_local(conv.created_at),
                "contact": lead_contact(msgs) or "",
                "question": first_question(msgs)[:160],
                "handled": states[conv.id][1],
            })
        leads.sort(key=lambda l: l["created_at"], reverse=True)   # plus recents d'abord
        leads.sort(key=lambda l: l["handled"])                    # puis non traites en tete
    open_leads = sum(1 for l in leads if not l["handled"])

    return {
        "days": days,
        "conversations": conversations,
        "previous_conversations": previous_count,
        "visitor_messages": visitor_messages,
        "after_hours": after_hours,
        "after_hours_pct": round(100 * after_hours / conversations) if conversations else 0,
        "leads_period": leads_period,
        "open_leads": open_leads,
        "hours": hours,
        "per_day": [{"date": k, "count": per_day[k]} for k in day_keys],
        "leads": leads[:50],
        "topics": question_topics(client_token, days, questions),
        "topics_sample": len(questions),
        "value": value_stats(client_token, db, since),
        "value_previous": value_stats(client_token, db, prev_since, since),
        "orders_ever": db.query(Event).filter(Event.client_token == client_token, Event.type == "order").count(),
    }


# ── Demandes de demo envoyees depuis aireply.fr ───────────────────────────────
# Elles arrivent comme des "clients a rappeler" dans le dashboard de Replai
# (client DEMO_LEADS_TOKEN) et par email a l'adresse de ce client.
DEMO_LEADS_TOKEN = os.getenv("DEMO_LEADS_TOKEN", "replai_cb23fd")
DEMO_RATE = {}   # ip -> [timestamps]


class DemoRequest(BaseModel):
    shop_url: str
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    lang: Optional[str] = None
    website: Optional[str] = None   # champ piege : invisible pour un humain, rempli par les robots


@app.post("/demo-request")
def demo_request(req: DemoRequest, request: Request, db: Session = Depends(get_db)):
    if req.website:
        return {"ok": True}
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "").split(",")[0].strip()
    now = time.time()
    recent = [t for t in DEMO_RATE.get(ip, []) if now - t < 3600]
    if len(recent) >= 5:
        raise HTTPException(status_code=429, detail="Trop de demandes, reessayez plus tard")
    DEMO_RATE[ip] = recent + [now]

    shop = (req.shop_url or "").strip()[:200]
    email = (req.email or "").strip()[:200]
    name = (req.name or "").strip()[:80]
    phone = (req.phone or "").strip()[:40]
    if len(shop) < 4 or not EMAIL_RE.fullmatch(email):
        raise HTTPException(status_code=400, detail="Adresse de boutique ou email invalide")

    c = db.query(Client).filter(Client.token == DEMO_LEADS_TOKEN).first()
    conv_id = str(uuid.uuid4())
    db.add(Conversation(id=conv_id, title="Demande de demo", client_token=DEMO_LEADS_TOKEN if c else None))
    db.commit()
    save_message(conv_id, "user", "Demande de démo pour la boutique : " + shop, db)
    contact = " · ".join(x for x in (name, email, phone) if x)
    save_message(conv_id, "user", contact, db)
    save_message(conv_id, "assistant", "Demande de démo reçue via le formulaire du site.", db)
    set_state(conv_id, STATE_DONE, db)

    if c and c.client_email:
        try:
            rows = [("Boutique", shop), ("Email", email), ("Prénom", name), ("Téléphone", phone),
                    ("Langue du site", (req.lang or "")[:5])]
            resend.Emails.send({
                "from": "Replai <noreply@gianluca-ai.fr>",
                "to": [c.client_email],
                "reply_to": email,
                "subject": "Nouvelle demande de démo - " + re.sub(r"^https?://(www\.)?", "", shop)[:80],
                "html": (
                    "<div style='font-family:Arial,sans-serif;max-width:600px'>"
                    "<h2 style='color:#4f46e5'>Nouvelle demande de démo</h2>"
                    + "".join("<p><strong>%s :</strong> %s</p>" % (k, html_lib.escape(v)) for k, v in rows if v)
                    + "<p>Répondez directement à cet email pour écrire au prospect.</p></div>"
                ),
            })
        except Exception as e:
            print("DEMO EMAIL ERROR:", e)
    return {"ok": True}


# ── Suivi de ce que le chat rapporte ──────────────────────────────────────────
# Le widget signale les clics vers les produits et les ajouts au panier.
# Les commandes arrivent par le pixel Shopify (attribut de panier "_replai")
# ou par le widget sur la page de confirmation WooCommerce.
TRACK_TYPES = {"product_click", "add_to_cart"}
ATTRIBUTION_DAYS = 30


async def _json_body(request: Request) -> dict:
    """Accepte JSON ou texte brut (le pixel Shopify envoie parfois en text/plain)."""
    try:
        data = json.loads((await request.body()) or b"{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _to_float(v) -> Optional[float]:
    try:
        f = float(str(v).replace(",", "."))
        return f if 0 <= f < 1_000_000 else None
    except (TypeError, ValueError):
        return None


def _short(v, n=80) -> Optional[str]:
    return str(v)[:n] if v not in (None, "") else None


@app.post("/track")
async def track(request: Request, db: Session = Depends(get_db)):
    d = await _json_body(request)
    token = _short(d.get("client_token"), 60)
    kind = d.get("type")
    if not token or kind not in TRACK_TYPES:
        raise HTTPException(status_code=400)
    if not db.query(Client).filter(Client.token == token).first():
        raise HTTPException(status_code=404)
    db.add(Event(id=str(uuid.uuid4()), client_token=token, conversation_id=_short(d.get("conversation_id")),
                 type=kind, product_id=_short(d.get("product_id")), variant_id=_short(d.get("variant_id")),
                 value=_to_float(d.get("value")), currency=_short(d.get("currency"), 3)))
    db.commit()
    return {"ok": True}


@app.post("/track-order")
async def track_order(request: Request, db: Session = Depends(get_db)):
    d = await _json_body(request)
    token = _short(d.get("client_token"), 60)
    conv_id = _short(d.get("conversation_id"))
    order_ref = _short(d.get("order_id"), 120)
    total = _to_float(d.get("total"))
    if not token or not conv_id or not order_ref or total is None:
        raise HTTPException(status_code=400)
    conv = db.query(Conversation).filter(Conversation.id == conv_id, Conversation.client_token == token).first()
    # Une vente n'est attribuee que si le client a vraiment parle a l'assistant recemment
    if not conv or not conv.created_at or conv.created_at < datetime.utcnow() - timedelta(days=ATTRIBUTION_DAYS):
        return {"ok": True, "attributed": False}
    has_visitor_msg = db.query(MessageModel).filter(
        MessageModel.conversation_id == conv_id, MessageModel.role == "user").first()
    if not has_visitor_msg:
        return {"ok": True, "attributed": False}
    exists = db.query(Event).filter(Event.client_token == token, Event.type == "order", Event.ref == order_ref).first()
    if exists:
        return {"ok": True, "attributed": True}
    db.add(Event(id=str(uuid.uuid4()), client_token=token, conversation_id=conv_id, type="order",
                 value=total, currency=_short(d.get("currency"), 3) or "EUR", ref=order_ref))
    db.commit()
    print("ORDER ATTRIBUTED:", token, order_ref, total)
    return {"ok": True, "attributed": True}


SHOPIFY_PIXEL_TEMPLATE = """// Replai : suivi des ventes generees par l'assistant
// A coller dans Shopify > Parametres > Evenements clients > Ajouter un pixel personnalise
analytics.subscribe("checkout_completed", (event) => {
  const checkout = event.data.checkout;
  const attr = (checkout.attributes || []).find((a) => a.key === "_replai");
  if (!attr || !attr.value) return;
  fetch("%(base)s/track-order", {
    method: "POST",
    keepalive: true,
    headers: { "Content-Type": "text/plain" },
    body: JSON.stringify({
      client_token: "%(token)s",
      conversation_id: attr.value,
      order_id: (checkout.order && checkout.order.id) || checkout.token,
      total: checkout.totalPrice && checkout.totalPrice.amount,
      currency: checkout.totalPrice && checkout.totalPrice.currencyCode,
    }),
  });
});
"""
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "https://ai-assistant-backend-clean-iz6y.onrender.com")


@app.get("/superadmin/pixel-code")
def pixel_code(token: str, superadmin_password: str):
    if superadmin_password != SUPERADMIN_PASSWORD:
        raise HTTPException(status_code=401)
    return PlainTextResponse(SHOPIFY_PIXEL_TEMPLATE % {"base": PUBLIC_BASE_URL, "token": token})


# ── Bulle d'accroche adaptee au produit regarde ──────────────────────────────
# Une phrase courte ecrite par l'IA a partir de la fiche produit (taille pour un
# vetement, dimensions pour un tableau...). Une seule generation par produit et
# par langue, gardee en memoire.
TEASER_CACHE = {}   # (shop, product_id, lang) -> texte
TEASER_LANGS = {"fr": "francais", "en": "anglais", "es": "espagnol", "it": "italien", "de": "allemand",
                "nl": "neerlandais", "pt": "portugais"}


def find_product(catalog: dict, page_url: str) -> Optional[dict]:
    key = _url_key(page_url or "")
    if not key:
        return None
    for p in catalog.get("products", []):
        if p.get("url") and _url_key(p["url"]) == key:
            return p
    return None


def fallback_teaser(p: dict, lang: str) -> str:
    sized = any(SIZE_OPTION_RE.search(o["name"]) for o in p.get("options", []))
    p = dict(p, title=p["title"].strip('"\u00ab\u00bb\u201c\u201d ') or p["title"])
    if lang == "fr":
        return ("Une question sur la taille de « %s » ? Je vous conseille tout de suite." if sized
                else "Une question sur « %s » ? Je vous réponds tout de suite.") % p["title"][:40]
    return ("Not sure about the size of “%s”? I can help right away." if sized
            else "Any question about “%s”? I can help right away.") % p["title"][:40]


def product_teaser(shop: str, p: dict, lang: str) -> str:
    key = (shop, p["id"], lang)
    if key in TEASER_CACHE:
        return TEASER_CACHE[key]
    info = "Produit : %s\nPrix : %s %s\nOptions : %s\nDisponible : %s\nInfos : %s" % (
        p["title"], p["price"], p["currency"],
        "; ".join("%s (%s)" % (o["name"], ", ".join(o["values"][:8])) for o in p["options"]) or "aucune",
        "oui" if p["available"] else "non",
        (p["fit"] + " " + p["desc"])[:400])
    text = ""
    try:
        r = client.with_options(timeout=8, max_retries=0).chat.completions.create(
            model="gpt-4.1-mini",
            max_tokens=60,
            messages=[
                {"role": "system", "content": (
                    "Tu ecris la petite bulle qui s'affiche a cote du chat d'une boutique en ligne quand un visiteur "
                    "regarde un produit. Une seule phrase, 95 caracteres maximum, ton chaleureux et naturel, "
                    "qui propose une aide UTILE ET SPECIFIQUE a CE produit (ex : la taille et la coupe pour un vetement, "
                    "les dimensions ou la matiere pour un tableau ou un objet, l'utilisation pour un soin...). "
                    "Appuie-toi uniquement sur les infos fournies, n'invente rien, aucun prix. "
                    "Ne dis jamais qu'un vetement taille normalement, grand ou petit si ce n'est pas ecrit tel quel : "
                    "'boxy' ou 'oversize' decrivent une coupe ample, pas une correspondance de taille. "
                    "Pas d'emoji, pas de guillemets autour de la phrase. Ecris en %s." % TEASER_LANGS.get(lang, "anglais")
                )},
                {"role": "user", "content": info},
            ],
        )
        text = (r.choices[0].message.content or "").strip().strip('"\u00ab\u00bb\u201c\u201d ').strip()
    except Exception as e:
        print("TEASER ERROR:", e)
    if not text or len(text) > 140:
        return fallback_teaser(p, lang)      # pas mis en cache : on reessaiera
    TEASER_CACHE[key] = text
    return text


@app.get("/teaser")
def teaser(token: str = "", url: str = "", lang: str = "fr", db: Session = Depends(get_db)):
    """Route publique appelee par le widget sur une page produit."""
    shop = get_shop_url(token, db) if token else ""
    if not shop:
        return {}
    p = find_product(get_catalog(shop), url)
    if not p:
        return {}
    lang = (lang or "fr")[:2].lower()
    return {"text": product_teaser(shop, p, lang if lang in TEASER_LANGS else "en"), "title": p["title"]}


WIDGET_SNIPPET = '<script src="%(base)s/static/ai-widget.js?token=%(token)s"></script>'


@app.get("/admin/install")
def admin_install(client_token: str, request: Request, db: Session = Depends(get_db)):
    """Codes a installer, deja remplis pour ce client, et etat de l'installation."""
    c = check_admin(client_token, request.headers.get("X-Admin-Password", ""), db)
    shop = get_shop_url(c.token, db)
    platform = get_catalog(shop)["platform"] if shop else ""
    seen = WIDGET_SEEN.get(c.token)
    last_conv = db.query(Conversation).filter(Conversation.client_token == c.token).order_by(
        Conversation.created_at.desc()).first()
    first_order = db.query(Event).filter(Event.client_token == c.token, Event.type == "order").order_by(
        Event.created_at).first()
    return {
        "platform": platform,
        "shop_url": shop,
        "widget_snippet": WIDGET_SNIPPET % {"base": PUBLIC_BASE_URL, "token": c.token},
        "pixel_code": SHOPIFY_PIXEL_TEMPLATE % {"base": PUBLIC_BASE_URL, "token": c.token},
        "widget_seen_at": fmt_local(seen[0]) if seen else None,
        "widget_seen_on": seen[1] if seen else None,
        "last_conversation_at": fmt_local(last_conv.created_at) if last_conv else None,
        "first_order_at": fmt_local(first_order.created_at) if first_order else None,
    }


def value_stats(token: str, db: Session, since: datetime, until: Optional[datetime] = None) -> dict:
    q = db.query(Event).filter(Event.client_token == token, Event.created_at >= since)
    if until is not None:
        q = q.filter(Event.created_at < until)
    stats = {"product_clicks": 0, "add_to_cart": 0, "orders": 0, "revenue": 0.0, "currency": "EUR"}
    for e in q.all():
        if e.type == "product_click":
            stats["product_clicks"] += 1
        elif e.type == "add_to_cart":
            stats["add_to_cart"] += 1
        elif e.type == "order":
            stats["orders"] += 1
            stats["revenue"] += e.value or 0.0
            stats["currency"] = e.currency or stats["currency"]
    stats["revenue"] = round(stats["revenue"], 2)
    return stats


# ── Rapport mensuel envoye au client ──────────────────────────────────────────
# Chaque debut de mois, chaque client recoit par email ce que son assistant a
# fait le mois precedent : la preuve concrete de ce que Replai lui apporte.
MONTHS_FR_ACC = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
                 "septembre", "octobre", "novembre", "décembre"]


def month_bounds(year: int, month: int):
    """Debut et fin du mois (heure de Paris), convertis en UTC naif comme en base."""
    start = datetime(year, month, 1, tzinfo=LOCAL_TZ)
    end = datetime(year + (month == 12), month % 12 + 1, 1, tzinfo=LOCAL_TZ)
    to_utc = lambda d: d.astimezone(timezone.utc).replace(tzinfo=None)
    return to_utc(start), to_utc(end)


def period_summary(token: str, db: Session, start: datetime, end: datetime) -> dict:
    states = conversation_rows(token, db)
    by_conv = messages_by_conversation(token, db, since=start)
    convs = db.query(Conversation).filter(Conversation.client_token == token,
                                          Conversation.created_at >= start, Conversation.created_at < end).all()
    total = after = leads = msgs = 0
    for conv in convs:
        user_msgs = [m for m in by_conv.get(conv.id, []) if m.role == "user"]
        if not user_msgs:
            continue
        total += 1
        msgs += len(user_msgs)
        t = to_local(user_msgs[0].created_at or conv.created_at)
        if t.hour >= 20 or t.hour < 8 or t.weekday() >= 5:
            after += 1
        if states.get(conv.id, (STATE_NORMAL, False))[0] == STATE_DONE:
            leads += 1
    return {"conversations": total, "after_hours": after, "leads": leads, "visitor_messages": msgs,
            "value": value_stats(token, db, start, end)}


def _eur(v: float) -> str:
    s = ("%.2f" % v).replace(".", ",")
    s = s[:-3] if s.endswith(",00") else s
    return s + " €"


def report_email_html(name: str, month_label: str, s: dict, dashboard_url: str, color: str) -> str:
    v = s["value"]
    rows = [
        ("Conversations avec vos clients", str(s["conversations"])),
        ("Dont le soir, la nuit ou le week-end", str(s["after_hours"])),
        ("Questions répondues", str(s["visitor_messages"])),
        ("Clients à rappeler transmis", str(s["leads"])),
        ("Clics vers vos produits", str(v["product_clicks"])),
        ("Ajouts au panier depuis le chat", str(v["add_to_cart"])),
    ]
    if v["orders"]:
        rows.append(("Commandes après une conversation", "%d (%s)" % (v["orders"], _eur(v["revenue"]))))
    accent = color if HEX_RE.match(color or "") else "#4f46e5"
    highlight = ""
    if v["orders"]:
        highlight = ("<p style='font-size:28px;font-weight:700;margin:8px 0 0;color:%s'>%s</p>"
                     "<p style='margin:4px 0 0;color:#475569'>de ventes après une conversation avec l'assistant</p>"
                     % (accent, _eur(v["revenue"])))
    elif s["after_hours"]:
        highlight = ("<p style='font-size:28px;font-weight:700;margin:8px 0 0;color:%s'>%d</p>"
                     "<p style='margin:4px 0 0;color:#475569'>clients accompagnés quand votre boutique était fermée</p>"
                     % (accent, s["after_hours"]))
    table = "".join(
        "<tr><td style='padding:10px 0;border-bottom:1px solid #eef0f3;color:#475569'>%s</td>"
        "<td style='padding:10px 0;border-bottom:1px solid #eef0f3;text-align:right;font-weight:600'>%s</td></tr>"
        % (html_lib.escape(k), html_lib.escape(val)) for k, val in rows)
    return (
        "<div style='font-family:Arial,sans-serif;max-width:560px;margin:0 auto;color:#0f172a'>"
        "<p style='color:#94a3b8;font-size:13px;margin:0'>Rapport mensuel · %s</p>"
        "<h1 style='font-size:22px;margin:6px 0 0'>Votre assistant en %s</h1>%s"
        "<table style='width:100%%;border-collapse:collapse;margin-top:22px;font-size:15px'>%s</table>"
        "<p style='margin-top:24px'><a href='%s' style='background:%s;color:#fff;padding:12px 18px;"
        "border-radius:10px;text-decoration:none;font-weight:600'>Voir le détail dans mon espace</a></p>"
        "<p style='color:#94a3b8;font-size:12px;margin-top:28px'>Replai · l'assistant de votre boutique</p></div>"
    ) % (html_lib.escape(name), month_label, highlight, table, html_lib.escape(dashboard_url), accent)


def send_monthly_report(c: Client, year: int, month: int, db: Session, force: bool = False) -> str:
    log_id = "%s:%04d-%02d" % (c.token, year, month)
    if not force and db.query(ReportLog).filter(ReportLog.id == log_id).first():
        return "deja envoye"
    if not c.client_email:
        return "pas d'email"
    start, end = month_bounds(year, month)
    s = period_summary(c.token, db, start, end)
    if not s["conversations"] and not force:
        return "aucune conversation"
    brand = client_brand(c, db)
    label = MONTHS_FR_ACC[month - 1] + " " + str(year)
    v = s["value"]
    subject = "Votre assistant en %s : %d conversation%s" % (
        MONTHS_FR_ACC[month - 1], s["conversations"], "s" if s["conversations"] > 1 else "")
    if v["orders"]:
        subject += ", " + _eur(v["revenue"]) + " de ventes"
    try:
        resend.Emails.send({
            "from": "Replai <noreply@gianluca-ai.fr>",
            "to": [c.client_email],
            "subject": subject,
            "html": report_email_html(brand["name"], label, s,
                                      PUBLIC_BASE_URL + "/admin?token=" + c.token, brand["color"]),
        })
    except Exception as e:
        print("REPORT EMAIL ERROR:", c.token, e)
        return "erreur : %s" % e
    if not db.query(ReportLog).filter(ReportLog.id == log_id).first():
        db.add(ReportLog(id=log_id))
        db.commit()
    return "envoye"


def previous_month(now_local: datetime):
    return (now_local.year - 1, 12) if now_local.month == 1 else (now_local.year, now_local.month - 1)


class SendReportsRequest(BaseModel):
    superadmin_password: str
    token: Optional[str] = None      # un seul client (sinon tous)
    month: Optional[str] = None      # "2026-10" (sinon le mois precedent)
    force: bool = False              # renvoyer meme si deja envoye / vide (pour tester)


@app.post("/superadmin/send-reports")
def send_reports(req: SendReportsRequest, db: Session = Depends(get_db)):
    if req.superadmin_password != SUPERADMIN_PASSWORD:
        raise HTTPException(status_code=401, detail="Non autorise")
    if req.month and re.fullmatch(r"\d{4}-\d{2}", req.month):
        year, month = int(req.month[:4]), int(req.month[5:])
    else:
        year, month = previous_month(datetime.now(LOCAL_TZ))
    q = db.query(Client)
    if req.token:
        q = q.filter(Client.token == req.token)
    return {c.token: send_monthly_report(c, year, month, db, req.force) for c in q.all()}


def _reports_loop():
    """Envoie automatiquement les rapports du mois precedent, les 3 premiers jours du mois apres 9 h."""
    while True:
        try:
            now = datetime.now(LOCAL_TZ)
            if now.day <= 3 and now.hour >= 9:
                year, month = previous_month(now)
                db = SessionLocal()
                try:
                    for c in db.query(Client).all():
                        result = send_monthly_report(c, year, month, db)
                        if result == "envoye":
                            print("REPORT SENT:", c.token, year, month)
                finally:
                    db.close()
        except Exception as e:
            print("REPORTS LOOP ERROR:", e)
        time.sleep(3600)


@app.on_event("startup")
def start_reports_loop():
    if os.getenv("REPORTS_AUTO", "1") != "0":
        import threading
        threading.Thread(target=_reports_loop, daemon=True).start()


@app.post("/contact-human")
def contact_human(req: ContactHumanRequest, db: Session = Depends(get_db)):
    conv_id = req.conversation_id or str(uuid.uuid4())
    client_token = req.client_token or ""
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        conv = Conversation(id=conv_id, title="Conversation client", client_token=client_token)
        db.add(conv)
        db.commit()
    visitor_msgs = get_visitor_messages(conv_id, db)
    reply = translate_to_visitor_language(MSG_ASKING, visitor_msgs, page_lang_hint(req.page_lang))
    set_state(conv_id, STATE_ASKING, db)
    save_message(conv_id, "assistant", reply, db)
    return bot_reply(reply, conv_id, False)


@app.post("/chat")
def chat(msg: ChatRequest, db: Session = Depends(get_db)):
    conv_id = msg.conversation_id or str(uuid.uuid4())
    client_token = msg.client_token or ""
    c = db.query(Client).filter(Client.token == client_token).first()

    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        conv = Conversation(id=conv_id, title="Conversation client", client_token=client_token)
        db.add(conv)
        db.commit()

    save_message(conv_id, "user", msg.message, db)
    state = get_state(conv_id, db)
    visitor_msgs = get_visitor_messages(conv_id, db)
    page_lang = page_lang_hint(msg.page_lang)

    if state == STATE_ASKING:
        if contains_contact_info(msg.message):
            if c:
                send_human_email(conv_id, msg.message, c)
            set_state(conv_id, STATE_DONE, db)
            reply = translate_to_visitor_language(MSG_CONFIRMED, visitor_msgs, page_lang)
            save_message(conv_id, "assistant", reply, db)
            return bot_reply(reply, conv_id, True)
        label = classify_reply(msg.message, "asking")
        if label == "YES":
            reply = translate_to_visitor_language(MSG_ASKING, visitor_msgs, page_lang)
            save_message(conv_id, "assistant", reply, db)
            return bot_reply(reply, conv_id, False)
        set_state(conv_id, STATE_NORMAL, db)
        if label == "NO":
            reply = translate_to_visitor_language(MSG_DECLINED, visitor_msgs, page_lang)
            save_message(conv_id, "assistant", reply, db)
            return bot_reply(reply, conv_id, False)
        # OTHER : le visiteur a change de sujet -> reponse normale plus bas
        state = STATE_NORMAL

    if state == STATE_PROPOSED:
        label = classify_reply(msg.message, "proposal")
        if label == "YES":
            set_state(conv_id, STATE_ASKING, db)
            reply = translate_to_visitor_language(MSG_ASKING, visitor_msgs, page_lang)
            save_message(conv_id, "assistant", reply, db)
            return bot_reply(reply, conv_id, False)
        set_state(conv_id, STATE_NORMAL, db)
        if label == "NO":
            reply = translate_to_visitor_language(MSG_DECLINED, visitor_msgs, page_lang)
            save_message(conv_id, "assistant", reply, db)
            return bot_reply(reply, conv_id, False)
        # OTHER : nouvelle question -> reponse normale plus bas
        state = STATE_NORMAL

    if HUMAN_REGEX.search(msg.message):
        set_state(conv_id, STATE_PROPOSED, db)
        reply = translate_to_visitor_language(MSG_PROPOSAL, visitor_msgs, page_lang)
        save_message(conv_id, "assistant", reply, db)
        return bot_reply(reply, conv_id, False)

    history = db.query(MessageModel).filter(
        MessageModel.conversation_id == conv_id
    ).order_by(MessageModel.created_at).all()

    if c and c.system_prompt:
        base_prompt = c.system_prompt
    else:
        base_prompt = "Tu es un assistant virtuel professionnel."

    shop_url = get_shop_url(c.token, db) if c else ""
    catalog = get_catalog(shop_url) if shop_url else EMPTY_CATALOG
    if catalog["text"]:
        base_prompt += (
            "\n\nCATALOGUE EN TEMPS REEL (source de verite pour les produits, prix et stocks : "
            "si une autre information du prompt contredit ce catalogue, c'est le catalogue qui a raison. "
            "Ne propose jamais un produit ou une taille absent ou epuise) :\n" + catalog["text"]
        )
    if shop_url:
        site_info = get_site_info(shop_url)
        if site_info:
            base_prompt += (
                "\n\nINFOS DU SITE DE LA BOUTIQUE (newsletter, reseaux, livraison, retours). "
                "Utilise-les pour repondre ; si la premiere partie de ce prompt les contredit, "
                "c'est la premiere partie qui a raison :\n" + site_info
            )

    # Le texte de la page n'est utile que si le visiteur est sur le site du client
    # (sur la page demo d'aireply.fr, ce serait le texte marketing de Replai).
    page_ok = bool(msg.page_content)
    if page_ok and shop_url and msg.page_url and _host(msg.page_url) != _host(shop_url):
        page_ok = False
    if page_ok:
        base_prompt += "\n\nCONTENU DE LA PAGE CONSULTEE PAR LE VISITEUR :\n" + msg.page_content

    base_prompt += (
        "\n\nREGLES :\n"
        "- Reponds TOUJOURS dans la meme langue que le dernier message du visiteur\n"
        "- Reponds uniquement aux questions liees a l activite du business\n"
        "- Sois concis, professionnel et serviable\n"
        "- Si tu ne connais pas la reponse, dis-le simplement"
    )
    if catalog["products"]:
        base_prompt += (
            "\n\nVENDRE COMME UN BON VENDEUR EN BOUTIQUE :\n"
            "- Quand tu recommandes un produit, ecris son lien exact tel qu'il apparait dans le catalogue "
            "(une seule fois, sans le mettre entre crochets) : le site l'affiche sous forme de fiche avec photo, "
            "prix et bouton d'ajout au panier. 3 produits maximum par reponse.\n"
            "- Si le visiteur hesite, propose 1 ou 2 produits precis et disponibles plutot qu'une liste.\n"
            "- Ne mentionne jamais de prix, taille ou stock qui ne figure pas dans le catalogue.\n"
            "\nCONSEIL DE TAILLE (objectif : la bonne taille du premier coup, donc moins de retours) :\n"
            "- Si on te demande quelle taille prendre et que tu n'as pas les infos, demande en une seule question "
            "sa taille (en cm), son poids et s'il prefere porter ajuste ou ample.\n"
            "- Appuie-toi en priorite sur le guide des tailles de la boutique et sur les INFO TAILLE DU PRODUIT "
            "CONCERNE uniquement (jamais celles d'un autre produit : chaque modele a sa coupe et son mannequin). "
            "Sans ces infos, base-toi sur les correspondances usuelles et dis-le simplement.\n"
            "- Avec la taille du mannequin : compare-la a celle du client. En gros, une taille au-dessus tous les "
            "8 a 10 cm de plus, une en dessous tous les 8 a 10 cm de moins ; ajuste ensuite selon la corpulence "
            "(mince ou carre) et la preference ajuste/ample. Pour une personne grande et mince, la longueur compte "
            "plus que la largeur. Cite le chiffre du mannequin dans ta raison.\n"
            "- Donne UNE taille precise, avec la raison en une phrase (ex : 'Prenez un M : la coupe est ample, "
            "un L serait trop long pour 1m75'). Entre deux tailles, choisis selon sa preference ajuste/ample.\n"
            "- Verifie que la taille conseillee est disponible ; si elle est epuisee, dis-le clairement, puis propose "
            "la taille disponible la plus proche en expliquant la difference (ex : 'le L serait ideal mais il est "
            "epuise ; le M vous ira plus court').\n"
            "- Dans ta reponse, ne cite qu'une seule taille (celle que tu conseilles) : n'enumere pas toutes les "
            "tailles disponibles, la fiche produit affichee sous ton message permet deja de les voir.\n"
            "- N'invente jamais de mesures (tour de poitrine, longueur...) absentes des informations de la boutique."
        )

    messages_for_openai = [{"role": "system", "content": base_prompt}]
    for m in history:
        messages_for_openai.append({"role": m.role, "content": m.content})

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages_for_openai
    )
    reply = response.choices[0].message.content

    if GPT_PROPOSES_HUMAN.search(reply):
        set_state(conv_id, STATE_PROPOSED, db)

    save_message(conv_id, "assistant", reply, db)
    return bot_reply(reply, conv_id, False, product_cards(reply, catalog))


app.mount("/static", StaticFiles(directory="static"), name="static")