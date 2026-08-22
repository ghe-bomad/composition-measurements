from h2s_reader import config


def test_lmp_register_values_match_spec():
    assert config.TIACN_VALUE == 0x0C
    assert config.REFCN_VALUE == 0x80   # external ref + 20% zero + zero bias
    assert config.MODECN_VALUE == 0x03


def test_ads_config_words():
    assert config.ADS_CONF_AIN0 == 0xC383
    assert config.ADS_CONF_AIN2 == 0xE383


def test_derived_zero_voltage():
    assert abs(config.V_ZERO - 0.50) < 1e-9  # 0.20 * 2.5 V


def test_calibration_constants():
    assert config.I0_UA == 0.063
    assert config.SENSITIVITY_UA_PER_PPM == 0.099
