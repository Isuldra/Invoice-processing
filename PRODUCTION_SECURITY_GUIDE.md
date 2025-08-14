# 🔒 OneMed Fakturabehandling - Produksjonssikkerhet

## 🚨 KRITISKE SIKKERHETSTILTAK

### Fase 1: Applikasjonssikkerhet (Høy prioritet)

```python
# Legg til i app.py - Sikkerhetstiltak
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from werkzeug.middleware.proxy_fix import ProxyFix
import secrets
import logging
import os

# Sikre Flask-konfiguration
app.config.update(
    SECRET_KEY=os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32)),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=15),
    MAX_CONTENT_LENGTH=50 * 1024 * 1024,  # 50MB max
    WTF_CSRF_TIME_LIMIT=None
)

# CSRF-beskyttelse
csrf = CSRFProtect(app)

# Rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379"
)

# Sikker filhåndtering
ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}
UPLOAD_FOLDER = '/secure/uploads'  # Isolert fra web root

def secure_filename_check(filename):
    """Avansert filnavn-validering"""
    if not filename or '..' in filename:
        raise ValueError("Ugyldig filnavn")
    
    # Sjekk file magic numbers
    if not is_valid_file_type(filename):
        raise ValueError("Ugyldig filtype")
    
    return secure_filename(filename)

# Logging for sikkerhetshendelser
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[
        logging.FileHandler('/var/log/onemed/security.log'),
        logging.StreamHandler()
    ]
)
```

### Fase 2: Infrastruktursikkerhet

#### Docker Produksjonskonfigurasjon

```dockerfile
# Dockerfile.prod
FROM python:3.11-slim-bullseye

# Sikkerhetstiltak
RUN groupadd -r onemed && useradd --no-log-init -r -g onemed onemed
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    libyaml-dev \
    && rm -rf /var/lib/apt/lists/*

# Ikke kjør som root
USER onemed
WORKDIR /app

# Kopier requirements først for bedre caching
COPY --chown=onemed:onemed requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopier applikasjon
COPY --chown=onemed:onemed . .

# Helse-sjekk
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", \
     "--timeout", "120", "--keep-alive", "2", \
     "--max-requests", "1000", "--preload", "app:app"]
```

#### Docker Compose med Sikkerhet

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  onemed-faktura:
    build:
      context: .
      dockerfile: Dockerfile.prod
    restart: unless-stopped
    environment:
      - FLASK_ENV=production
      - FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
      - DATABASE_URL=${DATABASE_URL}
    volumes:
      - ./secure_uploads:/app/secure_uploads:rw
      - ./logs:/var/log/onemed:rw
    networks:
      - onemed_internal
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.onemed.tls=true"
      - "traefik.http.routers.onemed.tls.certresolver=letsencrypt"

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - onemed_internal

  traefik:
    image: traefik:v2.9
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik:/etc/traefik:ro
      - traefik_certs:/certs
    networks:
      - onemed_internal

volumes:
  redis_data:
  traefik_certs:

networks:
  onemed_internal:
    driver: bridge
    internal: false
```

### Fase 3: GDPR Compliance

#### Data Processing Record (GDPR Article 30)

```yaml
# gdpr_records.yml
data_processing_activities:
  - activity_name: "Telia Invoice Processing"
    legal_basis: "Article 6(1)(c) - Legal obligation"
    data_categories:
      - "Employee names"
      - "Phone numbers"
      - "Cost center assignments"
      - "Invoice amounts and dates"
    data_subjects: "OneMed employees"
    retention_period: "7 years (accounting law)"
    data_sources: "Telia Norge AS invoices"
    recipients: "OneMed accounting department"
    third_country_transfers: "None"
    security_measures:
      - "Encryption at rest (AES-256)"
      - "Encryption in transit (TLS 1.3)"
      - "Access controls and authentication"
      - "Audit logging"
      - "Regular security assessments"
```

#### Personvernerklæring (Privacy Policy)

```markdown
# PERSONVERNERKLÆRING - OneMed Fakturabehandling

## Behandlingsformål
OneMed behandler personopplysninger fra Telia-fakturaer for å:
- Korrekt fordeling av telekomkostnader til kostsentre
- Oppfyllelse av regnskapslovens krav til dokumentasjon
- Intern kostnadskontroll og budsjettering

## Rettslig grunnlag
- Artikkel 6(1)(c) GDPR - Rettslig forpliktelse (regnskapsloven)
- Artikkel 6(1)(b) GDPR - Kontraktsoppfyllelse (arbeidsavtaler)

## Oppbevaringstid  
Personopplysninger oppbevares i maksimalt 7 år etter regnskapslovens krav.

## Dine rettigheter
- Rett til innsyn i behandling av dine personopplysninger
- Rett til retting av feilaktige opplysninger
- Rett til sletting når lovpålagt oppbevaring er utløpt
- Rett til begrensning av behandling
- Rett til dataportabilitet

## Kontakt
Personvernombud: privacy@onemed.no
```

### Fase 4: Overvåking og Incident Response

#### Sikkerhetshendelse-prosedyre

```python
# security_monitoring.py
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

class SecurityMonitor:
    def __init__(self):
        self.logger = logging.getLogger('security')
        
    def log_security_event(self, event_type, severity, details):
        """Log sikkerhetshendelser"""
        timestamp = datetime.now().isoformat()
        
        log_entry = {
            'timestamp': timestamp,
            'event_type': event_type,
            'severity': severity,
            'details': details,
            'source_ip': request.remote_addr if request else 'N/A'
        }
        
        self.logger.warning(f"SECURITY EVENT: {log_entry}")
        
        # Send varsel ved kritiske hendelser
        if severity >= 8:  # CVSS høy/kritisk
            self.send_security_alert(log_entry)
    
    def send_security_alert(self, event):
        """Send sikkerhetsvarsler til ansvarlige"""
        msg = MIMEText(f"""
        SIKKERHETSHENDELSE DETEKTERT
        
        Tidspunkt: {event['timestamp']}
        Alvorlighetsgrad: {event['severity']}/10
        Type: {event['event_type']}
        Detaljer: {event['details']}
        Kilde-IP: {event['source_ip']}
        
        Umiddelbar handling kreves!
        """)
        
        msg['Subject'] = f"SIKKERHETSHENDELSE - OneMed Fakturabehandling"
        msg['From'] = 'security@onemed.no'
        msg['To'] = 'it-sikkerhet@onemed.no'
        
        # Send e-post (konfigurasjon nødvendig)
        # smtp_server.send_message(msg)

# Bruk i Flask-app
security_monitor = SecurityMonitor()

@app.before_request
def security_check():
    """Sikkerhetsjekker før hver forespørsel"""
    
    # Rate limiting check
    if limiter.hit_limit():
        security_monitor.log_security_event(
            'rate_limit_exceeded', 
            6, 
            f"IP {request.remote_addr} exceeded rate limit"
        )
    
    # Mistenkelig filnavn-mønstre
    if request.files:
        for file in request.files.values():
            if file and ('..' in file.filename or 
                        any(char in file.filename for char in ['<', '>', '|', '&'])):
                security_monitor.log_security_event(
                    'malicious_filename_attempt',
                    7,
                    f"Suspicious filename: {file.filename}"
                )
                abort(400)
```

## 🚨 INCIDENT RESPONSE PLAN

### Umiddelbare tiltak ved databrudd:

1. **Første 15 minutter:**
   - Isoler kompromitterte systemer
   - Dokumenter alle observasjoner
   - Varsle IT-sikkerhet og ledelse

2. **Første time:**
   - Vurder omfang av brudd
   - Kontakt juridisk avdeling
   - Forbered kommunikasjon til berørte

3. **Første 24 timer:**
   - Rapporter til Datatilsynet (hvis påkrevet)
   - Implementer midlertidige sikkerhetstiltak
   - Start forensisk undersøkelse

4. **72 timer:**
   - Fullstendig GDPR-bruddrapportering
   - Kommuniker med berørte personer
   - Implementer permanente løsninger

### Kontaktinformasjon ved sikkerhetshendelser:

```
IT-Sikkerhet: +47 XXX XX XXX (24/7)
Datatilsynet: +47 22 39 69 00
Juridisk rådgiver: +47 XXX XX XXX
Ledelse: +47 XXX XX XXX
Kommunikasjonsansvarlig: +47 XXX XX XXX
```

---

**🔒 VIKTIG:** Implementer ALDRI dette systemet i produksjon uten å ha gjennomført alle sikkerhetstiltakene beskrevet ovenfor. Konsekvensene av databrudd kan være katastrofale for OneMed.