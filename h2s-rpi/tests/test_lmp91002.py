import pytest

from h2s_reader import config
from h2s_reader.lmp91002 import LMP91002
from fakes import FakeBus


def test_configure_writes_unlock_registers_lock_mode_in_order():
    bus = FakeBus()
    LMP91002(bus).configure()
    a = config.LMP91002_ADDR
    assert bus.writes == [
        (a, config.REG_LOCK, config.LOCK_UNLOCK),
        (a, config.REG_TIACN, config.TIACN_VALUE),
        (a, config.REG_REFCN, config.REFCN_VALUE),
        (a, config.REG_LOCK, config.LOCK_LOCK),
        (a, config.REG_MODECN, config.MODECN_VALUE),
    ]


def test_wait_ready_true_when_status_bit_set():
    bus = FakeBus()
    bus.byte_regs[(config.LMP91002_ADDR, config.REG_STATUS)] = 0x01
    assert LMP91002(bus).wait_ready(timeout_s=0.05) is True


def test_wait_ready_times_out_when_never_ready():
    bus = FakeBus()  # STATUS reads 0x00 forever
    with pytest.raises(TimeoutError):
        LMP91002(bus).wait_ready(timeout_s=0.05, poll_s=0.01)
