from docxpand.template import DocumentTemplate

def test_load_template():
    template = DocumentTemplate.load("id_card_td1_a")
    assert template.name == "ID_CARD_TD1_A"
    assert template.width == 1011
    assert template.height == 637
    assert "front" in template.sides
    assert "back" in template.sides
