from h2s_reader.h2s_sensor import Reading
from h2s_reader.__main__ import format_reading


def test_format_reading_contains_ppm_and_temp():
    line = format_reading(Reading(ppm=50.0, i_we_uA=5.02, vout_v=0.5351,
                                  temp_c=25.0, r_ntc_ohm=10000.0))
    assert "50.00 ppm" in line
    assert "25.00 C" in line
    assert "uA" in line
