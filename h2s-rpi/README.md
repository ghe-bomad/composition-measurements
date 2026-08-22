# H2S-RPi reader

Reads the Mzuzu H2S sensor PCB (LMP91002 potentiostat + ADS1115 ADC) over I²C on a
Raspberry Pi 5 and reports H₂S concentration (ppm) and sensor temperature (°C).
The LMP91002 is configured to use the on-board **external 2.5 V reference (ADR3425)**.

## Wiring / addresses

- Connect the PCB terminal block (CN1): **5 V**, **GND**, **SDA**, **SCL** to the Pi.
- I²C bus `1` (`/dev/i2c-1`), 3.3 V logic (level-correct on the board).
- Devices: LMP91002 at `0x48`, ADS1115 at `0x49`.

## Pi 5 setup

```bash
sudo raspi-config    # Interface Options -> I2C -> enable   (dtparam=i2c_arm=on)
sudo apt install -y python3-pip i2c-tools
pip install smbus2
i2cdetect -y 1       # expect 0x48 and 0x49
```

## Usage

```bash
cd src/h2s-rpi
python -m h2s_reader --selftest        # verify both devices respond
python -m h2s_reader                    # one reading
python -m h2s_reader --stream --interval 2
```

## Calibrating / tuning

All tunable values live in `h2s_reader/config.py`:
- H₂S: `I0_UA` (zero-gas baseline) and `SENSITIVITY_UA_PER_PPM` — from your cal certificate.
- NTC: `NTC_R0`, `NTC_BETA`, `NTC_R_FIXED`, `NTC_VSUPPLY`.
- AFE: `R_TIA`, `INT_Z`/`REFCN_VALUE`, `POLARITY`.

## Bring-up checklist

1. `i2cdetect -y 1` shows `0x48` and `0x49`.
2. **Swing direction:** at zero gas `Vout ≈ 0.50 V`; applying H₂S should make it **increase**.
   If it instead **decreases**, the cell swings the other way and 20 % zero leaves too little
   downward headroom (a full-range signal would clip at 0 V). Move the zero high *and* flip the
   sign in `config.py`: set `INT_Z = 0.67`, `REFCN_VALUE = 0xC0` (external ref + 67 % zero), and
   `POLARITY = -1`.
3. Confirm baseline stability over hours/days in the anaerobic environment (see below).
4. If temperature accuracy matters, set `NTC_VSUPPLY` to the measured 3.3 V rail (LP5907 ~±1 %).

## Deployment considerations (digester environment)

These are siting/hardware notes — they do not change the code:

- **Cross-sensitivity:** CO, NH₃ and trace H₂ are oxidized the same direction as H₂S and read
  as *extra apparent H₂S*. NH₃ matters for ammonia-rich human/organic waste. Correcting for it
  would need a separate measurement; rely on sensor selectivity + periodic calibration.
- **Near-zero O₂:** amperometric H₂S cells generally assume some ambient O₂ at the counter
  electrode. A fully anaerobic stream is outside typical spec — validate baseline stability.
- **Range & sensor life:** the cell caps at 1000 ppm and is consumable; sustained high H₂S
  shortens its life. Dilute if you expect > 1000 ppm.
- **Water-saturated gas:** condensation is a corrosion/reading risk (esp. the resin-sealed
  electrolyte port under the sensor) — a hydrophobic membrane and conformal coat help.
