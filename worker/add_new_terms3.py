#!/usr/bin/env python3
"""Third batch — depth in medical, legal, return, detention, procedure, status."""
import json, sys, time, re, unicodedata
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

WORKER = "https://cool-moon-d7ebitalk-translate.metlamari.workers.dev/"
TERMS = "C:/Users/italk/italk/data/terms.json"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

SEED = [
    # ---- MEDICAL — ENT / dermatology / pediatrics / OB-GYN / chronic ----
    ("ωτίτιδα", "medical", "ωτορινολαρυγγολογική λοίμωξη"),
    ("ιγμορίτιδα", "medical", "λοίμωξη παραρρίνιων"),
    ("φαρυγγίτιδα", "medical", "λοίμωξη λαιμού"),
    ("αμυγδαλίτιδα", "medical", "λοίμωξη αμυγδαλών"),
    ("ρινορραγία", "medical", "αιμορραγία από τη μύτη"),
    ("βαρηκοΐα", "medical", "μειωμένη ακοή"),
    ("εμβοές", "medical", "ηχητικό σύμπτωμα ωτών"),
    ("ίλιγγος", "medical", "αίσθηση περιστροφής"),
    ("δυσφαγία", "medical", "δυσκολία κατάποσης"),
    ("κνίδωση", "medical", "δερματική αντίδραση"),
    ("μελάνωμα", "medical", "καρκίνος δέρματος"),
    ("ουλή", "medical", "τραυματική δερματική βλάβη"),
    ("ψώρα", "medical", "δερματική παρασιτική νόσος"),
    ("δερματοφυτίαση", "medical", "μυκητίαση δέρματος"),
    ("εμβόλιο ιλαράς-ερυθράς-παρωτίτιδας", "medical", "παιδικό εμβόλιο MMR"),
    ("εμβόλιο διφθερίτιδας-τετάνου-κοκκύτη", "medical", "παιδικό εμβόλιο DTP"),
    ("εμβόλιο πολυομυελίτιδας", "medical", "παιδικό εμβόλιο"),
    ("παιδική διάρροια", "medical", "παιδιατρικό επείγον"),
    ("καθυστέρηση ανάπτυξης παιδιού", "medical", "παιδιατρική αξιολόγηση"),
    ("αυτισμός", "medical", "νευροαναπτυξιακή διαταραχή"),
    ("ΔΕΠΥ ADHD", "medical", "νευροαναπτυξιακή διαταραχή"),
    ("δυσλεξία", "medical", "μαθησιακή δυσκολία"),
    ("προεκλαμψία", "medical", "επιπλοκή εγκυμοσύνης"),
    ("εκλαμψία", "medical", "επείγον εγκυμοσύνης"),
    ("εξωμήτριος κύηση", "medical", "επείγον γυναικολογικό"),
    ("δυσμηνόρροια", "medical", "επώδυνη εμμηνόρροια"),
    ("στειρότητα", "medical", "γυναικολογική/ανδρολογική"),
    ("πνιγμονή από τροφή", "medical", "επείγον αναπνευστικό"),
    ("ασφυξία", "medical", "επείγον αναπνευστικό"),
    ("διάσειση εγκεφάλου", "medical", "τραυματολογία"),
    ("τραύμα κεφαλής", "medical", "τραυματολογία"),
    ("έγκαυμα α' βαθμού", "medical", "τραυματολογία"),
    ("έγκαυμα β' βαθμού", "medical", "τραυματολογία"),
    ("έγκαυμα γ' βαθμού", "medical", "τραυματολογία σοβαρή"),
    ("δηλητηρίαση από ναρκωτικά", "medical", "τοξικολογία επείγον"),
    ("αρθρίτιδα", "medical", "χρόνια πάθηση"),
    ("οστεοπόρωση", "medical", "χρόνια πάθηση σκελετού"),
    ("ρευματοειδής αρθρίτιδα", "medical", "αυτοάνοση πάθηση"),
    ("χρόνια νεφρική ανεπάρκεια", "medical", "νεφρολογική πάθηση"),
    ("αιμοκάθαρση", "medical", "θεραπεία νεφρικής ανεπάρκειας"),
    ("οξύς πόνος", "medical", "κατηγορία πόνου"),
    ("χρόνιος πόνος", "medical", "κατηγορία πόνου"),
    ("οσφυαλγία-ισχιαλγία", "medical", "πόνος πλάτης"),
    ("έλλειψη βιταμίνης D", "medical", "διατροφική έλλειψη"),
    ("έλλειψη βιταμίνης B12", "medical", "διατροφική έλλειψη"),
    ("αφυδάτωση", "medical", "κλινική κατάσταση"),
    ("υπογλυκαιμία", "medical", "επιπλοκή διαβήτη"),
    ("υπεργλυκαιμία", "medical", "επιπλοκή διαβήτη"),
    ("διαβητικό κώμα", "medical", "επείγον διαβήτη"),
    ("αλλεργικό σοκ", "medical", "επείγον αλλεργικό"),

    # ---- MEDICAL — cardiology / neurology depth ----
    ("αρτηριακή πίεση", "medical", "καρδιαγγειακό μέγεθος"),
    ("καρδιακός ρυθμός", "medical", "καρδιακό μέγεθος"),
    ("κολπική μαρμαρυγή", "medical", "αρρυθμία"),
    ("βηματοδότης", "medical", "καρδιολογική συσκευή"),
    ("στεφανιαία νόσος", "medical", "καρδιαγγειακή πάθηση"),
    ("φύσημα καρδιάς", "medical", "καρδιολογικό σημείο"),
    ("θρόμβωση", "medical", "αγγειακή πάθηση"),
    ("πνευμονική εμβολή", "medical", "επείγον καρδιοπνευμονικό"),
    ("υπερλιπιδαιμία", "medical", "μεταβολική πάθηση"),
    ("υπερτριγλυκεριδαιμία", "medical", "μεταβολική"),
    ("κρίση ημικρανίας", "medical", "νευρολογικό επείγον"),
    ("νευραλγία τριδύμου", "medical", "νευρολογική πάθηση"),
    ("περιφερική νευροπάθεια", "medical", "νευρολογική πάθηση"),
    ("Πάρκινσον τρόμος", "medical", "σύμπτωμα νόσου Πάρκινσον"),
    ("μυασθένεια", "medical", "νευρομυϊκή πάθηση"),

    # ---- LEGAL — EU / international / humanitarian ----
    ("Σύμβαση της Γενεύης 1951", "legal", "θεμελιώδης σύμβαση προσφύγων"),
    ("Πρωτόκολλο 1967 Νέας Υόρκης", "legal", "συμπλήρωμα σύμβασης Γενεύης"),
    ("Παγκόσμια Διακήρυξη Ανθρωπίνων Δικαιωμάτων", "legal", "διεθνές έγγραφο 1948"),
    ("Σύμβαση κατά των Βασανιστηρίων", "legal", "CAT 1984"),
    ("Σύμβαση για τα Δικαιώματα του Παιδιού", "legal", "CRC 1989"),
    ("Σύμβαση για την Εξάλειψη Διακρίσεων κατά των Γυναικών", "legal", "CEDAW 1979"),
    ("Ευρωπαϊκή Σύμβαση Δικαιωμάτων του Ανθρώπου άρθρο 3", "legal", "απαγόρευση απάνθρωπης μεταχείρισης"),
    ("Ευρωπαϊκή Σύμβαση Δικαιωμάτων του Ανθρώπου άρθρο 8", "legal", "ιδιωτική και οικογενειακή ζωή"),
    ("Χάρτης Θεμελιωδών Δικαιωμάτων της ΕΕ", "legal", "primary EU law"),
    ("Οδηγία 2013/33/ΕΕ Υποδοχής", "legal", "Reception Conditions Directive"),
    ("Κανονισμός Δουβλίνο III", "legal", "Regulation 604/2013"),
    ("Κανονισμός EURODAC", "legal", "603/2013 fingerprint database"),
    ("γενικές αρχές δικαίου ΕΕ", "legal", "primary source EU law"),
    ("δικαστική ερμηνεία σύμφωνη με την οδηγία", "legal", "conforming interpretation"),
    ("ευρωπαϊκή εντολή σύλληψης", "legal", "EAW instrument"),
    ("έκδοση αλλοδαπού", "legal", "extradition"),
    ("άσυλο διπλωματικό", "legal", "diplomatic asylum"),
    ("άσυλο πολιτικό", "legal", "political asylum"),
    ("διεθνές ανθρωπιστικό δίκαιο", "legal", "IHL, Geneva Conventions"),
    ("απαγόρευση συλλογικής απέλασης", "legal", "άρθρο 4 πρωτοκόλλου 4 ΕΣΔΑ"),
    ("μη εξαναγκαστική επιστροφή", "legal", "non-refoulement principle expansion"),
    ("διεθνής προστασία vs εθνική προστασία", "legal", "διάκριση"),
    ("επικύρωση διεθνών συμβάσεων", "legal", "εθνική διαδικασία"),
    ("ratio decidendi", "legal", "λατινικός νομικός όρος"),
    ("obiter dictum", "legal", "λατινικός νομικός όρος"),

    # ---- LEGAL — Greek asylum code specifics ----
    ("Κώδικας Νομοθεσίας Διεθνούς Προστασίας", "legal", "Ν.4939/2022 συνολικά"),
    ("Άρθρο 2 Ν.4939 ορισμοί", "legal", "βασικοί ορισμοί"),
    ("Άρθρο 5 Ν.4939 προσφυγική ιδιότητα", "legal", "χορήγηση προσφυγικής"),
    ("Άρθρο 15 Ν.4939 επικουρική", "legal", "χορήγηση επικουρικής"),
    ("Άρθρο 22 Ν.4939 πρόσβαση σε διαδικασία", "legal", "διαδικαστικό"),
    ("Άρθρο 65 Ν.4939 συνέντευξη", "legal", "διαδικαστικό"),
    ("Άρθρο 82 Ν.4939 προσφυγή", "legal", "διαδικαστικό"),
    ("διάταξη νόμου", "legal", "νομοθετικό μέρος"),
    ("αιτιολογική έκθεση νόμου", "legal", "νομοθετικό υλικό"),
    ("κανονιστική πράξη διοίκησης", "legal", "εκτελεστικό δίκαιο"),
    ("διοικητική εγκύκλιος", "legal", "εσωτερική οδηγία διοίκησης"),
    ("υπουργική απόφαση", "legal", "εκτελεστικό δίκαιο"),
    ("ΦΕΚ Εφημερίς της Κυβερνήσεως", "legal", "δημοσίευση νόμων"),

    # ---- PROCEDURE — APR / Pact detail ----
    ("Άρθρο 42 APR επιταχυνόμενη", "procedure", "accelerated procedure grounds"),
    ("Άρθρο 43 APR συνοριακή διαδικασία", "procedure", "border procedure"),
    ("Άρθρο 21 APR πληροφορίες αιτούντος", "procedure", "information rights"),
    ("Άρθρο 28 APR ρόλος διερμηνέα", "procedure", "interpreter under APR"),
    ("ΑΠΡ αίτηση χωρίς νομική συνδρομή σε α' βαθμό", "procedure", "APR practical"),
    ("χρόνος εξέτασης 3 μηνών", "procedure", "APR deadline"),
    ("χρόνος εξέτασης 6 μηνών παράταση", "procedure", "APR extension"),
    ("σιωπηρή απόρριψη", "procedure", "άπρακτη προθεσμία"),
    ("υποχρέωση συνεργασίας αιτούντος", "procedure", "cooperation duty"),
    ("συνέπειες μη συνεργασίας", "procedure", "APR sanctions"),
    ("απόρριψη ως προδήλως αβάσιμη", "procedure", "manifestly unfounded"),
    ("απόρριψη ως καταχρηστική", "procedure", "abuse of process"),
    ("διακοπή διαδικασίας", "procedure", "discontinuation"),
    ("αποχώρηση αιτούντος από τη δομή", "procedure", "absconding"),
    ("Επιτροπή Ελέγχου Νομιμότητας Κράτησης", "procedure", "όργανο δικαστικού ελέγχου"),

    # ---- RETURN — expansion ----
    ("απόφαση επιστροφής", "return", "διοικητική πράξη"),
    ("χορήγηση προθεσμίας οικειοθελούς αναχώρησης", "return", "πράξη"),
    ("οικειοθελής αναχώρηση χωρίς βοήθεια", "return", "μέθοδος επιστροφής"),
    ("οικειοθελής επιστροφή με μετρητά επανένταξης", "return", "AVR variant"),
    ("επιστροφή σε τρίτη ασφαλή χώρα", "return", "τύπος επιστροφής"),
    ("κράτηση για σκοπούς απομάκρυνσης", "return", "detention for return"),
    ("συμφωνία επανεισδοχής με τρίτη χώρα", "return", "readmission agreement variant"),
    ("συμφωνία επανεισδοχής με χώρα καταγωγής", "return", "readmission"),
    ("διαβατήριο επαναπατρισμού", "return", "laissez-passer for return"),
    ("άρνηση παραλαβής από τη χώρα καταγωγής", "return", "practical obstacle"),
    ("διακοπή διαδικασίας απομάκρυνσης", "return", "suspension"),
    ("απόφαση Δικαστηρίου κατά της απομάκρυνσης", "return", "judicial suspension"),
    ("μη επαναπροώθηση σε χώρα κινδύνου", "return", "non-refoulement in return"),
    ("επαναπροώθηση δια θαλάσσης (pushback)", "return", "unlawful practice"),
    ("επαναπροώθηση στη ζώνη Έβρου", "return", "documented practice"),
    ("Frontex σε επιχειρήσεις επιστροφής", "return", "joint operations"),
    ("συνοδεία αστυνομικού σε πτήση επιστροφής", "return", "escort protocol"),
    ("ιατρός σε πτήση επιστροφής", "return", "medical escort"),
    ("απαγόρευση εισόδου Schengen", "return", "SIS alert"),
    ("διαγραφή απαγόρευσης εισόδου", "return", "delisting SIS"),

    # ---- DETENTION — depth ----
    ("απόφαση κράτησης του Διευθυντή", "detention", "διοικητική απόφαση"),
    ("γνωστοποίηση απόφασης κράτησης εγγράφως", "detention", "διαδικαστική πράξη"),
    ("μετάφραση απόφασης κράτησης", "detention", "διαδικαστικό δικαίωμα"),
    ("μηνιαίος έλεγχος συνθηκών κράτησης", "detention", "monitoring"),
    ("έλεγχος από ανεξάρτητο μηχανισμό", "detention", "external monitoring"),
    ("επίσκεψη Ερυθρού Σταυρού σε κράτηση", "detention", "ICRC access"),
    ("επίσκεψη CPT σε κράτηση", "detention", "Council of Europe monitoring"),
    ("υπερπληρότητα χώρου κράτησης", "detention", "συνθήκες"),
    ("έλλειψη προσωπικής υγιεινής σε κράτηση", "detention", "συνθήκες"),
    ("ψυχολογική υποστήριξη σε κράτηση", "detention", "παροχή υπηρεσίας"),
    ("απεργία πείνας σε κράτηση", "detention", "μορφή διαμαρτυρίας"),
    ("αυτοκτονία σε κράτηση", "detention", "θανάσιμο συμβάν"),
    ("θάνατος σε κράτηση", "detention", "θανάσιμο συμβάν"),
    ("επίσκεψη οικογένειας σε κράτηση", "detention", "δικαίωμα"),
    ("επίσκεψη δικηγόρου σε κράτηση", "detention", "δικαίωμα"),
    ("επικοινωνία με ΜΚΟ σε κράτηση", "detention", "δικαίωμα"),

    # ---- STATUS extras ----
    ("δικαιούχος διεθνούς προστασίας με τριετή άδεια διαμονής", "status", "residence permit"),
    ("δικαιούχος επικουρικής με τριετή άδεια διαμονής", "status", "residence permit"),
    ("ανανέωση καθεστώτος πρόσφυγα", "status", "διοικητικό βήμα"),
    ("άρση καθεστώτος πρόσφυγα", "status", "cessation act"),
    ("επιστροφή στη χώρα καταγωγής προσωρινή", "status", "risk of cessation"),
    ("μεταβίβαση καθεστώτος σε τέκνο", "status", "παράγωγη προστασία"),
    ("μεταβίβαση καθεστώτος σε σύζυγο", "status", "παράγωγη προστασία"),
    ("έγκυρο διαβατήριο χώρας καταγωγής", "status", "διαδικαστικό στοιχείο"),
    ("διπλή υπηκοότητα", "status", "καθεστώς πολιτότητας"),
    ("απόκτηση ελληνικής ιθαγένειας μέσω πολιτογράφησης", "status", "citizenship"),

    # ---- VULNERABLE extras ----
    ("άτομο που έχει υποστεί ακρωτηριασμό γεννητικών οργάνων (FGM)", "vulnerable", "IPSN"),
    ("θύμα σεξουαλικής εκμετάλλευσης", "vulnerable", "IPSN THB variant"),
    ("θύμα εργασιακής εκμετάλλευσης", "vulnerable", "IPSN THB variant"),
    ("παιδί-στρατιώτης", "vulnerable", "IPSN, ειδική κατηγορία"),
    ("μη συνοδευόμενη έγκυος ανήλικη", "vulnerable", "διπλή ευαλωτότητα"),
    ("ασυνόδευτο παιδί με χρόνια ασθένεια", "vulnerable", "διπλή ευαλωτότητα"),
    ("πρόσωπο με σοβαρή εξάρτηση από φροντίδα", "vulnerable", "IPSN"),
    ("επιζών γενοκτονίας", "vulnerable", "IPSN"),
    ("επιζών βασανιστηρίων εν καιρώ πολέμου", "vulnerable", "IPSN torture"),
    ("επιζών βίας κατά μελών ΛΟΑΤΚΙ+", "vulnerable", "IPSN gender-related"),

    # ---- COMMUNICATION / cultural mediation extras ----
    ("κώδικας δεοντολογίας διερμηνέα ΜΕΤΑδρασης", "communication", "τεκμηρίωση"),
    ("ρόλος πολιτισμικού διαμεσολαβητή", "communication", "job description"),
    ("διαφορά διερμηνέα-διαμεσολαβητή", "communication", "εννοιολογική"),
    ("κώδικας εμπιστευτικότητας", "communication", "δεοντολογία"),
    ("διαχείριση δευτερογενούς τραύματος διερμηνέα", "communication", "self-care"),
    ("επίπεδα γλωσσομάθειας CEFR", "communication", "language framework"),
    ("γλωσσικός συνδυασμός", "communication", "language pair"),
    ("ενεργός γλώσσα διερμηνέα", "communication", "professional term"),
    ("παθητική γλώσσα διερμηνέα", "communication", "professional term"),
    ("πίνακας διερμηνέων του δικαστηρίου", "communication", "θεσμική λίστα"),
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
            skipped += 1
            continue
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
        existing_ids.add(slug)
        existing_el.add(greek.strip().lower())
        added += 1
        time.sleep(0.3)

    data["meta"]["version"] = "0.6.0"
    data["meta"]["updated"] = "2026-09-06"
    with open(TERMS, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print()
    print(f"added: {added}  skipped: {skipped}  failed: {len(failed)}  total: {len(data['terms'])}")
    if failed:
        for g in failed[:20]: print(f"  - {g}")

if __name__ == "__main__":
    main()
