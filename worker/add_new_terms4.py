#!/usr/bin/env python3
"""Fourth batch — daily-life reception, integration workflows, documentation depth,
cultural mediation, religion/gender-based asylum specifics."""
import json, sys, time, re, unicodedata
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

WORKER = "https://cool-moon-d7ebitalk-translate.metlamari.workers.dev/"
TERMS = "C:/Users/italk/italk/data/terms.json"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

SEED = [
    # ---- RECEPTION daily life ----
    ("διανομή γεύματος στη δομή", "reception", "καθημερινή λειτουργία"),
    ("κάρτα σίτισης", "reception", "εξατομικευμένη ταυτοποίηση σίτισης"),
    ("πρόγραμμα σίτισης", "reception", "ωρολόγιο"),
    ("αλλαγή διαιτολογίου για θρησκευτικούς λόγους", "reception", "παροχή"),
    ("διανομή προσωπικής υγιεινής", "reception", "παροχή"),
    ("διανομή ρουχισμού εποχής", "reception", "παροχή"),
    ("κάρτα εισόδου-εξόδου δομής", "reception", "έλεγχος"),
    ("ώρα κοιτώνα", "reception", "εσωτερικός κανονισμός"),
    ("απαγόρευση εξόδου τη νύχτα", "reception", "εσωτερικός κανονισμός"),
    ("επίσκεψη εξωτερικού προσώπου", "reception", "εσωτερικός κανονισμός"),
    ("γραμματεία της δομής", "reception", "υπηρεσία"),
    ("κοινωνικός λειτουργός της δομής", "reception", "στέλεχος"),
    ("σύμβουλος στέγασης", "reception", "στέλεχος"),
    ("έφορος της δομής", "reception", "στέλεχος"),
    ("διαχειριστής case management", "reception", "στέλεχος"),
    ("συνάντηση case management", "reception", "διαδικαστικό"),
    ("τοπικός συντονιστής IOM", "reception", "στέλεχος"),
    ("κοινωνικό δίκτυο υποστήριξης", "reception", "παροχή"),
    ("έκθεση συμβάντος βίας στη δομή", "reception", "διαχείριση"),
    ("μεταφορά σε άλλη δομή", "reception", "διοικητική"),

    # ---- INTEGRATION — school & health & work workflows ----
    ("εγγραφή παιδιού σε νηπιαγωγείο", "integration", "παιδική εκπαίδευση"),
    ("εγγραφή παιδιού σε δημοτικό", "integration", "πρωτοβάθμια εκπαίδευση"),
    ("εγγραφή σε γυμνάσιο", "integration", "δευτεροβάθμια"),
    ("τάξη υποδοχής ΖΕΠ", "integration", "εκπαίδευση προσφύγων"),
    ("απολυτήριο δημοτικού", "integration", "πιστοποιητικό εκπαίδευσης"),
    ("απολυτήριο γυμνασίου", "integration", "πιστοποιητικό"),
    ("αναγνώριση σπουδών δευτεροβάθμιας", "integration", "ΔΟΑΤΑΠ ισοδυναμία"),
    ("αναγνώριση σπουδών τριτοβάθμιας", "integration", "ΔΟΑΤΑΠ"),
    ("πρόσβαση σε δημόσιο νοσοκομείο", "integration", "υγειονομική κάλυψη"),
    ("επίσκεψη σε κέντρο υγείας", "integration", "υγειονομική"),
    ("συνταγογράφηση από ιατρό", "integration", "διαδικαστικό υγείας"),
    ("φαρμακείο με ΑΜΚΑ", "integration", "διαδικαστικό υγείας"),
    ("επίδομα παιδιού από ΟΠΕΚΑ", "integration", "κοινωνικό επίδομα"),
    ("επίδομα στέγασης από ΟΠΕΚΑ", "integration", "κοινωνικό επίδομα"),
    ("ελάχιστο εγγυημένο εισόδημα", "integration", "κοινωνικό επίδομα"),
    ("συμβόλαιο ενοικίασης κατοικίας", "integration", "στέγαση"),
    ("κοινόχρηστα σπιτιού", "integration", "λειτουργικό κόστος"),
    ("λογαριασμός ΔΕΗ ρεύματος", "integration", "λειτουργικό"),
    ("λογαριασμός νερού ΕΥΔΑΠ", "integration", "λειτουργικό"),
    ("κάρτα απορίας από τον δήμο", "integration", "κοινωνική παροχή"),
    ("κοινωνικό παντοπωλείο", "integration", "παροχή"),
    ("συσσίτιο ενορίας", "integration", "παροχή"),
    ("κάρτα μετακίνησης ΟΑΣΘ ή ΟΑΣΑ", "integration", "μεταφορές"),
    ("μηνιαία κάρτα μεταφορών", "integration", "μεταφορές"),

    # ---- WORK & TAX ----
    ("υπογραφή σύμβασης εξαρτημένης εργασίας", "integration", "εργασιακό"),
    ("αναγγελία πρόσληψης στη ΔΥΠΑ", "integration", "εργασιακό"),
    ("απόδειξη μισθοδοσίας", "integration", "εργασιακό"),
    ("εκκαθαριστικό μισθοδοσίας", "integration", "εργασιακό"),
    ("εργόσημο", "integration", "εργασιακό ασφαλιστικό μέσο"),
    ("μπλοκάκι παροχής υπηρεσιών", "integration", "ελεύθεροι επαγγελματίες"),
    ("έναρξη επαγγελματικής δραστηριότητας", "integration", "εφορία διαδικασία"),
    ("διακοπή εργασιών", "integration", "εφορία"),
    ("ΦΠΑ", "integration", "φορολογικός όρος"),
    ("μηνιαία φορολογική δήλωση", "integration", "εφορία"),
    ("ετήσια φορολογική δήλωση", "integration", "εφορία"),
    ("επιστροφή φόρου", "integration", "εφορία"),
    ("απαλλαγή από τέλος επιτηδεύματος", "integration", "εφορία"),

    # ---- DOCUMENTATION extras ----
    ("αστυνομικός έλεγχος με πρακτικό", "documentation", "διοικητικό έγγραφο"),
    ("δελτίο συμβάντος αστυνομίας", "documentation", "διοικητικό έγγραφο"),
    ("μηνυτήρια αναφορά", "documentation", "νομικό έγγραφο"),
    ("ιατρική βεβαίωση από νοσοκομείο", "documentation", "ιατρικό έγγραφο"),
    ("γνωμάτευση ιατρού ειδικότητας", "documentation", "ιατρικό έγγραφο"),
    ("συνταγή ιατρικών εξετάσεων", "documentation", "ιατρικό έγγραφο"),
    ("παραπεμπτικό για εξέταση", "documentation", "ιατρικό διοικητικό"),
    ("έντυπο νοσηλείας", "documentation", "ιατρικό διοικητικό"),
    ("έντυπο εξιτηρίου", "documentation", "ιατρικό διοικητικό"),
    ("κάρτα υγείας αλλοδαπών (ΚΥΠΑ)", "documentation", "διοικητικό έγγραφο υγείας"),
    ("πράξη εκκαθάρισης ΕΦΚΑ", "documentation", "διοικητικό ασφαλιστικό"),
    ("βεβαίωση ασφαλιστικής ενημερότητας", "documentation", "διοικητικό ασφαλιστικό"),
    ("βεβαίωση φορολογικής ενημερότητας", "documentation", "διοικητικό φορολογικό"),
    ("απόσπασμα ποινικού μητρώου γενικής χρήσης", "documentation", "νομικό έγγραφο"),
    ("απόσπασμα ποινικού μητρώου δικαστικής χρήσης", "documentation", "νομικό έγγραφο"),
    ("πιστοποιητικό ελληνομάθειας ΚΕΓ", "documentation", "εκπαιδευτικό πιστοποιητικό"),

    # ---- FAMILY extras ----
    ("γάμος σε τρίτη χώρα", "family", "οικογενειακό γεγονός"),
    ("θρησκευτικός γάμος χωρίς πολιτικό", "family", "οικογενειακό στοιχείο"),
    ("συμβίωση χωρίς γάμο", "family", "συνθήκες συμβίωσης"),
    ("σύμφωνο συμβίωσης", "family", "νομικό πλαίσιο"),
    ("επιμέλεια τέκνου κοινή", "family", "διάταξη επιμέλειας"),
    ("επιμέλεια τέκνου αποκλειστική", "family", "διάταξη επιμέλειας"),
    ("επικοινωνία γονέα με τέκνο", "family", "δικαίωμα"),
    ("διατροφή τέκνου", "family", "νομικό δικαίωμα"),
    ("διεθνής απαγωγή παιδιού", "family", "Χάγη 1980"),
    ("αναδοχή ανηλίκου", "family", "παιδική προστασία"),
    ("υιοθεσία διακρατική", "family", "διεθνής υιοθεσία"),
    ("ασυνόδευτο βρέφος", "family", "ειδική κατηγορία"),

    # ---- VULNERABLE — religion & gender depth ----
    ("θύμα δίωξης βάσει θρησκείας", "vulnerable", "grounds for persecution"),
    ("θύμα δίωξης βάσει σεξουαλικού προσανατολισμού", "vulnerable", "grounds"),
    ("θύμα δίωξης βάσει ταυτότητας φύλου", "vulnerable", "grounds"),
    ("θύμα δίωξης βάσει πολιτικής γνώμης", "vulnerable", "grounds"),
    ("θύμα δίωξης βάσει εθνικότητας ή φυλής", "vulnerable", "grounds"),
    ("θύμα δίωξης βάσει συμμετοχής σε ιδιαίτερη κοινωνική ομάδα", "vulnerable", "grounds PSG"),
    ("άτομο που αποκήρυξε θρησκεία (απόστατης)", "vulnerable", "apostasy persecution"),
    ("άτομο που άλλαξε θρησκεία", "vulnerable", "conversion persecution"),
    ("άθεος από ισλαμική χώρα", "vulnerable", "atheism persecution"),
    ("μέλος διωκόμενης θρησκευτικής μειονότητας", "vulnerable", "religious minority"),
    ("γυναίκα σε χώρα με sharia", "vulnerable", "gender-based persecution"),
    ("γυναίκα που αρνήθηκε αναγκαστικό γάμο", "vulnerable", "GBV"),
    ("γυναίκα θύμα εγκλήματος τιμής", "vulnerable", "honour-based violence"),
    ("άτομο ΛΟΑΤΚΙ+ σε χώρα ποινικοποίησης", "vulnerable", "SOGI persecution"),
    ("ενεργός ακτιβιστής δικαιωμάτων γυναικών", "vulnerable", "political activist grounds"),
    ("δημοσιογράφος υπό δίωξη", "vulnerable", "professional grounds"),
    ("συνδικαλιστής υπό δίωξη", "vulnerable", "professional grounds"),
    ("λιποτάκτης στρατού", "vulnerable", "military desertion grounds"),
    ("άρνηση στράτευσης για λόγους συνείδησης", "vulnerable", "conscientious objector"),

    # ---- PROCEDURE — religion/gender-specific interview handling ----
    ("συνέντευξη για θρησκευτική δίωξη", "procedure", "specialised interview"),
    ("συνέντευξη για SOGI αίτημα", "procedure", "specialised interview"),
    ("συνέντευξη για GBV αίτημα", "procedure", "specialised interview"),
    ("γυναίκα χειριστής για GBV", "procedure", "procedural guarantee"),
    ("γυναίκα διερμηνέας για GBV", "procedure", "procedural guarantee"),
    ("δωμάτιο συνέντευξης προστατευμένο", "procedure", "safe space"),
    ("διάλειμμα κατά τη διάρκεια συνέντευξης", "procedure", "procedural"),
    ("συνέντευξη με ψυχολόγο παρόντα", "procedure", "vulnerable-friendly"),
    ("συνέντευξη ανηλίκου με ψυχολόγο και επίτροπο", "procedure", "child-friendly"),
    ("απομαγνητοφώνηση συνέντευξης", "procedure", "διοικητικό βήμα"),
    ("διόρθωση απομαγνητοφώνησης", "procedure", "διοικητικό βήμα"),
    ("υπογραφή απομαγνητοφώνησης από αιτούντα", "procedure", "διαδικαστικό"),

    # ---- LEGAL — Greek immigration code specifics ----
    ("Ν.4251/2014 Κώδικας Μετανάστευσης", "legal", "νομοθεσία μετανάστευσης"),
    ("άδεια διαμονής για εξαιρετικούς λόγους", "legal", "τύπος άδειας"),
    ("άδεια διαμονής για εργασία", "legal", "τύπος άδειας"),
    ("άδεια διαμονής για σπουδές", "legal", "τύπος άδειας"),
    ("άδεια διαμονής για ιατρικούς λόγους", "legal", "τύπος άδειας"),
    ("άδεια διαμονής για ανθρωπιστικούς λόγους", "legal", "τύπος άδειας"),
    ("μπλε κάρτα ΕΕ", "legal", "EU Blue Card"),
    ("άδεια διαμονής επί μακρόν διαμένοντος", "legal", "long-term residence"),
    ("θεώρηση εισόδου τύπου C", "legal", "short-stay visa"),
    ("θεώρηση εισόδου τύπου D", "legal", "long-stay visa"),
    ("άσυλο δυνάμει άρθρου 3 ΕΣΔΑ", "legal", "protection basis"),
    ("άσυλο δυνάμει άρθρου 33 Σύμβασης Γενεύης", "legal", "non-refoulement basis"),
    ("επίδραση δεδικασμένου σε νεότερη αίτηση", "legal", "res judicata"),
    ("νέα στοιχεία σε μεταγενέστερη αίτηση", "legal", "new evidence standard"),

    # ---- COMMUNICATION extras ----
    ("διερμηνέας για ασυνόδευτο ανήλικο", "communication", "specialised interpreter"),
    ("διερμηνέας για συνέντευξη GBV", "communication", "specialised interpreter"),
    ("διερμηνέας για ιατρικό ραντεβού", "communication", "specialised interpreter"),
    ("διερμηνέας για ψυχοθεραπεία", "communication", "specialised interpreter"),
    ("διερμηνέας για δικαστική συνέντευξη", "communication", "court interpreter"),
    ("διερμηνέας για νομική συμβουλή", "communication", "legal interpreter"),
    ("διερμηνέας για αίτηση ιθαγένειας", "communication", "citizenship interpreter"),
    ("διαχείριση σιωπής στη συνέντευξη", "communication", "interpreter technique"),
    ("διαχείριση συγκίνησης αιτούντος", "communication", "interpreter technique"),
    ("αναζήτηση διευκρίνισης άγνωστου όρου", "communication", "clarification"),

    # ---- MEDICAL — a few more high-value ----
    ("επιληπτική κρίση", "medical", "νευρολογικό επείγον"),
    ("αναπνευστική κρίση άσθματος", "medical", "επείγον"),
    ("αλλεργική αντίδραση σε τσίμπημα", "medical", "επείγον"),
    ("έγκυος με αιμορραγία", "medical", "μαιευτικό επείγον"),
    ("τοκετός εν οίκω", "medical", "μαιευτικό συμβάν"),
    ("έμφραγμα μυοκαρδίου", "medical", "καρδιολογικό επείγον"),
    ("εγκεφαλικό αγγειακό επεισόδιο", "medical", "νευρολογικό επείγον"),
    ("υπερβολική δόση φαρμάκου", "medical", "τοξικολογικό επείγον"),
    ("αυτοπυρπόληση", "medical", "ψυχιατρικό επείγον"),
    ("αυτοκτονική απόπειρα", "medical", "ψυχιατρικό επείγον"),
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
    added = 0; skipped = 0; failed = []
    total = len(SEED)
    for i, (greek, cat, hint) in enumerate(SEED, 1):
        if greek.strip().lower() in existing_el:
            skipped += 1; continue
        payload = greek if not hint else f"{greek} ({hint})"
        print(f"  [{i}/{total}] [{cat}] {greek} …")
        try:
            resp = translate(payload)
        except Exception as e:
            print(f"    ERR: {e}"); failed.append(greek); time.sleep(1.0); continue
        if not resp.get("translations"):
            print(f"    no translations"); failed.append(greek); continue
        translations = {}
        for lang in ["el", "en", "ar", "fa", "fr"]:
            v = (resp["translations"].get(lang) or "").strip()
            if lang == "el": v = greek
            translations[lang] = v
        en = translations.get("en", "")
        base = slugify(en) or slugify(greek) or f"{cat}-{i}"
        slug = base; n = 2
        while slug in existing_ids:
            slug = f"{base}-{n}"; n += 1
        data["terms"].append({
            "id": slug, "category": cat, "translations": translations,
            "definition_el": (resp.get("definition_el") or "").strip(),
            "definition_en": (resp.get("definition_en") or "").strip(),
            "sources": [f"AI-generated ({resp.get('model')}) 2026-09-06 — needs native review"]
        })
        existing_ids.add(slug); existing_el.add(greek.strip().lower())
        added += 1; time.sleep(0.3)
    data["meta"]["version"] = "0.7.0"; data["meta"]["updated"] = "2026-09-06"
    with open(TERMS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print()
    print(f"added: {added}  skipped: {skipped}  failed: {len(failed)}  total: {len(data['terms'])}")
    if failed:
        for g in failed[:20]: print(f"  - {g}")

if __name__ == "__main__": main()
