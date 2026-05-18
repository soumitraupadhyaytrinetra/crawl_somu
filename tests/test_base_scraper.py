import pytest
from scrapers.base_scraper import extract_tech_hints, extract_pricing_plans, detect_virtual_tryon

def test_extract_tech_hints_finds_keywords():
    text = "Our platform uses AR, AI, LiDAR and 3D technology for virtual try-on."
    hints = extract_tech_hints(text)
    assert "AR" in hints
    assert "AI" in hints
    assert "3D" in hints
    assert "LiDAR" in hints

def test_extract_tech_hints_no_duplicates():
    text = "AR technology with AR support and more AR features"
    hints = extract_tech_hints(text)
    assert hints.count("AR") == 1

def test_extract_pricing_plans():
    text = "Starter - $99/month\nProfessional - $299/month\nEnterprise - Contact us"
    plans = extract_pricing_plans(text)
    assert len(plans) == 3
    assert any("99" in p for p in plans)

def test_detect_virtual_tryon_true():
    text = "Try our AI-powered virtual try-on feature"
    assert detect_virtual_tryon(text) is True

def test_detect_virtual_tryon_false():
    text = "Shop the latest fashion trends online"
    assert detect_virtual_tryon(text) is False

def test_extract_tech_hints_empty_text():
    assert extract_tech_hints("") == []

def test_detect_virtual_tryon_ar_keyword():
    text = "Experience augmented reality shopping"
    assert detect_virtual_tryon(text) is True
