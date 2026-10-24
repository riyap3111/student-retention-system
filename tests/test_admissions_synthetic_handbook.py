from admissions_platform.synthetic.handbook import load_sample_handbook_text


def test_load_sample_handbook_text_contains_expected_policy_sections():
    text = load_sample_handbook_text()
    assert "Brightwater University" in text
    assert "2.75" in text  # minimum GPA policy, referenced by future rules-extraction tests
    assert "withdraw" in text.lower()
