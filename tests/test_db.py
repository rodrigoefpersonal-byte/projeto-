from leadbot import db


def test_phone_normalization():
    assert db.normalize_phone("(11) 98765-4321") == "5511987654321"
    assert db.normalize_phone("+55 11 3456-7890") == "551134567890"
    assert db.normalize_phone("123") is None


def test_optout_words():
    assert db.is_optout_text("por favor PARE de mandar")
    assert db.is_optout_text("não quero")
    assert not db.is_optout_text("quanto custa?")


def test_dedupe_and_optout(tmp_path):
    con = db.connect(tmp_path / "t.db")
    assert db.add_lead(con, source_id="a", name="X", phone="11987654321")
    assert not db.add_lead(con, source_id="b", name="X2", phone="(11) 98765-4321")
    db.opt_out(con, "11987654321")
    assert con.execute("SELECT status FROM leads").fetchone()[0] == "opted_out"
    assert not db.add_lead(con, source_id="c", name="X3", phone="11987654321")
