#!/usr/bin/env python3
"""
Second batch of new terms.
- Retries the 18 seeds that Claude rejected as "out of asylum scope"
  (mostly single-word body parts) by passing an explicit category hint.
- Adds another ~250 targeted terms in medical / legal / procedure.
"""
import json, sys, time, re, unicodedata
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

WORKER = "https://cool-moon-d7ebitalk-translate.metlamari.workers.dev/"
TERMS = "C:/Users/italk/italk/data/terms.json"

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

# Each entry: (greek_term, category, context_hint_or_None)
# The context hint (in Greek) gets appended in parentheses so Claude
# doesn't reject the term as out-of-scope.
SEED = [
    # ---- RETRIES from batch 1 ----
    ("κεφάλι",      "medical", "μέρος του σώματος στην ιατρική εξέταση"),
    ("μάτι",        "medical", "μέρος του σώματος, οφθαλμός"),
    ("μύτη",        "medical", "μέρος του σώματος, ρίνα"),
    ("δόντι",       "medical", "στοματική υγεία"),
    ("βραχίονας",   "medical", "άνω άκρο"),
    ("αγκώνας",     "medical", "άρθρωση άνω άκρου"),
    ("καρπός",      "medical", "άρθρωση χεριού"),
    ("καρδιά",      "medical", "καρδιαγγειακό όργανο"),
    ("φτέρνισμα",   "medical", "αναπνευστικό σύμπτωμα"),
    ("ερυθρά",      "medical", "παιδική εξανθηματική νόσος"),
    ("παυσίπονο",   "medical", "φαρμακευτική κατηγορία, αναλγητικό"),
    ("νάρθηκας",    "medical", "ιατρικό υλικό, ακινητοποίηση κατάγματος"),
    ("γάζα",        "medical", "ιατρικό υλικό, επίδεσμος"),
    ("γενικευμένη αγχώδης διαταραχή", "medical", "ψυχιατρική διάγνωση GAD"),
    ("εφιάλτες",    "medical", "διαταραχή ύπνου, σύμπτωμα PTSD"),
    ("εκκαθαριστικό εφορίας", "documentation", "φορολογικό έγγραφο για ΑΦΜ"),
    ("νονός",       "family",  "θρησκευτικός/νομικός ρόλος στην ελληνική οικογένεια"),
    ("νονά",        "family",  "θρησκευτικός/νομικός ρόλος στην ελληνική οικογένεια"),

    # ---- BATCH 2: MEDICAL ANATOMY (deeper) ----
    ("αρτηρία", "medical", "αγγείο"),
    ("φλέβα", "medical", "αγγείο"),
    ("θυρεοειδής αδένας", "medical", "ενδοκρινικό όργανο"),
    ("επινεφρίδια", "medical", "ενδοκρινικά όργανα πάνω από τους νεφρούς"),
    ("υπόφυση", "medical", "εγκεφαλικός αδένας"),
    ("λεμφαδένες", "medical", "λεμφικό σύστημα"),
    ("σπλήνας", "medical", "όργανο κοιλιάς"),
    ("σκωληκοειδής απόφυση", "medical", "μέρος πεπτικού συστήματος"),
    ("μήτρα", "medical", "γυναικείο αναπαραγωγικό όργανο"),
    ("ωοθήκες", "medical", "γυναικείο αναπαραγωγικό όργανο"),
    ("μαστός", "medical", "γυναικείο ανατομικό μέλος"),
    ("προστάτης", "medical", "ανδρικό αναπαραγωγικό όργανο"),
    ("γόνατο", "medical", "άρθρωση κάτω άκρου"),
    ("αστράγαλος", "medical", "άρθρωση ποδιού"),
    ("μηρός", "medical", "τμήμα κάτω άκρου"),
    ("πλευρά", "medical", "θωρακικό οστό"),
    ("σπονδυλική στήλη", "medical", "ανατομικός άξονας"),
    ("κρανίο", "medical", "οστό κεφαλής"),
    ("νεφρικοί λίθοι", "medical", "νεφρική πάθηση"),
    ("χοληδόχος κύστη", "medical", "όργανο πέψης"),

    # ---- BATCH 2: MEDICAL DISEASES (more) ----
    ("υποθυρεοειδισμός", "medical", "ενδοκρινική πάθηση"),
    ("υπερθυρεοειδισμός", "medical", "ενδοκρινική πάθηση"),
    ("αναιμία σιδηροπενική", "medical", "αιματολογική πάθηση"),
    ("δρεπανοκυτταρική αναιμία", "medical", "γενετική αιματολογική πάθηση"),
    ("μεσογειακή αναιμία", "medical", "θαλασσαιμία"),
    ("γαστρίτιδα", "medical", "πάθηση στομάχου"),
    ("γαστρικό έλκος", "medical", "πεπτική πάθηση"),
    ("κολίτιδα", "medical", "εντερική φλεγμονή"),
    ("νόσος Crohn", "medical", "ιδιοπαθής φλεγμονώδης εντεροπάθεια"),
    ("κίρρωση ήπατος", "medical", "ηπατική πάθηση"),
    ("δερματίτιδα", "medical", "δερματική πάθηση"),
    ("έκζεμα", "medical", "δερματική πάθηση"),
    ("ψωρίαση", "medical", "χρόνια δερματική πάθηση"),
    ("επιληψία", "medical", "νευρολογική πάθηση"),
    ("νόσος Πάρκινσον", "medical", "νευροεκφυλιστική νόσος"),
    ("άνοια Αλτσχάιμερ", "medical", "νευροεκφυλιστική νόσος"),
    ("σκλήρυνση κατά πλάκας", "medical", "νευρολογική πάθηση"),
    ("μολυσματική μονοπυρήνωση", "medical", "λοίμωξη"),
    ("κοκκύτης", "medical", "παιδική λοίμωξη αναπνευστικού"),
    ("μηνιγγίτιδα", "medical", "λοίμωξη κεντρικού νευρικού"),
    ("Ebola", "medical", "ιογενής αιμορραγικός πυρετός"),
    ("COVID-19", "medical", "ιογενής λοίμωξη"),
    ("μπρουκέλλωση", "medical", "ζωονόσος"),
    ("λέπρα", "medical", "μυκοβακτηριακή νόσος"),
    ("άνοια", "medical", "γνωσιακή διαταραχή"),

    # ---- BATCH 2: DENTAL & OPHTHALMOLOGY ----
    ("τερηδόνα", "medical", "οδοντική νόσος"),
    ("οδοντικό απόστημα", "medical", "οδοντιατρικό επείγον"),
    ("γναθοπροσωπικός χειρουργός", "medical", "ιατρική ειδικότητα"),
    ("οδοντοστοιχία", "medical", "οδοντιατρικό βοήθημα"),
    ("μυωπία", "medical", "διαθλαστικό σφάλμα"),
    ("υπερμετρωπία", "medical", "διαθλαστικό σφάλμα"),
    ("γλαύκωμα", "medical", "οφθαλμολογική πάθηση"),
    ("καταρράκτης", "medical", "οφθαλμολογική πάθηση"),
    ("επιπεφυκίτιδα", "medical", "οφθαλμική λοίμωξη"),

    # ---- BATCH 2: MENTAL HEALTH extras ----
    ("διαχωριστική διαταραχή ταυτότητας", "medical", "ψυχιατρική διάγνωση"),
    ("διαταραχή προσωπικότητας οριακού τύπου", "medical", "ψυχιατρική διάγνωση"),
    ("νευρική ανορεξία", "medical", "διατροφική διαταραχή"),
    ("βουλιμία", "medical", "διατροφική διαταραχή"),
    ("κρίση άγχους", "medical", "ψυχιατρικό σύμπτωμα"),
    ("υπερεγρήγορση", "medical", "σύμπτωμα PTSD, hypervigilance"),
    ("επανάληψη τραυματικού βιώματος", "medical", "flashback, PTSD"),
    ("αποσύνδεση", "medical", "ψυχιατρικό σύμπτωμα, dissociation"),
    ("συναισθηματική αναισθησία", "medical", "emotional numbing, PTSD"),
    ("αϋπνία μετά από τραύμα", "medical", "διαταραχή ύπνου συνοδεύουσα PTSD"),

    # ---- BATCH 2: LEGAL COURT process (more) ----
    ("διοικητικό δικαστήριο", "legal", "κατηγορία δικαστηρίου"),
    ("διοικητικό εφετείο", "legal", "κατηγορία δικαστηρίου"),
    ("Πολυμελές Πρωτοδικείο", "legal", "σύνθεση δικαστηρίου"),
    ("Μονομελές Πρωτοδικείο", "legal", "σύνθεση δικαστηρίου"),
    ("τακτική διαδικασία", "legal", "είδος αστικής δίκης"),
    ("διαδικασία εκουσίας δικαιοδοσίας", "legal", "τύπος δίκης"),
    ("ασφαλιστικά μέτρα ενώπιον δικαστή", "legal", "επείγουσα δικαστική προστασία"),
    ("κατάθεση ενόρκως", "legal", "διαδικαστική πράξη"),
    ("ανακριτής", "legal", "δικαστικός λειτουργός"),
    ("ανάκριση", "legal", "στάδιο ποινικής δίκης"),
    ("απολογία", "legal", "διαδικαστική πράξη κατηγορουμένου"),
    ("κλητήριο θέσπισμα", "legal", "έγγραφο κλήσης σε δίκη"),
    ("αναβολή δικασίμου", "legal", "διαδικαστική"),
    ("συνήγορος πολιτικής αγωγής", "legal", "ρόλος"),
    ("δωρεάν δικηγόρος", "legal", "νομική συνδρομή"),
    ("διαμεσολάβηση", "legal", "εναλλακτική επίλυση διαφορών"),
    ("διαιτησία", "legal", "εναλλακτική επίλυση διαφορών"),
    ("δικαστικά έξοδα", "legal", "κόστος δίκης"),
    ("επιδίκαση δικαστικών εξόδων", "legal", "διαδικαστική"),
    ("τελεσίδικη απόφαση", "legal", "καθεστώς δικαστικής απόφασης"),
    ("αμετάκλητη απόφαση", "legal", "καθεστώς δικαστικής απόφασης"),
    ("απόφαση με αναγκαστική εκτέλεση", "legal", "εκτελεστός τίτλος"),
    ("κατάσχεση", "legal", "εκτελεστική πράξη"),
    ("πλειστηριασμός", "legal", "εκτελεστική πράξη"),

    # ---- BATCH 2: LEGAL DOCUMENTS (extra) ----
    ("συμβόλαιο", "documentation", "νομικό έγγραφο"),
    ("συμφωνητικό εργασίας", "documentation", "συμβατικό έγγραφο"),
    ("μισθωτήριο συμβόλαιο", "documentation", "συμβατικό έγγραφο ενοικίασης"),
    ("διαθήκη", "documentation", "κληρονομικό έγγραφο"),
    ("κληρονομητήριο", "documentation", "δικαστικό έγγραφο κληρονομικής διαδοχής"),
    ("νομικό γνωμοδοτικό σημείωμα", "documentation", "έγγραφο δικηγόρου"),
    ("υπόμνημα", "documentation", "νομικό υπόμνημα προς δικαστήριο"),
    ("γνήσιο υπογραφής", "documentation", "διαδικασία επικύρωσης"),

    # ---- BATCH 2: PROCEDURE (more asylum-specific) ----
    ("δεύτερη προσωπική συνέντευξη", "procedure", "στάδιο διαδικασίας"),
    ("συμπληρωματική συνέντευξη", "procedure", "στάδιο διαδικασίας"),
    ("προφορική ακρόαση σε β' βαθμό", "procedure", "στάδιο προσφυγής"),
    ("έγγραφη προσφυγή", "procedure", "τύπος προσφυγής"),
    ("νέα αίτηση", "procedure", "μεταγενέστερη αίτηση διεθνούς προστασίας"),
    ("ρήτρα κυριαρχίας Δουβλίνο", "procedure", "άρθρο 17 Δουβλίνο"),
    ("ανθρωπιστική ρήτρα Δουβλίνο", "procedure", "άρθρο 17 παρ. 2"),
    ("έλεγχος στοιχείων EURODAC", "procedure", "διαδικαστικό βήμα"),
    ("αίτημα εκ νέου εξέτασης", "procedure", "διαδικαστική πράξη"),
    ("αποχώρηση από τη δομή χωρίς άδεια", "procedure", "διοικητικό συμβάν"),
    ("λήξη προθεσμίας κατάθεσης προσφυγής", "procedure", "διαδικαστική"),
    ("επίδοση απόφασης με ταχυδρομείο", "procedure", "διαδικαστική"),
    ("επίδοση απόφασης με ηλεκτρονικά μέσα", "procedure", "διαδικαστική"),
    ("θυροκόλληση απόφασης στη δομή", "procedure", "διαδικαστική"),
    ("θεώρηση αντιγράφου", "procedure", "διοικητική πράξη επικύρωσης"),

    # ---- BATCH 2: VULNERABILITY (more IPSN indicators) ----
    ("LGBTI αιτών", "vulnerable", "ιδιότητα, IPSN"),
    ("θύμα σοβαρών μορφών βίας", "vulnerable", "IPSN κατηγορία"),
    ("μονογονεϊκή οικογένεια με ανήλικα", "vulnerable", "IPSN κατηγορία"),
    ("θύμα βασανιστηρίων", "vulnerable", "IPSN κατηγορία"),
    ("θύμα σεξουαλικής βίας", "vulnerable", "IPSN κατηγορία"),
    ("θύμα ακρωτηριασμού γυναικείων γεννητικών οργάνων", "vulnerable", "IPSN"),
    ("θύμα εξαναγκαστικού γάμου", "vulnerable", "IPSN κατηγορία"),
    ("θύμα παιδικού γάμου", "vulnerable", "IPSN"),
    ("άτομο με σοβαρή μεταδοτική νόσο", "vulnerable", "IPSN κατηγορία"),
    ("άτομο με νοητική αναπηρία", "vulnerable", "IPSN"),
    ("άτομο με ψυχιατρική διαταραχή", "vulnerable", "IPSN"),
    ("αναλφάβητος αιτών", "vulnerable", "IPSN, ειδικές διαδικαστικές ανάγκες"),
    ("ηλικιωμένος χωρίς οικογένεια", "vulnerable", "IPSN"),

    # ---- BATCH 2: DETENTION extras ----
    ("έλεγχος νομιμότητας κράτησης", "detention", "δικαστικός έλεγχος"),
    ("προσφυγή κατά κράτησης στα διοικητικά δικαστήρια", "detention", "ένδικο μέσο"),
    ("δικαίωμα επικοινωνίας με δικηγόρο εντός κράτησης", "detention", "διαδικαστικό δικαίωμα"),
    ("δικαίωμα ιατρικής εξέτασης εντός κράτησης", "detention", "δικαίωμα"),
    ("απομόνωση εντός κράτησης", "detention", "συνθήκες"),
    ("συνθήκες κράτησης", "detention", "μεταχείριση"),
    ("κακομεταχείριση εντός κράτησης", "detention", "παραβίαση δικαιωμάτων"),
    ("αναφορά κακομεταχείρισης στον Συνήγορο του Πολίτη", "detention", "μηχανισμός καταγγελίας"),
    ("Εθνικός Μηχανισμός Πρόληψης Βασανιστηρίων", "detention", "θεσμικός φορέας"),

    # ---- BATCH 2: STATUS extras ----
    ("αναγνωρισμένος πρόσφυγας", "status", "κατηγορία δικαιούχου"),
    ("δικαιούχος επικουρικής προστασίας", "status", "κατηγορία δικαιούχου"),
    ("αιτών επικουρικής προστασίας", "status", "κατηγορία"),
    ("αιτών χωρίς οικογένεια", "status", "κατηγορία"),
    ("αιτών με οικογένεια", "status", "κατηγορία"),
    ("απορριφθείς αιτών", "status", "καθεστώς"),
    ("αιτών σε β' βαθμό", "status", "στάδιο διαδικασίας"),
    ("τελεσίδικα απορριφθείς", "status", "καθεστώς"),
    ("επιστρέφων εθελοντικά", "status", "καθεστώς AVR"),

    # ---- BATCH 2: INTEGRATION extras ----
    ("μάθημα γλώσσας επιπέδου Α1", "integration", "CEFR"),
    ("μάθημα γλώσσας επιπέδου Α2", "integration", "CEFR"),
    ("μάθημα γλώσσας επιπέδου Β1", "integration", "CEFR"),
    ("πιστοποιητικό ελληνομάθειας επιπέδου Β1", "integration", "απαραίτητο για πολιτογράφηση"),
    ("εξετάσεις πολιτογράφησης", "integration", "διαδικασία απόκτησης ιθαγένειας"),
    ("μονιμοποίηση διαμονής", "integration", "μακροχρόνια άδεια"),
    ("κάρτα ανεργίας ΔΥΠΑ", "integration", "εργασιακά"),
    ("απόκτηση ΑΦΜ", "integration", "διαδικαστικό βήμα"),
    ("απόκτηση ΑΜΚΑ", "integration", "διαδικαστικό βήμα υγειονομικής κάλυψης"),
    ("άνοιγμα τραπεζικού λογαριασμού", "integration", "διαδικαστικό βήμα"),
    ("υπογραφή σύμβασης εργασίας", "integration", "εργασιακό βήμα"),

    # ---- BATCH 2: COMMUNICATION / interpretation extras ----
    ("τηλεδιερμηνεία", "communication", "εξ αποστάσεως διερμηνεία"),
    ("διερμηνεία μέσω τηλεφώνου", "communication", "μέθοδος"),
    ("διερμηνεία μέσω βιντεοκλήσης", "communication", "μέθοδος"),
    ("ορκωτός μεταφραστής", "communication", "νομικός ρόλος"),
    ("μεταφραστική υπηρεσία ΥΠΕΞ", "communication", "επίσημη υπηρεσία"),
    ("δεοντολογικός κώδικας διερμηνέα", "communication", "επαγγελματικοί κανόνες"),
    ("κατάρτιση διερμηνέα", "communication", "εκπαίδευση"),
    ("διερμηνεία σε νοηματική γλώσσα", "communication", "εξειδικευμένη διερμηνεία"),
    ("διερμηνεία για ΚωΦούς-Τυφλούς", "communication", "εξειδικευμένη διερμηνεία"),
]

def slugify(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:60]

def translate(term_with_context):
    body = json.dumps({"term": term_with_context, "sourceLang": "el"}).encode("utf-8")
    req = urllib.request.Request(WORKER, data=body, method="POST", headers={
        "Content-Type": "application/json",
        "Origin": "https://i-talk.gr",
        "User-Agent": UA
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def main():
    with open(TERMS, "r", encoding="utf-8") as f:
        data = json.load(f)

    existing_ids = {t["id"] for t in data["terms"]}
    existing_el = {t["translations"].get("el", "").strip().lower() for t in data["terms"]}
    added = 0
    skipped = 0
    failed = []

    total = len(SEED)
    for i, (greek, cat, hint) in enumerate(SEED, 1):
        if greek.strip().lower() in existing_el:
            skipped += 1
            continue
        # Compose term with hint to keep Claude in scope
        payload = greek if not hint else f"{greek} ({hint})"
        print(f"  [{i}/{total}] [{cat}] {greek} …")
        try:
            resp = translate(payload)
        except Exception as e:
            print(f"    ERR: {e}")
            failed.append(greek)
            time.sleep(1.0)
            continue

        if not resp.get("translations"):
            print(f"    no translations: {resp.get('note') or resp.get('error')}")
            failed.append(greek)
            continue

        # For EL translation, prefer the plain Greek we sent (not "term (hint)")
        translations = {}
        for lang in ["el", "en", "ar", "fa", "fr"]:
            v = (resp["translations"].get(lang) or "").strip()
            if lang == "el":
                v = greek  # keep original clean Greek
            translations[lang] = v

        en = translations.get("en", "")
        base = slugify(en) or slugify(greek) or f"{cat}-{i}"
        slug = base
        n = 2
        while slug in existing_ids:
            slug = f"{base}-{n}"
            n += 1

        data["terms"].append({
            "id": slug,
            "category": cat,
            "translations": translations,
            "definition_el": (resp.get("definition_el") or "").strip(),
            "definition_en": (resp.get("definition_en") or "").strip(),
            "sources": [f"AI-generated ({resp.get('model')}) 2026-09-06 — needs native review"]
        })
        existing_ids.add(slug)
        existing_el.add(greek.strip().lower())
        added += 1
        time.sleep(0.3)

    data["meta"]["version"] = "0.5.0"
    data["meta"]["updated"] = "2026-09-06"

    with open(TERMS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print()
    print(f"added:   {added}")
    print(f"skipped: {skipped}")
    print(f"failed:  {len(failed)}")
    print(f"total terms now: {len(data['terms'])}")
    if failed:
        for g in failed[:20]:
            print(f"  - {g}")

if __name__ == "__main__":
    main()
