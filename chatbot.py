from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
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
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

from database import SessionLocal, engine
from models import Base, Client, Conversation, Message as MessageModel

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

MSG_PROPOSAL  = "Souhaitez-vous etre contacte par notre equipe ?"
MSG_ASKING    = "Parfait ! Donnez-moi votre prenom et votre numero de telephone, notre equipe vous contactera rapidement."
MSG_CONFIRMED = "Merci ! Notre equipe va vous contacter tres rapidement. A bientot !"
MSG_DECLINED  = "Pas de probleme, je reste a votre disposition si besoin !"


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

def translate_to_visitor_language(canonical_msg: str, visitor_messages: list) -> str:
    context = " | ".join(visitor_messages[-3:]) if visitor_messages else ""
    if not context:
        return canonical_msg
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            max_tokens=120,
            messages=[
                {"role": "system", "content": (
                    "Detect the language from the conversation context and translate the message into that language. "
                    "The context may contain multiple messages separated by | — use the overall language pattern, "
                    "not just the last message (which may contain a name or phone number). "
                    "Return ONLY the translated message, nothing else. "
                    "If the language is unclear, return the message in English."
                )},
                {"role": "user", "content": "Conversation context: " + context[:400] + "\n\nMessage to translate: " + canonical_msg}
            ]
        )
        result = response.choices[0].message.content.strip()
        return result if result else canonical_msg
    except Exception as e:
        print("TRANSLATE ERROR:", e)
        return canonical_msg


def classify_yes_no(visitor_message: str) -> bool:
    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            max_tokens=5,
            messages=[
                {"role": "system", "content": (
                    "The user was asked if they want to be contacted by a team member. "
                    "Classify their reply. Answer ONLY with YES or NO. "
                    "YES = they accept (any language: oui, yes, si, ja, da, hai, etc. or any positive phrasing). "
                    "NO = they decline or refuse."
                )},
                {"role": "user", "content": visitor_message[:300]}
            ]
        )
        return "YES" in response.choices[0].message.content.upper()
    except Exception as e:
        print("CLASSIFY ERROR:", e)
        t = visitor_message.strip().lower()
        negative = re.compile(r'\b(non|no|nope|nein|nee|nej|niet|nao|jamais|never|not)\b', re.IGNORECASE)
        if negative.search(t):
            return False
        return len(t.split()) <= 8


def contains_contact_info(message: str) -> bool:
    digits = re.sub(r'\D', '', message)
    return len(digits) >= 6


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


def bot_reply(text_content: str, conv_id: str, needs_human: bool = False):
    return {"reply": text_content, "conversation_id": conv_id, "needs_human": needs_human}


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
                + contact_info +
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


# ── Catalogue Shopify automatique ─────────────────────────────────────────────
# Chaque boutique Shopify expose publiquement /products.json (sans cle API).
# On le lit, on le met en cache, et on l'injecte dans le prompt : les nouveaux
# drops, prix et ruptures de stock sont connus du bot sans intervention.
CATALOG_TTL = 1800          # secondes (30 min)
CATALOG_MAX_CHARS = 40000   # ~10k tokens : ~150 produits avec description courte
CATALOG_CACHE = {}          # shop_url -> (timestamp, texte)


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


def _stock_text(p: dict, variants: list) -> str:
    # Un seul variant "Default Title" = produit sans taille/couleur
    if len(variants) == 1 and variants[0].get("title") == "Default Title":
        return "en stock" if variants[0].get("available") else "RUPTURE DE STOCK"
    if not any(v.get("available") for v in variants):
        return "RUPTURE DE STOCK (toutes tailles)"
    options = p.get("options") or []
    if len(options) <= 1:
        dispo = [v.get("title") for v in variants if v.get("available")]
        epuise = [v.get("title") for v in variants if not v.get("available")]
        txt = "disponible : " + ", ".join(dispo)
        return txt + (" | epuise : " + ", ".join(epuise) if epuise else "")
    # Plusieurs options (ex : taille x couleur) : on resume option par option,
    # sinon une bague en 15 tailles x 4 pierres ferait 60 variantes sur une ligne.
    parts = []
    for i, opt in enumerate(options[:3], 1):
        key = "option%d" % i
        all_vals = _uniq(opt.get("values") or [v.get(key) for v in variants])
        dispo = _uniq(v.get(key) for v in variants if v.get("available"))
        epuise = [x for x in all_vals if x not in dispo]
        part = "%s dispo : %s" % (opt.get("name") or "Option", ", ".join(dispo[:30]))
        if epuise:
            part += " (epuise : %s)" % ", ".join(epuise[:30])
        parts.append(part)
    return " | ".join(parts)


def format_catalog(products: list, shop_url: str) -> str:
    cores, descs = [], []
    for p in products:
        variants = p.get("variants") or []
        if not variants:
            continue
        prices = [float(v["price"]) for v in variants if v.get("price")]
        compares = [float(v["compare_at_price"]) for v in variants if v.get("compare_at_price")]
        price = min(prices) if prices else None
        line = "- " + (p.get("title") or "Produit")
        if price is not None:
            line += " : %.2f EUR" % price
            if compares and max(compares) > price:
                line += " (au lieu de %.2f EUR)" % max(compares)
        line += " | " + _stock_text(p, variants)
        if p.get("handle"):
            line += " | " + shop_url + "/products/" + p["handle"]
        cores.append(line)
        descs.append(strip_html(p.get("body_html", "")))

    # Priorite : que TOUS les produits tiennent dans le prompt. On raccourcit
    # les descriptions avant de supprimer des produits.
    for desc_len in (250, 120, 60, 0):
        lines = [c + (" | " + d[:desc_len] if d and desc_len else "") for c, d in zip(cores, descs)]
        out = "\n".join(lines)
        if len(out) <= CATALOG_MAX_CHARS:
            return out
    kept = out[:CATALOG_MAX_CHARS].rsplit("\n", 1)[0]
    missing = len(lines) - kept.count("\n") - 1
    return kept + "\n(... %d autres produits non listes ici : voir %s/collections/all)" % (missing, shop_url)


def get_catalog_text(shop_url: str) -> str:
    """Catalogue formate, avec cache. En cas d'erreur, renvoie la derniere
    version connue (ou "" si aucune) : le chat ne doit jamais planter a cause de Shopify."""
    if not shop_url:
        return ""
    now = time.time()
    cached = CATALOG_CACHE.get(shop_url)
    if cached and now - cached[0] < CATALOG_TTL:
        return cached[1]
    try:
        r = httpx.get(
            shop_url + "/products.json",
            params={"limit": 250},
            timeout=5.0,
            follow_redirects=True,
            headers={"User-Agent": "Replai-Catalog/1.0"},
        )
        r.raise_for_status()
        catalog = format_catalog(r.json().get("products", []), shop_url)
        CATALOG_CACHE[shop_url] = (now, catalog)
        print("CATALOG OK:", shop_url, len(catalog), "chars")
        return catalog
    except Exception as e:
        print("CATALOG ERROR:", shop_url, e)
        # On garde l'ancienne version (ou rien) et on ne reessaie que dans 5 min,
        # pour ne pas ralentir chaque message si la boutique est injoignable.
        previous = cached[1] if cached else ""
        CATALOG_CACHE[shop_url] = (now - CATALOG_TTL + 300, previous)
        return previous


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
    client_token: Optional[str] = None

class ContactHumanRequest(BaseModel):
    conversation_id: Optional[str] = None
    client_token: Optional[str] = None

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

    if any(x is not None for x in (req.widget_color, req.widget_mode, req.assistant_name, req.welcome_message)):
        if req.widget_color and not HEX_RE.match(req.widget_color):
            raise HTTPException(status_code=400, detail="widget_color doit etre au format #rrggbb")
        if req.widget_mode and req.widget_mode not in ("light", "dark"):
            raise HTTPException(status_code=400, detail="widget_mode doit etre light ou dark")
        cfg = get_widget_config(c.token, db)
        for key, val in (("color", req.widget_color), ("mode", req.widget_mode),
                         ("assistant_name", req.assistant_name), ("welcome", req.welcome_message)):
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


@app.get("/widget-config")
def widget_config(token: str = "", db: Session = Depends(get_db)):
    """Route publique lue par le widget au chargement : uniquement l'apparence."""
    cfg = get_widget_config(token, db) if token else {}
    return {k: cfg.get(k) for k in ("color", "mode", "assistant_name", "welcome") if cfg.get(k)}


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
ADMIN_HTML = """<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Replai Admin</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Inter', sans-serif; background: #0f1117; color: #e2e8f0; min-height: 100vh; }

    /* ── LOGIN ── */
    #login { display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 16px; }
    .card { background: #1a1d27; border: 1px solid #2d3148; border-radius: 16px; padding: 40px 32px; width: 100%; max-width: 380px; text-align: center; }
    .logo { width: 52px; height: 52px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 14px; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; font-size: 24px; }
    .card h2 { font-size: 22px; font-weight: 700; color: #f1f5f9; margin-bottom: 6px; }
    .card .sub { font-size: 14px; color: #64748b; margin-bottom: 28px; }
    .pwd-row { position: relative; margin-bottom: 12px; }
    .pwd-row input { width: 100%; padding: 12px 44px 12px 16px; background: #0f1117; border: 1px solid #2d3148; border-radius: 10px; color: #f1f5f9; font-size: 15px; font-family: 'Inter', sans-serif; outline: none; }
    .pwd-row input:focus { border-color: #6366f1; }
    .eye { position: absolute; right: 14px; top: 50%; transform: translateY(-50%); cursor: pointer; font-size: 16px; user-select: none; }
    .btn-login { width: 100%; padding: 13px; background: linear-gradient(135deg, #6366f1, #8b5cf6); color: white; border: none; border-radius: 10px; font-size: 15px; font-weight: 600; font-family: 'Inter', sans-serif; cursor: pointer; }
    .btn-login:hover { opacity: 0.9; }
    .err { color: #f87171; font-size: 13px; margin-top: 12px; padding: 10px; background: rgba(127,29,29,0.2); border: 1px solid #7f1d1d; border-radius: 8px; display: none; }

    /* ── DASHBOARD ── */
    #dashboard { display: none; }

    /* ── TOP BAR (mobile) ── */
    .topbar { display: none; align-items: center; justify-content: space-between; padding: 14px 16px; background: #1a1d27; border-bottom: 1px solid #2d3148; position: sticky; top: 0; z-index: 100; }
    .topbar-brand { display: flex; align-items: center; gap: 8px; }
    .topbar-icon { width: 28px; height: 28px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 7px; display: flex; align-items: center; justify-content: center; font-size: 13px; }
    .topbar-name { font-size: 14px; font-weight: 600; color: #f1f5f9; }
    .btn-menu { background: #0f1117; border: 1px solid #2d3148; border-radius: 8px; color: #94a3b8; font-size: 18px; width: 36px; height: 36px; cursor: pointer; display: flex; align-items: center; justify-content: center; }

    /* ── STATS BAR (mobile) ── */
    .stats-bar { display: none; gap: 8px; padding: 12px 16px; background: #0f1117; border-bottom: 1px solid #2d3148; overflow-x: auto; }
    .stats-bar::-webkit-scrollbar { display: none; }
    .stat-pill { background: #1a1d27; border: 1px solid #2d3148; border-radius: 10px; padding: 10px 14px; flex-shrink: 0; text-align: center; min-width: 80px; }
    .stat-pill .sp-n { display: block; font-size: 20px; font-weight: 700; color: #f1f5f9; line-height: 1; }
    .stat-pill .sp-l { font-size: 10px; color: #64748b; margin-top: 3px; display: block; }
    .stat-pill.highlight { border-color: #6366f1; background: rgba(99,102,241,0.08); }
    .stat-pill.highlight .sp-n { color: #818cf8; }
    .stat-pill.success .sp-n { color: #34d399; }

    /* ── DESKTOP LAYOUT ── */
    .layout { display: flex; height: 100vh; }
    .sidebar { width: 280px; background: #1a1d27; border-right: 1px solid #2d3148; display: flex; flex-direction: column; flex-shrink: 0; }
    .sb-top { padding: 20px; border-bottom: 1px solid #2d3148; }
    .brand { display: flex; align-items: center; gap: 10px; margin-bottom: 16px; }
    .brand-icon { width: 32px; height: 32px; background: linear-gradient(135deg, #6366f1, #8b5cf6); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 15px; }
    .brand-name { font-size: 15px; font-weight: 600; color: #f1f5f9; }

    /* Stats desktop — 3 colonnes */
    .stats-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-bottom: 10px; }
    .stat { background: #0f1117; border: 1px solid #2d3148; border-radius: 8px; padding: 8px 6px; text-align: center; }
    .stat.highlight { border-color: #6366f1; background: rgba(99,102,241,0.08); }
    .stat.success { }
    .stat-n { display: block; font-size: 17px; font-weight: 700; color: #f1f5f9; }
    .stat.highlight .stat-n { color: #818cf8; }
    .stat.success .stat-n { color: #34d399; }
    .stat-l { font-size: 10px; color: #64748b; }

    .sb-mid { padding: 12px 16px; border-bottom: 1px solid #2d3148; display: flex; flex-direction: column; gap: 8px; }
    .search-input { width: 100%; padding: 8px 12px; background: #0f1117; border: 1px solid #2d3148; border-radius: 8px; color: #f1f5f9; font-size: 13px; font-family: 'Inter', sans-serif; outline: none; }
    .search-input:focus { border-color: #6366f1; }
    .btn-refresh { width: 100%; padding: 9px; background: #0f1117; border: 1px solid #2d3148; border-radius: 8px; color: #94a3b8; font-size: 13px; font-family: 'Inter', sans-serif; cursor: pointer; }
    .btn-refresh:hover { border-color: #6366f1; color: #6366f1; }
    .conv-list { flex: 1; overflow-y: auto; padding: 8px; }
    .conv-list::-webkit-scrollbar { width: 3px; }
    .conv-list::-webkit-scrollbar-thumb { background: #2d3148; border-radius: 2px; }
    .ci { padding: 12px 14px; border-radius: 10px; margin-bottom: 4px; cursor: pointer; border: 1px solid transparent; }
    .ci:hover { background: #0f1117; border-color: #2d3148; }
    .ci.active { background: #1e2035; border-color: #6366f1; }
    .ci.urgent { border-left: 3px solid #f87171; }
    .ci-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
    .ci-id { font-size: 13px; font-weight: 500; color: #e2e8f0; font-family: monospace; }
    .badge { background: #7f1d1d; color: #fca5a5; font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 20px; }
    .ci-meta { font-size: 11px; color: #475569; }
    .contact-info { background: rgba(79,142,255,0.1); border: 1px solid rgba(79,142,255,0.3); border-radius: 8px; padding: 6px 10px; margin-top: 6px; font-size: 12px; color: #4f8eff; }
    .sb-bot { padding: 12px 16px; border-top: 1px solid #2d3148; }
    .btn-logout { width: 100%; padding: 8px; background: transparent; border: 1px solid #2d3148; border-radius: 8px; color: #64748b; font-size: 12px; font-family: 'Inter', sans-serif; cursor: pointer; }
    .btn-logout:hover { border-color: #f87171; color: #f87171; }
    .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }
    .main-hdr { padding: 20px 28px; border-bottom: 1px solid #2d3148; background: #1a1d27; flex-shrink: 0; }
    .main-hdr h2 { font-size: 15px; font-weight: 600; color: #f1f5f9; }
    .main-hdr p { font-size: 13px; color: #475569; margin-top: 3px; }
    .msgs-area { flex: 1; overflow-y: auto; padding: 24px 28px; }
    .msgs-area::-webkit-scrollbar { width: 3px; }
    .msgs-area::-webkit-scrollbar-thumb { background: #2d3148; border-radius: 2px; }
    .empty { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #2d3148; }
    .empty-icon { font-size: 52px; margin-bottom: 16px; }
    .empty p { font-size: 15px; }
    .msgs-wrap { display: flex; flex-direction: column; gap: 14px; }
    .msg { display: flex; flex-direction: column; max-width: 72%; }
    .msg.user { align-self: flex-end; }
    .msg.assistant { align-self: flex-start; }
    .msg-who { font-size: 11px; color: #475569; margin-bottom: 4px; padding: 0 4px; }
    .msg.user .msg-who { text-align: right; }
    .msg-text { padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.6; }
    .msg.user .msg-text { background: #312e81; color: #e0e7ff; border-bottom-right-radius: 3px; }
    .msg.assistant .msg-text { background: #1e2035; color: #cbd5e1; border: 1px solid #2d3148; border-bottom-left-radius: 3px; }

    /* ── MOBILE DRAWER ── */
    .drawer-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 200; }
    .drawer { position: fixed; left: 0; top: 0; bottom: 0; width: 300px; background: #1a1d27; border-right: 1px solid #2d3148; z-index: 201; display: flex; flex-direction: column; transform: translateX(-100%); transition: transform 0.25s ease; }
    .drawer.open { transform: translateX(0); }
    .drawer-header { padding: 16px; border-bottom: 1px solid #2d3148; display: flex; align-items: center; justify-content: space-between; }
    .drawer-header .brand { margin-bottom: 0; }
    .btn-close { background: transparent; border: none; color: #64748b; font-size: 20px; cursor: pointer; padding: 4px; }

    /* ── MOBILE VIEW ── */
    .mobile-conv-list { flex: 1; overflow-y: auto; padding: 8px; }
    .mobile-conv-list::-webkit-scrollbar { width: 3px; }
    .mobile-main { display: none; flex-direction: column; min-height: 0; }
    .mobile-main.visible { display: flex; flex: 1; }
    .mobile-msgs { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; }
    .btn-back { display: none; align-items: center; gap: 6px; padding: 10px 16px; background: transparent; border: none; border-bottom: 1px solid #2d3148; color: #818cf8; font-size: 14px; font-family: 'Inter', sans-serif; cursor: pointer; width: 100%; text-align: left; }

    /* ── RESPONSIVE ── */
    @media (max-width: 768px) {
      .layout { display: none !important; }
      .topbar { display: flex; }
      .stats-bar { display: flex; }
      .mobile-main { display: none; }
      .mobile-main.visible { display: flex; flex-direction: column; }
      .btn-back { display: flex; }
      #mobileConvSection { display: block; }
    }

    @media (min-width: 769px) {
      .topbar { display: none !important; }
      .stats-bar { display: none !important; }
      .drawer-overlay { display: none !important; }
      .drawer { display: none !important; }
      #mobileConvSection { display: none !important; }
      .mobile-main { display: none !important; }
      .btn-back { display: none !important; }
      .layout { display: flex !important; height: 100vh; }
    }
  </style>
</head>
<body>

<!-- ══ LOGIN ══ -->
<div id="login">
  <div class="card">
    <div class="logo">&#129302;</div>
    <h2>Replai Admin</h2>
    <p class="sub">Connectez-vous pour acceder au dashboard</p>
    <div class="pwd-row">
      <input type="password" id="pwd" placeholder="Mot de passe" />
      <span class="eye" id="eyeBtn">&#128065;</span>
    </div>
    <button class="btn-login" id="loginBtn">Se connecter</button>
    <div class="err" id="errMsg">Mot de passe incorrect</div>
  </div>
</div>

<!-- ══ DASHBOARD ══ -->
<div id="dashboard">

  <!-- TOP BAR mobile -->
  <div class="topbar">
    <div class="topbar-brand">
      <div class="topbar-icon">&#129302;</div>
      <span class="topbar-name" id="topbarName">Replai</span>
    </div>
    <div style="display:flex;gap:8px">
      <button class="btn-menu" id="refreshBtnMobile" title="Rafraichir">&#8635;</button>
      <button class="btn-menu" id="menuBtn">&#9776;</button>
    </div>
  </div>

  <!-- STATS BAR mobile -->
  <div class="stats-bar" id="statsBarMobile">
    <div class="stat-pill highlight">
      <span class="sp-n" id="mLeads">0</span>
      <span class="sp-l">Leads</span>
    </div>
    <div class="stat-pill">
      <span class="sp-n" id="mTotal">0</span>
      <span class="sp-l">Total</span>
    </div>
    <div class="stat-pill success">
      <span class="sp-n" id="mRate">0%</span>
      <span class="sp-l">Conversion</span>
    </div>
    <div class="stat-pill">
      <span class="sp-n" id="mMonth">0</span>
      <span class="sp-l">Ce mois</span>
    </div>
  </div>

  <!-- MOBILE: liste conversations -->
  <div id="mobileConvSection">
    <div style="padding:10px 16px 4px;border-bottom:1px solid #2d3148;">
      <input class="search-input" id="searchMobile" placeholder="&#128269; Rechercher..." style="width:100%" />
    </div>
    <div class="mobile-conv-list" id="mobileConvList" style="max-height:calc(100vh - 200px);overflow-y:auto;padding:8px"></div>
  </div>

  <!-- MOBILE: vue conversation -->
  <div class="mobile-main" id="mobileConvView">
    <button class="btn-back" id="backBtn">&#8592; Retour aux conversations</button>
    <div style="padding:14px 16px;border-bottom:1px solid #2d3148;background:#1a1d27;">
      <div style="font-size:14px;font-weight:600;color:#f1f5f9" id="mobileHdrTitle">Conversation</div>
      <div style="font-size:12px;color:#475569;margin-top:2px" id="mobileHdrSub"></div>
    </div>
    <div class="mobile-msgs" id="mobileMsgs"></div>
  </div>

  <!-- DRAWER (liste convs sur mobile) -->
  <div class="drawer-overlay" id="drawerOverlay"></div>
  <div class="drawer" id="drawer">
    <div class="drawer-header">
      <div class="brand">
        <div class="brand-icon">&#129302;</div>
        <span class="brand-name" id="drawerName">Replai</span>
      </div>
      <button class="btn-close" id="closeDrawer">&#10005;</button>
    </div>
    <div style="padding:10px 12px;border-bottom:1px solid #2d3148">
      <button class="btn-logout" id="logoutBtnMobile">Se deconnecter</button>
    </div>
  </div>

  <!-- DESKTOP LAYOUT -->
  <div class="layout">
    <div class="sidebar">
      <div class="sb-top">
        <div class="brand">
          <div class="brand-icon">&#129302;</div>
          <span class="brand-name" id="businessName">Replai</span>
        </div>
        <!-- Stats 3 colonnes -->
        <div class="stats-grid">
          <div class="stat highlight">
            <span class="stat-n" id="leadsN">0</span>
            <span class="stat-l">Leads</span>
          </div>
          <div class="stat">
            <span class="stat-n" id="totalN">0</span>
            <span class="stat-l">Total</span>
          </div>
          <div class="stat success">
            <span class="stat-n" id="rateN">0%</span>
            <span class="stat-l">Conv.</span>
          </div>
        </div>
        <div class="stats-grid" style="margin-top:6px">
          <div class="stat" style="grid-column:1/2">
            <span class="stat-n" id="monthN">0</span>
            <span class="stat-l">Ce mois</span>
          </div>
          <div class="stat" style="grid-column:2/4">
            <span class="stat-n" id="urgentN">0</span>
            <span class="stat-l">A rappeler</span>
          </div>
        </div>
      </div>
      <div class="sb-mid">
        <input class="search-input" id="searchInput" placeholder="&#128269; Rechercher..." />
        <button class="btn-refresh" id="refreshBtn">&#8635; Rafraichir</button>
      </div>
      <div class="conv-list" id="convList"></div>
      <div class="sb-bot">
        <button class="btn-logout" id="logoutBtn">Se deconnecter</button>
      </div>
    </div>
    <div class="main">
      <div class="main-hdr">
        <h2 id="hdrTitle">Conversations</h2>
        <p id="hdrSub">Selectionnez une conversation</p>
      </div>
      <div class="msgs-area" id="msgsArea">
        <div class="empty">
          <div class="empty-icon">&#128172;</div>
          <p>Selectionnez une conversation</p>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
var token = localStorage.getItem("wt") || "";
var clientToken = new URLSearchParams(window.location.search).get("token") || "";
var activeId = null;
var allConvs = [];
var isMobile = function() { return window.innerWidth <= 768; };
// Les messages viennent des visiteurs : on les echappe avant tout innerHTML
function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, function(ch) {
    return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[ch];
  });
}

if (!clientToken) {
  document.body.innerHTML = "<div style='display:flex;align-items:center;justify-content:center;height:100vh;color:#f87171;font-family:Inter,sans-serif'>Token manquant dans l URL</div>";
}
if (token && clientToken) doVerify();

// ── Auth ──────────────────────────────────────────────────────────────────────
document.getElementById("eyeBtn").onclick = function() {
  var i = document.getElementById("pwd");
  i.type = i.type === "password" ? "text" : "password";
};
document.getElementById("loginBtn").onclick = doLogin;
document.getElementById("pwd").onkeydown = function(e) { if (e.key==="Enter") doLogin(); };

function doVerify() {
  fetch("/admin/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({password:token,client_token:clientToken})})
  .then(function(r){ if(r.ok) r.json().then(function(d){ showDash(d.business_name); }); else { token=""; localStorage.removeItem("wt"); } });
}

function doLogin() {
  var pwd = document.getElementById("pwd").value;
  var err = document.getElementById("errMsg");
  err.style.display = "none";
  fetch("/admin/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({password:pwd,client_token:clientToken})})
  .then(function(r){
    if(r.ok) r.json().then(function(d){ token=pwd; localStorage.setItem("wt",pwd); showDash(d.business_name); });
    else err.style.display = "block";
  }).catch(function(){ err.style.display="block"; err.innerText="Erreur reseau"; });
}

function showDash(name) {
  document.getElementById("login").style.display = "none";
  document.getElementById("dashboard").style.display = "block";
  // Noms
  if(name) {
    document.getElementById("businessName").innerText = name;
    document.getElementById("topbarName").innerText = name;
    document.getElementById("drawerName").innerText = name;
  }
  loadConvs();
}

function doLogout() {
  localStorage.removeItem("wt"); token = "";
  document.getElementById("dashboard").style.display = "none";
  document.getElementById("login").style.display = "flex";
  document.getElementById("pwd").value = "";
}

document.getElementById("logoutBtn").onclick = doLogout;
document.getElementById("logoutBtnMobile").onclick = doLogout;

// ── Menu mobile ───────────────────────────────────────────────────────────────
document.getElementById("menuBtn").onclick = function() {
  document.getElementById("drawer").classList.add("open");
  document.getElementById("drawerOverlay").style.display = "block";
};
document.getElementById("closeDrawer").onclick = closeDrawer;
document.getElementById("drawerOverlay").onclick = closeDrawer;
function closeDrawer() {
  document.getElementById("drawer").classList.remove("open");
  document.getElementById("drawerOverlay").style.display = "none";
}

// ── Refresh ───────────────────────────────────────────────────────────────────
document.getElementById("refreshBtn").onclick = loadConvs;
document.getElementById("refreshBtnMobile").onclick = loadConvs;

// ── Recherche ─────────────────────────────────────────────────────────────────
document.getElementById("searchInput").oninput = function() { renderConvList(filterConvs(this.value)); };
document.getElementById("searchMobile").oninput = function() { renderConvList(filterConvs(this.value)); };

// ── Back mobile ───────────────────────────────────────────────────────────────
document.getElementById("backBtn").onclick = function() {
  document.getElementById("mobileConvView").classList.remove("visible");
  document.getElementById("mobileConvSection").style.display = "block";
  document.getElementById("statsBarMobile").style.display = "flex";
};

// ── Chargement conversations ──────────────────────────────────────────────────
function loadConvs() {
  fetch("/admin/conversations?client_token="+clientToken, {headers:{"X-Admin-Password":token}})
  .then(function(r){ return r.json(); })
  .then(function(data){ allConvs = data; renderConvList(data); });
}

function filterConvs(q) {
  if(!q) return allConvs;
  q = q.toLowerCase();
  return allConvs.filter(function(c){ return c.id.toLowerCase().includes(q); });
}

// ── Stats ─────────────────────────────────────────────────────────────────────
function computeStats(data) {
  var total = data.length;
  var leads = data.filter(function(c){ return c.needs_human; }).length;
  var urgent = leads; // needs_human = a rappeler
  var rate = total > 0 ? Math.round((leads / total) * 100) : 0;

  // Ce mois : created_at commence par YYYY-MM courant
  var now = new Date();
  var ym = now.getFullYear() + "-" + String(now.getMonth()+1).padStart(2,"0");
  var month = data.filter(function(c){ return c.created_at && c.created_at.startsWith(ym); }).length;

  return { total: total, leads: leads, urgent: urgent, rate: rate, month: month };
}

function updateStats(data) {
  var s = computeStats(data);
  // Desktop
  document.getElementById("totalN").innerText = s.total;
  document.getElementById("leadsN").innerText = s.leads;
  document.getElementById("urgentN").innerText = s.urgent;
  document.getElementById("rateN").innerText = s.rate + "%";
  document.getElementById("monthN").innerText = s.month;
  // Mobile
  document.getElementById("mTotal").innerText = s.total;
  document.getElementById("mLeads").innerText = s.leads;
  document.getElementById("mRate").innerText = s.rate + "%";
  document.getElementById("mMonth").innerText = s.month;
}

// ── Rendu liste ───────────────────────────────────────────────────────────────
function renderConvList(data) {
  updateStats(allConvs); // stats toujours sur toutes les convs

  // Desktop
  var list = document.getElementById("convList");
  list.innerHTML = "";

  // Mobile
  var mlist = document.getElementById("mobileConvList");
  mlist.innerHTML = "";

  if(!data.length) {
    var empty = "<p style='color:#475569;font-size:13px;text-align:center;padding:20px'>Aucune conversation</p>";
    list.innerHTML = empty;
    mlist.innerHTML = empty;
    return;
  }

  data.forEach(function(conv) {
    var contact = conv.contact_info ? "<div class='contact-info'>&#128222; "+esc(conv.contact_info)+"</div>" : "";
    var inner = "<div class='ci-top'><span class='ci-id'>#"+esc(conv.id.slice(0,8))+"</span>"
      +(conv.needs_human?"<span class='badge'>RAPPELER</span>":"")+"</div>"
      +"<div class='ci-meta'>"+esc(conv.created_at)+" &middot; "+esc(conv.message_count)+" msg</div>"+contact;

    // Desktop
    var div = document.createElement("div");
    div.className = "ci"+(conv.needs_human?" urgent":"")+(conv.id===activeId?" active":"");
    div.innerHTML = inner;
    div.onclick = (function(id, el){ return function(){ loadConv(id, el, false); }; })(conv.id, div);
    list.appendChild(div);

    // Mobile
    var mdiv = document.createElement("div");
    mdiv.className = "ci"+(conv.needs_human?" urgent":"");
    mdiv.innerHTML = inner;
    mdiv.onclick = (function(id){ return function(){ loadConv(id, null, true); }; })(conv.id);
    mlist.appendChild(mdiv);
  });
}

// ── Chargement conversation ───────────────────────────────────────────────────
function loadConv(id, el, mobile) {
  activeId = id;
  if(!mobile) {
    document.querySelectorAll("#convList .ci").forEach(function(x){ x.classList.remove("active"); });
    if(el) el.classList.add("active");
    document.getElementById("hdrTitle").innerText = "Conversation #"+id.slice(0,8);
    document.getElementById("hdrSub").innerText = "Historique complet";
  } else {
    document.getElementById("mobileConvSection").style.display = "none";
    document.getElementById("statsBarMobile").style.display = "none";
    var view = document.getElementById("mobileConvView");
    view.classList.add("visible");
    document.getElementById("mobileHdrTitle").innerText = "Conversation #"+id.slice(0,8);
    document.getElementById("mobileHdrSub").innerText = "Historique complet";
  }

  fetch("/admin/conversations/"+id+"?client_token="+clientToken, {headers:{"X-Admin-Password":token}})
  .then(function(r){ return r.json(); })
  .then(function(data){
    if(!mobile) {
      var area = document.getElementById("msgsArea");
      area.innerHTML = "<div class='msgs-wrap' id='msgsWrap'></div>";
      var wrap = document.getElementById("msgsWrap");
      data.forEach(function(msg){ wrap.appendChild(buildMsg(msg)); });
      area.scrollTop = area.scrollHeight;
    } else {
      var mmsgs = document.getElementById("mobileMsgs");
      mmsgs.innerHTML = "";
      data.forEach(function(msg){ mmsgs.appendChild(buildMsg(msg)); });
      mmsgs.scrollTop = mmsgs.scrollHeight;
    }
  });
}

function buildMsg(msg) {
  var div = document.createElement("div");
  div.className = "msg " + msg.role;
  var who = msg.role === "user" ? "Visiteur" : "Assistant IA";
  div.innerHTML = "<div class='msg-who'>"+who+"</div><div class='msg-text'>"+esc(msg.content).split("\\n").join("<br>")+"</div>";
  return div;
}
</script>
</body>
</html>"""


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    return HTMLResponse(content=ADMIN_HTML)


@app.post("/admin/login")
def admin_login(data: dict, db: Session = Depends(get_db)):
    c = db.query(Client).filter(Client.token == data.get("client_token","")).first()
    if not c or c.admin_password != data.get("password",""):
        raise HTTPException(status_code=401)
    return {"ok": True, "business_name": c.business_name}


@app.get("/admin/conversations")
def admin_conversations(client_token: str, request: Request, db: Session = Depends(get_db)):
    password = request.headers.get("X-Admin-Password","")
    c = db.query(Client).filter(Client.token == client_token).first()
    if not c or c.admin_password != password:
        raise HTTPException(status_code=401)
    convs = db.query(Conversation).filter(
        Conversation.client_token == client_token
    ).order_by(Conversation.created_at.desc()).all()
    result = []
    for conv in convs:
        msgs = db.query(MessageModel).filter(MessageModel.conversation_id == conv.id).order_by(MessageModel.created_at).all()
        state = get_state(conv.id, db)
        needs_human = state == STATE_DONE
        contact_info = None
        for m in msgs:
            if m.role == "user":
                digits = re.sub(r'\D', '', m.content)
                if len(digits) >= 6:
                    contact_info = m.content
        result.append({
            "id": conv.id,
            "created_at": str(conv.created_at)[:16] if conv.created_at else "--",
            "message_count": len(msgs),
            "needs_human": needs_human,
            "contact_info": contact_info if needs_human else None,
            "state": state
        })
    return result


@app.get("/admin/conversations/{conv_id}")
def admin_conversation_detail(conv_id: str, client_token: str, request: Request, db: Session = Depends(get_db)):
    password = request.headers.get("X-Admin-Password","")
    c = db.query(Client).filter(Client.token == client_token).first()
    if not c or c.admin_password != password:
        raise HTTPException(status_code=401)
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id, Conversation.client_token == client_token
    ).first()
    if not conv:
        raise HTTPException(status_code=404)
    msgs = db.query(MessageModel).filter(
        MessageModel.conversation_id == conv_id
    ).order_by(MessageModel.created_at).all()
    return [{"role": m.role, "content": m.content} for m in msgs]


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
    reply = translate_to_visitor_language(MSG_ASKING, visitor_msgs) if visitor_msgs else MSG_ASKING
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

    if state == STATE_ASKING:
        if contains_contact_info(msg.message):
            if c:
                send_human_email(conv_id, msg.message, c)
            set_state(conv_id, STATE_DONE, db)
            reply = translate_to_visitor_language(MSG_CONFIRMED, visitor_msgs)
            save_message(conv_id, "assistant", reply, db)
            return bot_reply(reply, conv_id, True)
        else:
            reply = translate_to_visitor_language(MSG_ASKING, visitor_msgs)
            save_message(conv_id, "assistant", reply, db)
            return bot_reply(reply, conv_id, False)

    if state == STATE_PROPOSED:
        if classify_yes_no(msg.message):
            set_state(conv_id, STATE_ASKING, db)
            reply = translate_to_visitor_language(MSG_ASKING, visitor_msgs)
            save_message(conv_id, "assistant", reply, db)
            return bot_reply(reply, conv_id, False)
        else:
            set_state(conv_id, STATE_NORMAL, db)
            reply = translate_to_visitor_language(MSG_DECLINED, visitor_msgs)
            save_message(conv_id, "assistant", reply, db)
            return bot_reply(reply, conv_id, False)

    if HUMAN_REGEX.search(msg.message):
        set_state(conv_id, STATE_PROPOSED, db)
        reply = translate_to_visitor_language(MSG_PROPOSAL, visitor_msgs)
        save_message(conv_id, "assistant", reply, db)
        return bot_reply(reply, conv_id, False)

    history = db.query(MessageModel).filter(
        MessageModel.conversation_id == conv_id
    ).order_by(MessageModel.created_at).all()

    if c and c.system_prompt:
        base_prompt = c.system_prompt
    else:
        base_prompt = "Tu es un assistant virtuel professionnel."

    if c:
        catalog = get_catalog_text(get_shop_url(c.token, db))
        if catalog:
            base_prompt += (
                "\n\nCATALOGUE EN TEMPS REEL (source de verite pour les produits, prix et stocks : "
                "si une autre information du prompt contredit ce catalogue, c'est le catalogue qui a raison. "
                "Ne propose jamais un produit ou une taille absent ou epuise) :\n" + catalog
            )

    if msg.page_content:
        base_prompt += "\n\nCONTENU SUPPLEMENTAIRE DU SITE :\n" + msg.page_content

    base_prompt += (
        "\n\nREGLES :\n"
        "- Reponds TOUJOURS dans la meme langue que le dernier message du visiteur\n"
        "- Reponds uniquement aux questions liees a l activite du business\n"
        "- Sois concis, professionnel et serviable\n"
        "- Si tu ne connais pas la reponse, dis-le simplement"
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
    return bot_reply(reply, conv_id, False)


app.mount("/static", StaticFiles(directory="static"), name="static")