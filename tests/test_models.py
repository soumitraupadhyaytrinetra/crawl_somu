import pytest
from scrapers.models import CompetitorData, SampleProduct

def test_competitor_data_required_fields():
    c = CompetitorData(
        name="test",
        display_name="Test",
        url="https://test.com",
        region="india",
        type="retailer",
    )
    assert c.name == "test"
    assert c.has_virtual_tryon is False
    assert c.tech_hints == []
    assert c.categories == []
    assert c.sample_products == []
    assert c.pricing_plans == []

def test_competitor_data_region_validation():
    with pytest.raises(Exception):
        CompetitorData(
            name="bad",
            display_name="Bad",
            url="https://bad.com",
            region="mars",
            type="retailer",
        )

def test_competitor_data_type_validation():
    with pytest.raises(Exception):
        CompetitorData(
            name="bad",
            display_name="Bad",
            url="https://bad.com",
            region="india",
            type="unknown",
        )

def test_sample_product_model():
    p = SampleProduct(name="T-Shirt", price=999.0, currency="INR", image_url="https://img.com/1.jpg")
    assert p.name == "T-Shirt"
    assert p.currency == "INR"
