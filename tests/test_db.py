from leadbot import db


def test_phone_normalization():
    assert db.normalize_phone("(11) 98765-4321") == "5511987654321"
    assert db.normalize_phone("+55 11 3456-7890") == "551134567890"
    assert db.normalize_phone("+52 55 1234 5678") == "525512345678"
    assert db.normalize_phone("(305) 555-0142", "1") == "13055550142"
    assert db.normalize_phone("123") is None


def test_optout_words():
    for t in ("por favor PARE", "não quero", "baja por favor", "no quiero más", "unsubscribe", "stop"):
        assert db.is_optout_text(t), t
    assert not db.is_optout_text("quanto custa? / cuánto cuesta?")


def test_whatsapp_number_variants_match():
    # México: Places dá +52 55..., WhatsApp entrega 521 55...
    assert db.contact_key("+52 55 1234 5678") == db.contact_key("5215512345678")


def test_dedupe_and_optout(tmp_path):
    con = db.connect(tmp_path / "t.db")
    assert db.add_lead(con, source_id="a", name="X", phone="11987654321", cc="55")
    assert not db.add_lead(con, source_id="b", name="X2", phone="(11) 98765-4321", cc="55")
    db.opt_out(con, "5511987654321")
    assert con.execute("SELECT status FROM leads").fetchone()[0] == "opted_out"
    assert not db.add_lead(con, source_id="c", name="X3", phone="11987654321", cc="55")
    assert db.find_by_phone(con, "5511987654321")["name"] == "X"


def test_csv_import_and_free_qualify(tmp_path):
    import yaml
    from leadbot import pipeline
    cfg = yaml.safe_load(open("config.example.yaml", encoding="utf-8"))
    con = db.connect(tmp_path / "t.db")
    pipeline.import_csv(cfg, con, "leads_exemplo.csv")
    pipeline.qualify(cfg, con)
    rows = {r["name"]: r for r in con.execute("SELECT * FROM leads")}
    assert rows["Barbearia Fio"]["instagram"] == "barbeariafio"
    assert rows["Odonto Sorriso"]["status"] == "qualified"
