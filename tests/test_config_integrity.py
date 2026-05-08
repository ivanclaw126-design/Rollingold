from rollingold.config import load_config


def test_industry_mapping_has_required_contracts():
    config = load_config()

    assert config.benchmark_code == "801003"
    assert len(config.industries) == 26
    assert len(set(config.industry_names)) == 26

    for industry in config.industries:
        assert industry.price_sources, industry.name
        assert industry.breadth_sources, industry.name
        assert industry.etf_rule.fallback_code, industry.name
        assert industry.etf_rule.fallback_name, industry.name
        assert industry.etf_rule.match_note, industry.name
