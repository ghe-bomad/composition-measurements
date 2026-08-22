import json
import time
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent

STATUS_PATH = (
    PROJECT_DIR
    / "system_logs"
    / "status.json"
)

UPS_STATUS_PATH = (
    PROJECT_DIR
    / "system_logs"
    / "ups_status.json"
)

UPS_HISTORY_PATH = (
    PROJECT_DIR
    / "system_logs"
    / "ups_history.json"
)

SYSTEM_EVENT_LOG_PATH = (
    PROJECT_DIR
    / "system_logs"
    / "system_events.csv"
)

SYSTEM_STATE_PATH = (
    PROJECT_DIR
    / "system_logs"
    / "system_state.json"
)

DATA_DIR = (
    PROJECT_DIR
    / "data"
)

import pandas as pd
import streamlit as st

from settings.config_storage import (
    load_config,
    save_config,
    reset_config_to_defaults,
)

from services.service_controller import (
    is_service_active,
    start_service,
    stop_service,
)



TOP_CARD_HEIGHT = 750


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Drager X-am 8000 Valve Monitor",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# CSS
# =========================================================

st.markdown(
    """
    <style>

    /* -----------------------------------------------------
       STREAMLIT UI
    ----------------------------------------------------- */

    header[data-testid="stHeader"] {
        height: 0rem !important;
        background: transparent !important;
    }

    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"] {
        display: none !important;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }


    /* -----------------------------------------------------
       PAGE
    ----------------------------------------------------- */

    .stApp {
        background:
            radial-gradient(
                circle at 85% 5%,
                #102743 0%,
                #071526 32%,
                #040c17 75%
            );

        color: #f5f8fc;
    }

    .block-container {
        max-width: 1500px;

        padding-top: 1.4rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }


    /* -----------------------------------------------------
       TITLES
    ----------------------------------------------------- */

    .page-title {
        font-size: 2.25rem;
        font-weight: 800;

        color: #f7f9fc;

        margin: 0;

        line-height: 1.15;
    }

    .page-subtitle {
        color: #8296ab;

        font-size: 0.9rem;

        margin-top: 0.3rem;
        margin-bottom: 1.2rem;
    }

    .section-title {
        color: #56aaff;

        font-size: 0.92rem;
        font-weight: 800;

        letter-spacing: 0.08em;

        margin: 0;
    }


    /* -----------------------------------------------------
       TABS
    ----------------------------------------------------- */

    button[data-baseweb="tab"] {
        font-size: 0.95rem !important;

        font-weight: 700 !important;

        color: #8fa4b8 !important;

        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
    }

    button[data-baseweb="tab"][aria-selected="true"] {
        color: #56aaff !important;
    }

    [data-baseweb="tab-highlight"] {
        background-color: #56aaff !important;
    }

    [data-baseweb="tab-border"] {
        background-color: #24445f !important;
    }


    /* -----------------------------------------------------
       MAIN CARDS
    ----------------------------------------------------- */

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background:
            linear-gradient(
                145deg,
                #102943 0%,
                #0b2138 100%
            ) !important;

        border:
            1px solid
            #234260 !important;

        border-radius:
            16px !important;

        box-shadow:
            0 10px 26px
            rgba(
                0,
                0,
                0,
                0.18
            ) !important;
    }


    /* -----------------------------------------------------
       METRICS
    ----------------------------------------------------- */

    [data-testid="stMetric"] {
        background:
            #153451 !important;

        border:
            1px solid
            #284b6c !important;

        border-radius:
            12px !important;

        padding:
            0.8rem 1rem !important;
    }

    [data-testid="stMetricLabel"] {
        color:
            #8fa3b7 !important;
    }

    [data-testid="stMetricValue"] {
        color:
            #f6f9fd !important;
    }


    /* -----------------------------------------------------
       BUTTONS
    ----------------------------------------------------- */

    .stButton button {
        min-height:
            46px !important;

        border-radius:
            9px !important;

        font-weight:
            750 !important;

        background:
            #15324e !important;

        color:
            #f5f8fc !important;

        border:
            1px solid
            #315778 !important;

        box-shadow:
            none !important;
    }

    .stButton button:hover {
        background:
            #1b4163 !important;

        border-color:
            #4c9bea !important;
    }

    .stButton button:disabled {
        opacity:
            0.55 !important;

        color:
            #8496a7 !important;
    }


    /* -----------------------------------------------------
       NUMBER INPUTS
    ----------------------------------------------------- */

    [data-testid="stNumberInput"] input {
        background:
            #0c2238 !important;

        color:
            #f4f8fc !important;

        -webkit-text-fill-color:
            #f4f8fc !important;

        height:
            38px !important;

        min-height:
            38px !important;

        border:
            none !important;

        box-shadow:
            none !important;
    }

    [data-testid="stNumberInput"] button {
        background:
            #143754 !important;

        color:
            #f4f8fc !important;

        height:
            38px !important;

        min-height:
            38px !important;

        border:
            none !important;

        box-shadow:
            none !important;
    }

    [data-testid="stNumberInput"] input:disabled {
        background:
            #15212c !important;

        color:
            #697b8d !important;

        -webkit-text-fill-color:
            #697b8d !important;
    }


    /* -----------------------------------------------------
       SELECTS
    ----------------------------------------------------- */

    [data-baseweb="select"] > div {
        background:
            #0c2238 !important;

        color:
            #f4f8fc !important;

        border:
            1px solid
            #294e6c !important;

        border-radius:
            8px !important;
    }

    [data-baseweb="select"] * {
        color:
            #f4f8fc !important;
    }

    [data-baseweb="tag"] {
        background:
            #1f5c94 !important;

        color:
            white !important;
    }


    /* -----------------------------------------------------
       FORMS
    ----------------------------------------------------- */

    [data-testid="stForm"] {
        border:
            none !important;

        padding:
            0 !important;
    }


    /* -----------------------------------------------------
       SETTINGS
    ----------------------------------------------------- */

    .setting-row-label {
        display: flex;

        align-items: center;

        height: 38px;

        color: #dce6f1;

        font-size: 0.90rem;
        font-weight: 600;
    }

    .info-icon {
        position: relative;

        display:
            inline-flex;

        justify-content:
            center;

        align-items:
            center;

        width: 17px;
        height: 17px;

        margin-left: 8px;

        border-radius: 50%;

        border:
            1px solid
            #5687ae;

        color:
            #78b9eb;

        font-size: 11px;
        font-weight: 800;

        cursor: help;
    }

    .info-icon:hover::after {
        content:
            attr(data-tooltip);

        position:
            absolute;

        left: 24px;
        top: -8px;

        z-index: 99999;

        width: 235px;

        padding:
            9px 11px;

        border-radius:
            8px;

        background:
            #071522;

        border:
            1px solid
            #315675;

        color:
            #e7eef6;

        font-size:
            12px;

        font-weight:
            400;

        line-height:
            1.4;

        box-shadow:
            0 8px 25px
            rgba(0, 0, 0, 0.35);

        white-space:
            normal;
    }

    .settings-locked {
        background:
            #131f2a;

        border:
            1px solid
            #344758;

        color:
            #9aabba;

        padding:
            10px 13px;

        margin-top:
            12px;

        margin-bottom:
            14px;

        border-radius:
            8px;

        font-size:
            0.82rem;
    }


    /* -----------------------------------------------------
       LIVE DATA
    ----------------------------------------------------- */

    .gas-card {
        background:
            linear-gradient(
                145deg,
                #183a59 0%,
                #12304d 100%
            );

        border:
            1px solid
            #2b5577;

        border-radius:
            14px;

        padding:
            1.15rem 1.25rem;

        min-height:
            112px;

        box-shadow:
            0 6px 18px
            rgba(0, 0, 0, 0.16);
    }

    .gas-name {
        font-size:
            1rem;

        color:
            #f4f8fc;

        font-weight:
            750;
    }

    .gas-unit {
        font-size:
            0.75rem;

        color:
            #8fa4b8;

        margin-left:
            0.35rem;
    }

    .gas-value {
        color:
            #59aaff;

        font-size:
            1.8rem;

        font-weight:
            800;

        margin-top:
            0.9rem;
    }

    .live-valve-box {
        background:
            #153451;

        border:
            1px solid
            #2a506f;

        border-radius:
            10px;

        padding:
            0.75rem 1rem;

        color:
            #f4f8fc;

        text-align:
            center;

        font-weight:
            700;

        font-size:
            1rem;
    }

    .live-spacing {
        height:
            22px;
    }


    /* -----------------------------------------------------
       STATUS COLORS
    ----------------------------------------------------- */

    .running-status {
        color:
            #38d07d;

        font-size:
            1.05rem;

        font-weight:
            800;
    }

    .stopped-status {
        color:
            #91a4b7;

        font-size:
            1.05rem;

        font-weight:
            800;
    }

    .error-status {
        color:
            #ff6470;

        font-size:
            1.05rem;

        font-weight:
            800;
    }


    /* -----------------------------------------------------
       UPS / SYSTEM TAB
    ----------------------------------------------------- */

    .status-card {
        background:
            linear-gradient(
                145deg,
                #183a59 0%,
                #12304d 100%
            );

        border:
            1px solid
            #2b5577;

        border-radius:
            14px;

        padding:
            1.2rem 1.3rem;
    }

    .status-card-title {
        color:
            #8fa4b8;

        font-size:
            0.78rem;

        margin-bottom:
            0.4rem;
    }

    .status-card-value {
        color:
            #f4f8fc;

        font-size:
            1.2rem;

        font-weight:
            750;
    }


    /* -----------------------------------------------------
       DOWNLOAD
    ----------------------------------------------------- */

    [data-testid="stDownloadButton"] button {
        background:
            #112e4b !important;

        border:
            1px solid
            #315a7f !important;

        color:
            #54a8ff !important;

        min-height:
            44px !important;

        border-radius:
            9px !important;

        font-weight:
            750 !important;
    }


    /* -----------------------------------------------------
       DATAFRAME
    ----------------------------------------------------- */

    [data-testid="stDataFrame"] {
        border-radius:
            10px !important;

        overflow:
            hidden !important;
    }


    hr {
        border-color:
            #29445e !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# GENERIC JSON HELPER
# =========================================================

def load_json_file(
    path,
    default,
):
    if not path.exists():
        return default

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(
                file
            )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return default


# =========================================================
# STATUS
# =========================================================

def load_status():
    return load_json_file(
        STATUS_PATH,
        {
            "running": False,
            "mode": "idle",
            "current_valve": None,
            "cycle": 0,
            "pump": False,
            "message": "System is ready.",
            "measurements": [],
            "mzuzu": None,
            "last_measurement_time": None,
            "last_update": "-",
        },
    )


def format_mode(mode):
    modes = {
        "idle": "Ready",
        "starting": "Starting",
        "pump_start_delay": "Pump starting",
        "measurement": "Measuring",
        "flush": "Flushing",
        "cycle_pause": "Cycle pause",
        "stopping": "Stopping",
        "error": "Error",
    }

    return modes.get(
        mode,
        mode,
    )


# =========================================================
# UPS
# =========================================================

def load_ups_status():
    return load_json_file(
        UPS_STATUS_PATH,
        {
            "battery_percent": None,
            "battery_voltage": None,
            "warning": False,
            "shutdown_pending": False,
            "message": (
                "UPS monitor has not reported yet."
            ),
            "last_update": "-",
        },
    )


def load_ups_history():
    return load_json_file(
        UPS_HISTORY_PATH,
        {
            "last_shutdown": None,
        },
    )


# =========================================================
# SYSTEM EVENTS
# =========================================================

def load_system_events():
    if not SYSTEM_EVENT_LOG_PATH.exists():
        return pd.DataFrame(
            columns=[
                "Timestamp",
                "Event",
                "Details",
            ]
        )

    try:
        dataframe = pd.read_csv(
            SYSTEM_EVENT_LOG_PATH
        )

        if (
            "Timestamp"
            in dataframe.columns
        ):
            dataframe[
                "Timestamp"
            ] = pd.to_datetime(
                dataframe[
                    "Timestamp"
                ],
                errors="coerce",
            )

        return dataframe

    except Exception:
        return pd.DataFrame(
            columns=[
                "Timestamp",
                "Event",
                "Details",
            ]
        )


def load_system_state():
    return load_json_file(
        SYSTEM_STATE_PATH,
        {},
    )


# =========================================================
# CSV
# =========================================================

def get_all_csv_files():
    if not DATA_DIR.exists():
        return []

    return sorted(
        DATA_DIR.rglob(
            "*.csv"
        ),
        key=lambda file:
            file.stat().st_mtime,
    )


def get_latest_csv():
    files = get_all_csv_files()

    if not files:
        return None

    return files[-1]


def load_all_measurements():
    files = get_all_csv_files()

    dataframes = []

    for csv_file in files:
        try:
            dataframe = pd.read_csv(
                csv_file
            )

            if dataframe.empty:
                continue

            dataframe = dataframe.rename(
                columns={
                    "Co2": "CO2",
                    "Co": "CO",
                }
            )

            if (
                "Timestamp"
                not in dataframe.columns
            ):
                continue

            dataframe[
                "Timestamp"
            ] = pd.to_datetime(
                dataframe[
                    "Timestamp"
                ],
                errors="coerce",
            )

            dataframe = dataframe.dropna(
                subset=[
                    "Timestamp"
                ]
            )

            dataframe[
                "_source_file"
            ] = str(
                csv_file.relative_to(
                    DATA_DIR
                )
            )

            dataframes.append(
                dataframe
            )

        except Exception:
            continue

    if not dataframes:
        return pd.DataFrame()

    combined = pd.concat(
        dataframes,
        ignore_index=True,
    )

    return combined.sort_values(
        "Timestamp"
    )


def filter_measurements(
    dataframe,
    selection,
    start_date=None,
    end_date=None,
):
    if dataframe.empty:
        return dataframe

    now = pd.Timestamp.now()

    if selection == "All recorded data":
        return dataframe

    if selection == "Last 24 hours":
        return dataframe[
            dataframe["Timestamp"]
            >= (
                now
                - pd.Timedelta(
                    hours=24
                )
            )
        ]

    if selection == "Last 7 days":
        return dataframe[
            dataframe["Timestamp"]
            >= (
                now
                - pd.Timedelta(
                    days=7
                )
            )
        ]

    if selection == "Last 30 days":
        return dataframe[
            dataframe["Timestamp"]
            >= (
                now
                - pd.Timedelta(
                    days=30
                )
            )
        ]

    if (
        selection == "Custom date range"
        and start_date is not None
        and end_date is not None
    ):
        start_time = pd.Timestamp(
            start_date
        )

        end_time = (
            pd.Timestamp(
                end_date
            )
            + pd.Timedelta(
                days=1
            )
        )

        return dataframe[
            (
                dataframe[
                    "Timestamp"
                ]
                >= start_time
            )
            &
            (
                dataframe[
                    "Timestamp"
                ]
                < end_time
            )
        ]

    return dataframe


def dataframe_to_csv_bytes(
    dataframe
):
    output = dataframe.copy()

    if (
        "_source_file"
        in output.columns
    ):
        output = output.drop(
            columns=[
                "_source_file"
            ]
        )

    if (
        "Timestamp"
        in output.columns
    ):
        output[
            "Timestamp"
        ] = (
            output[
                "Timestamp"
            ]
            .dt.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

    return output.to_csv(
        index=False
    ).encode(
        "utf-8"
    )


# =========================================================
# LIVE VALUES
# =========================================================

def drager_value(
    status,
    gas,
):
    for measurement in (
        status.get(
            "measurements",
            []
        )
    ):
        if (
            measurement.get(
                "gas"
            )
            == gas
        ):
            value = measurement.get(
                "value"
            )

            if value is None:
                return "-"

            if isinstance(
                value,
                float,
            ):
                return (
                    f"{value:.3f}"
                    .rstrip("0")
                    .rstrip(".")
                )

            return str(
                value
            )

    return "-"


def format_number(
    value,
    decimals=2,
):
    if value is None:
        return "-"

    try:
        return (
            f"{float(value):.{decimals}f}"
            .rstrip("0")
            .rstrip(".")
        )

    except (
        TypeError,
        ValueError,
    ):
        return "-"


# =========================================================
# SETTINGS LABEL
# =========================================================

def setting_label(
    text,
    tooltip,
):
    st.markdown(
        (
            '<div '
            'class="setting-row-label">'
            f'{text}'
            '<span '
            'class="info-icon" '
            f'data-tooltip="{tooltip}">'
            'i'
            '</span>'
            '</div>'
        ),
        unsafe_allow_html=True,
    )


# =========================================================
# HEADER
# =========================================================

st.markdown(
    """
    <div class="page-title">
        Drager X-am 8000 Valve Monitor
    </div>

    <div class="page-subtitle">
        Remote gas monitoring and valve control system
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# TOP TABS
# =========================================================

measurement_tab, system_tab = st.tabs(
    [
        "Measurement System",
        "Battery & System Status",
    ]
)


# =========================================================
# TAB 1: MEASUREMENT SYSTEM
# =========================================================

with measurement_tab:

    left_column, right_column = st.columns(
        [0.31, 0.69],
        gap="large",
    )


    # =====================================================
    # LEFT SIDE
    # =====================================================

    with left_column:

        # =================================================
        # SYSTEM CONTROL
        # =================================================

        @st.fragment(
            run_every="2s"
        )
        def system_control():

            service_active = (
                is_service_active()
            )

            status = load_status()


            # -----------------------------------------
            # DYNAMIC START / STOP COLOR
            # -----------------------------------------

            if service_active:
                primary_css = """
                <style>

                .stButton
                button[kind="primary"] {

                    background:
                        linear-gradient(
                            135deg,
                            #a92732,
                            #d43a47
                        ) !important;

                    border:
                        1px solid
                        #f05b66 !important;

                    color:
                        white !important;
                }

                </style>
                """

            else:
                primary_css = """
                <style>

                .stButton
                button[kind="primary"] {

                    background:
                        linear-gradient(
                            135deg,
                            #16874d,
                            #27a963
                        ) !important;

                    border:
                        1px solid
                        #38c97e !important;

                    color:
                        white !important;
                }

                </style>
                """

            st.markdown(
                primary_css,
                unsafe_allow_html=True,
            )


            # -----------------------------------------
            # CARD
            # -----------------------------------------

            with st.container(
                border=True,
                height=TOP_CARD_HEIGHT,
            ):

                st.markdown(
                    '<div '
                    'class="section-title">'
                    'SYSTEM CONTROL'
                    '</div>',
                    unsafe_allow_html=True,
                )

                st.write("")


                start_col, stop_col = (
                    st.columns(2)
                )


                with start_col:
                    start_clicked = (
                        st.button(
                            "START",
                            type=(
                                "secondary"
                                if service_active
                                else "primary"
                            ),
                            disabled=(
                                service_active
                            ),
                            width="stretch",
                            key="system_start",
                        )
                    )


                with stop_col:
                    stop_clicked = (
                        st.button(
                            "STOP",
                            type=(
                                "primary"
                                if service_active
                                else "secondary"
                            ),
                            disabled=(
                                not
                                service_active
                            ),
                            width="stretch",
                            key="system_stop",
                        )
                    )


                if start_clicked:
                    result = start_service()

                    if result["success"]:
                        time.sleep(
                            0.5
                        )

                        st.rerun(
                            scope="fragment"
                        )

                    else:
                        st.error(
                            result["error"]
                            or
                            "Could not start system."
                        )


                if stop_clicked:
                    result = stop_service()

                    if result["success"]:
                        time.sleep(
                            0.5
                        )

                        st.rerun(
                            scope="fragment"
                        )

                    else:
                        st.error(
                            result["error"]
                            or
                            "Could not stop system."
                        )


                st.divider()


                mode = status.get(
                    "mode",
                    "idle",
                )


                if mode == "error":
                    st.markdown(
                        '<div '
                        'class="error-status">'
                        'Error'
                        '</div>',
                        unsafe_allow_html=True,
                    )

                elif service_active:
                    st.markdown(
                        f'<div '
                        f'class="running-status">'
                        f'{format_mode(mode)}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                else:
                    st.markdown(
                        '<div '
                        'class="stopped-status">'
                        'Stopped'
                        '</div>',
                        unsafe_allow_html=True,
                    )


                current_valve = (
                    status.get(
                        "current_valve"
                    )
                )

                if current_valve is None:
                    current_valve = "-"


                valve_col, pump_col, cycle_col = (
                    st.columns(3)
                )


                with valve_col:
                    st.metric(
                        "Valve",
                        current_valve,
                    )


                with pump_col:
                    st.metric(
                        "Pump",
                        (
                            "ON"
                            if status.get(
                                "pump"
                            )
                            else "OFF"
                        ),
                    )


                with cycle_col:
                    st.metric(
                        "Cycle",
                        status.get(
                            "cycle",
                            0,
                        ),
                    )


                st.markdown(
                    "**Current status**"
                )


                st.write(
                    status.get(
                        "message",
                        "No status available.",
                    )
                )


                st.caption(
                    "Last update: "
                    f"{status.get('last_update', '-')}"
                )


        system_control()


        # =================================================
        # SETTINGS
        # =================================================

        @st.fragment(
            run_every="2s"
        )
        def settings_panel():

            service_active = (
                is_service_active()
            )

            config = load_config()


            with st.container(
                border=True
            ):

                title_col, reset_col = (
                    st.columns(
                        [0.68, 0.32],
                        vertical_alignment=
                            "center",
                    )
                )


                with title_col:
                    st.markdown(
                        '<div '
                        'class="section-title">'
                        'MEASUREMENT SETTINGS'
                        '</div>',
                        unsafe_allow_html=True,
                    )


                with reset_col:
                    reset_clicked = (
                        st.button(
                            "RESTORE DEFAULTS",
                            disabled=(
                                service_active
                            ),
                            width="content",
                            key=(
                                "reset_default_settings"
                            ),
                            help=(
                                "Restore all measurement "
                                "settings to the values "
                                "defined in "
                                "default_config.json."
                            ),
                        )
                    )


                if reset_clicked:
                    reset_config_to_defaults()

                    time.sleep(
                        0.3
                    )

                    st.rerun(
                        scope="fragment"
                    )


                if service_active:
                    st.markdown(
                        '<div '
                        'class="settings-locked">'
                        'Settings cannot be changed '
                        'during an active '
                        'measurement cycle.'
                        '</div>',
                        unsafe_allow_html=True,
                    )


                available_valves = [
                    1,
                    2,
                    3,
                    4,
                    5,
                    6,
                ]


                with st.form(
                    "measurement_settings",
                    border=False,
                ):

                    settings = [
                        (
                            "Measurement time",
                            (
                                "How long each measurement "
                                "valve remains active while "
                                "sensor values are recorded."
                            ),
                            "measurement_duration_seconds",
                            10.0,
                            1.0,
                            3600.0,
                            1.0,
                        ),

                        (
                            "Flush time (Valve 6)",
                            (
                                "How long Valve 6 remains "
                                "open to flush the gas path "
                                "with fresh air."
                            ),
                            "flush_seconds",
                            10.0,
                            0.0,
                            3600.0,
                            1.0,
                        ),

                        (
                            "Measurement interval",
                            (
                                "Time between two sensor "
                                "readings while a valve "
                                "is active."
                            ),
                            "measurement_interval_seconds",
                            2.0,
                            0.1,
                            3600.0,
                            0.5,
                        ),

                        (
                            "Pause between cycles",
                            (
                                "Optional waiting time "
                                "after one complete cycle "
                                "before the next cycle starts."
                            ),
                            "cycle_pause_seconds",
                            0.0,
                            0.0,
                            3600.0,
                            1.0,
                        ),

                        (
                            "Pump startup delay",
                            (
                                "Waiting time after the "
                                "Drager pump is switched on "
                                "before the first valve opens."
                            ),
                            "pump_start_delay_seconds",
                            2.0,
                            0.0,
                            300.0,
                            1.0,
                        ),
                    ]


                    input_values = {}


                    for (
                        label,
                        tooltip,
                        key_name,
                        default,
                        minimum,
                        maximum,
                        step,
                    ) in settings:

                        label_col, input_col = (
                            st.columns(
                                [1.55, 1.0],
                                vertical_alignment=
                                    "center",
                            )
                        )


                        with label_col:
                            setting_label(
                                label,
                                tooltip,
                            )


                        with input_col:
                            input_values[
                                key_name
                            ] = st.number_input(
                                label,
                                min_value=minimum,
                                max_value=maximum,
                                value=float(
                                    config.get(
                                        key_name,
                                        default,
                                    )
                                ),
                                step=step,
                                disabled=(
                                    service_active
                                ),
                                label_visibility=
                                    "collapsed",
                                width="stretch",
                            )


                    # ---------------------------------
                    # PUMP FLOW
                    # ---------------------------------

                    label_col, input_col = (
                        st.columns(
                            [1.55, 1.0],
                            vertical_alignment=
                                "center",
                        )
                    )


                    with label_col:
                        setting_label(
                            "Pump flow",
                            (
                                "Requested Drager pump "
                                "flow rate in millilitres "
                                "per minute."
                            ),
                        )


                    with input_col:
                        pump_flow = (
                            st.number_input(
                                "Pump flow",
                                min_value=0,
                                max_value=1000,
                                value=int(
                                    config.get(
                                        "pump_flow",
                                        350,
                                    )
                                ),
                                step=10,
                                disabled=(
                                    service_active
                                ),
                                label_visibility=
                                    "collapsed",
                                width="stretch",
                            )
                        )


                    # ---------------------------------
                    # ADVANCED
                    # ---------------------------------

                    with st.expander(
                        "Advanced settings"
                    ):

                        measurement_valves = (
                            st.multiselect(
                                "Measurement valves",
                                options=(
                                    available_valves
                                ),
                                default=config.get(
                                    "measurement_valves",
                                    [
                                        1,
                                        2,
                                        3,
                                        4,
                                        5,
                                    ],
                                ),
                                disabled=(
                                    service_active
                                ),
                            )
                        )


                        flush_valve = (
                            st.selectbox(
                                "Flush valve",
                                options=(
                                    available_valves
                                ),
                                index=(
                                    available_valves
                                    .index(
                                        int(
                                            config.get(
                                                "flush_valve",
                                                6,
                                            )
                                        )
                                    )
                                ),
                                disabled=(
                                    service_active
                                ),
                            )
                        )


                        continuous_mode = (
                            st.checkbox(
                                "Continuous measuring",
                                value=bool(
                                    config.get(
                                        "continuous_mode",
                                        True,
                                    )
                                ),
                                disabled=(
                                    service_active
                                ),
                            )
                        )


                    save_clicked = (
                        st.form_submit_button(
                            "SAVE SETTINGS",
                            width="stretch",
                            disabled=(
                                service_active
                            ),
                        )
                    )


                if save_clicked:

                    measurement_duration = (
                        input_values[
                            "measurement_duration_seconds"
                        ]
                    )

                    measurement_interval = (
                        input_values[
                            "measurement_interval_seconds"
                        ]
                    )


                    if not measurement_valves:
                        st.error(
                            "Select at least one "
                            "measurement valve."
                        )


                    elif (
                        flush_valve
                        in measurement_valves
                    ):
                        st.error(
                            "Flush valve cannot also "
                            "be a measurement valve."
                        )


                    elif (
                        measurement_interval
                        > measurement_duration
                    ):
                        st.error(
                            "Measurement interval cannot "
                            "be longer than measurement "
                            "time."
                        )


                    else:
                        new_config = {
                            "measurement_valves":
                                sorted(
                                    int(v)
                                    for v
                                    in measurement_valves
                                ),

                            "flush_valve":
                                int(
                                    flush_valve
                                ),

                            "pump_start_delay_seconds":
                                float(
                                    input_values[
                                        "pump_start_delay_seconds"
                                    ]
                                ),

                            "flush_seconds":
                                float(
                                    input_values[
                                        "flush_seconds"
                                    ]
                                ),

                            "measurement_duration_seconds":
                                float(
                                    measurement_duration
                                ),

                            "measurement_interval_seconds":
                                float(
                                    measurement_interval
                                ),

                            "cycle_pause_seconds":
                                float(
                                    input_values[
                                        "cycle_pause_seconds"
                                    ]
                                ),

                            "continuous_mode":
                                bool(
                                    continuous_mode
                                ),

                            "pump_flow":
                                int(
                                    pump_flow
                                ),
                        }


                        save_config(
                            new_config
                        )


                        st.success(
                            "Settings saved."
                        )


        settings_panel()


    # =====================================================
    # RIGHT SIDE
    # =====================================================

    with right_column:

        # =================================================
        # LIVE DATA
        # =================================================

        @st.fragment(
            run_every="2s"
        )
        def live_data():

            status = load_status()

            current_valve = (
                status.get(
                    "current_valve"
                )
            )

            mzuzu = (
                status.get(
                    "mzuzu"
                )
                or {}
            )


            with st.container(
                border=True,
                height=TOP_CARD_HEIGHT,
            ):

                st.markdown(
                    '<div '
                    'class="section-title">'
                    'LIVE DATA'
                    '</div>',
                    unsafe_allow_html=True,
                )

                st.write("")


                if current_valve is None:
                    valve_text = (
                        "No active valve"
                    )

                else:
                    valve_text = (
                        f"Active Valve: "
                        f"{current_valve}"
                    )


                st.markdown(
                    f'<div '
                    f'class="live-valve-box">'
                    f'{valve_text}'
                    f'</div>',
                    unsafe_allow_html=True,
                )


                st.markdown(
                    '<div '
                    'class="live-spacing">'
                    '</div>',
                    unsafe_allow_html=True,
                )


                cards = [
                    (
                        "CO2",
                        "% vol",
                        drager_value(
                            status,
                            "CO2",
                        ),
                    ),

                    (
                        "CH4",
                        "% vol",
                        drager_value(
                            status,
                            "CH4",
                        ),
                    ),

                    (
                        "O2",
                        "% vol",
                        drager_value(
                            status,
                            "O2",
                        ),
                    ),

                    (
                        "H2S Drager",
                        "ppm",
                        drager_value(
                            status,
                            "H2S",
                        ),
                    ),

                    (
                        "H2S Mzuzu",
                        "ppm",
                        format_number(
                            mzuzu.get(
                                "h2s_ppm"
                            ),
                            2,
                        ),
                    ),

                    (
                        "CO",
                        "ppm",
                        drager_value(
                            status,
                            "CO",
                        ),
                    ),

                    (
                        "NH3",
                        "ppm",
                        drager_value(
                            status,
                            "NH3",
                        ),
                    ),

                    (
                        "Sensor Temp",
                        "C",
                        format_number(
                            mzuzu.get(
                                "temperature_c"
                            ),
                            2,
                        ),
                    ),
                ]


                for start_index in (
                    0,
                    3,
                    6,
                ):

                    row = st.columns(3)

                    row_cards = cards[
                        start_index:
                        start_index + 3
                    ]


                    for column, card in zip(
                        row,
                        row_cards,
                    ):

                        (
                            name,
                            unit,
                            value,
                        ) = card


                        with column:
                            html = (
                                '<div '
                                'class="gas-card">'
                                '<div>'
                                '<span '
                                'class="gas-name">'
                                f'{name}'
                                '</span>'
                                '<span '
                                'class="gas-unit">'
                                f'{unit}'
                                '</span>'
                                '</div>'
                                '<div '
                                'class="gas-value">'
                                f'{value}'
                                '</div>'
                                '</div>'
                            )

                            st.markdown(
                                html,
                                unsafe_allow_html=True,
                            )


                    st.write("")


                st.caption(
                    "Last sensor reading: "
                    f"{status.get('last_measurement_time', '-')}"
                )


        live_data()


        # =================================================
        # DOWNLOAD DATA
        # =================================================

        with st.container(
            border=True
        ):

            st.markdown(
                '<div '
                'class="section-title">'
                'DOWNLOAD DATA'
                '</div>',
                unsafe_allow_html=True,
            )


            all_measurements = (
                load_all_measurements()
            )


            if all_measurements.empty:
                st.info(
                    "No recorded measurement "
                    "data available."
                )


            else:

                selection = st.selectbox(
                    "Data range",
                    [
                        "All recorded data",
                        "Last 24 hours",
                        "Last 7 days",
                        "Last 30 days",
                        "Custom date range",
                    ],
                    key="download_range",
                )


                start_date = None
                end_date = None


                if (
                    selection
                    == "Custom date range"
                ):

                    date_col_1, date_col_2 = (
                        st.columns(2)
                    )


                    with date_col_1:
                        start_date = (
                            st.date_input(
                                "From",
                                value=(
                                    pd.Timestamp.now()
                                    - pd.Timedelta(
                                        days=7
                                    )
                                ).date(),
                            )
                        )


                    with date_col_2:
                        end_date = (
                            st.date_input(
                                "To",
                                value=(
                                    pd.Timestamp.now()
                                    .date()
                                ),
                            )
                        )


                selected_data = (
                    filter_measurements(
                        all_measurements,
                        selection,
                        start_date,
                        end_date,
                    )
                )


                st.caption(
                    f"{len(selected_data):,} "
                    "measurement rows selected"
                )


                if selected_data.empty:
                    st.warning(
                        "No measurements available "
                        "for this period."
                    )


                else:

                    source_files = sorted(
                        selected_data[
                            "_source_file"
                        ]
                        .dropna()
                        .unique()
                    )


                    first_measurement = (
                        selected_data[
                            "Timestamp"
                        ].min()
                    )

                    last_measurement = (
                        selected_data[
                            "Timestamp"
                        ].max()
                    )


                    info_col_1, info_col_2 = (
                        st.columns(2)
                    )


                    with info_col_1:
                        st.caption(
                            "First measurement"
                        )

                        st.write(
                            first_measurement
                        )


                    with info_col_2:
                        st.caption(
                            "Last measurement"
                        )

                        st.write(
                            last_measurement
                        )


                    st.caption(
                        f"{len(source_files)} "
                        "CSV source files included"
                    )


                    download_filename = (
                        "gas_measurements_"
                        + pd.Timestamp.now()
                        .strftime(
                            "%Y-%m-%d_%H-%M-%S"
                        )
                        + ".csv"
                    )


                    st.download_button(
                        "DOWNLOAD CONSOLIDATED DATA",
                        data=(
                            dataframe_to_csv_bytes(
                                selected_data
                            )
                        ),
                        file_name=(
                            download_filename
                        ),
                        mime="text/csv",
                        width="stretch",
                    )


                    with st.expander(
                        "Download individual source files"
                    ):

                        for source_file in (
                            source_files
                        ):

                            full_path = (
                                DATA_DIR
                                / source_file
                            )


                            if full_path.exists():

                                st.download_button(
                                    (
                                        "Download "
                                        + full_path.name
                                    ),
                                    data=(
                                        full_path
                                        .read_bytes()
                                    ),
                                    file_name=(
                                        full_path.name
                                    ),
                                    mime="text/csv",
                                    key=(
                                        "download_"
                                        + source_file
                                        .replace(
                                            "/",
                                            "_",
                                        )
                                    ),
                                    width="stretch",
                                )


    # =====================================================
    # BOTTOM BAR
    # =====================================================

    st.write("")


    @st.fragment(
        run_every="2s"
    )
    def bottom_bar():

        status = load_status()

        service_active = (
            is_service_active()
        )

        latest_csv = (
            get_latest_csv()
        )


        with st.container(
            border=True
        ):

            bottom_1, bottom_2, bottom_3 = (
                st.columns(3)
            )


            with bottom_1:

                if service_active:
                    st.markdown(
                        "**System Status:** "
                        ":green[RUNNING]"
                    )

                else:
                    st.markdown(
                        "**System Status:** "
                        "STOPPED"
                    )


            with bottom_2:

                if latest_csv:
                    st.markdown(
                        "**Latest Data File**  \n"
                        f"`{latest_csv.name}`"
                    )

                else:
                    st.markdown(
                        "**Latest Data File**  \n"
                        "No file"
                    )


            with bottom_3:

                st.markdown(
                    "**Last Update**  \n"
                    f"{status.get('last_update', '-')}"
                )


    bottom_bar()


# =========================================================
# TAB 2: BATTERY & SYSTEM STATUS
# =========================================================

with system_tab:

    @st.fragment(
        run_every="2s"
    )
    def battery_and_system_status():

        ups_status = (
            load_ups_status()
        )

        ups_history = (
            load_ups_history()
        )

        system_state = (
            load_system_state()
        )

        events = (
            load_system_events()
        )


        # =================================================
        # BATTERY
        # =================================================

        with st.container(
            border=True
        ):

            st.markdown(
                '<div '
                'class="section-title">'
                'BATTERY STATUS'
                '</div>',
                unsafe_allow_html=True,
            )

            st.write("")


            battery_percent = (
                ups_status.get(
                    "battery_percent"
                )
            )

            battery_voltage = (
                ups_status.get(
                    "battery_voltage"
                )
            )


            battery_col, voltage_col = (
                st.columns(2)
            )


            with battery_col:
                st.metric(
                    "Battery",
                    (
                        f"{battery_percent:.1f} %"
                        if battery_percent
                        is not None
                        else "-"
                    ),
                )


            with voltage_col:
                st.metric(
                    "Battery Voltage",
                    (
                        f"{battery_voltage:.3f} V"
                        if battery_voltage
                        is not None
                        else "-"
                    ),
                )


            if ups_status.get(
                "shutdown_pending",
                False,
            ):
                st.error(
                    "Critical battery level. "
                    "Safe shutdown is in progress."
                )


            elif ups_status.get(
                "warning",
                False,
            ):
                st.warning(
                    "UPS battery level is low."
                )


            else:
                st.success(
                    ups_status.get(
                        "message",
                        "UPS battery status normal.",
                    )
                )


            st.caption(
                "UPS last update: "
                f"{ups_status.get('last_update', '-')}"
            )


        # =================================================
        # SYSTEM STATE
        # =================================================

        st.write("")


        with st.container(
            border=True
        ):

            st.markdown(
                '<div '
                'class="section-title">'
                'SYSTEM STATUS'
                '</div>',
                unsafe_allow_html=True,
            )

            st.write("")


            last_boot = (
                system_state.get(
                    "last_boot",
                    "-"
                )
            )

            last_shutdown = (
                system_state.get(
                    "last_shutdown",
                    "-"
                )
            )

            shutdown_reason = (
                system_state.get(
                    "shutdown_reason",
                    "-"
                )
            )


            state_col_1, state_col_2 = (
                st.columns(2)
            )


            with state_col_1:

                st.markdown(
                    (
                        '<div class="status-card">'
                        '<div '
                        'class="status-card-title">'
                        'Last Boot'
                        '</div>'
                        '<div '
                        'class="status-card-value">'
                        f'{last_boot}'
                        '</div>'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )


            with state_col_2:

                st.markdown(
                    (
                        '<div class="status-card">'
                        '<div '
                        'class="status-card-title">'
                        'Last Shutdown'
                        '</div>'
                        '<div '
                        'class="status-card-value">'
                        f'{last_shutdown}'
                        '</div>'
                        '</div>'
                    ),
                    unsafe_allow_html=True,
                )


            st.write("")


            st.markdown(
                "**Last shutdown reason**"
            )

            st.write(
                shutdown_reason
            )


            last_ups_shutdown = (
                ups_history.get(
                    "last_shutdown"
                )
            )


            if last_ups_shutdown:

                st.divider()

                st.markdown(
                    "**Last UPS-triggered shutdown**"
                )

                ups_col_1, ups_col_2 = (
                    st.columns(2)
                )


                with ups_col_1:
                    st.metric(
                        "Battery",
                        (
                            f"{last_ups_shutdown.get('battery_percent', '-')} %"
                        ),
                    )


                with ups_col_2:
                    st.metric(
                        "Voltage",
                        (
                            f"{last_ups_shutdown.get('battery_voltage', '-')} V"
                        ),
                    )


                st.write(
                    "**Time:** "
                    f"{last_ups_shutdown.get('time', '-')}"
                )

                st.write(
                    "**Reason:** "
                    f"{last_ups_shutdown.get('reason', '-')}"
                )


        # =================================================
        # EVENT LOG
        # =================================================

        st.write("")


        with st.container(
            border=True
        ):

            st.markdown(
                '<div '
                'class="section-title">'
                'SYSTEM EVENT LOG'
                '</div>',
                unsafe_allow_html=True,
            )

            st.write("")


            if events.empty:

                st.info(
                    "No system events "
                    "have been recorded yet."
                )


            else:

                display_events = (
                    events
                    .sort_values(
                        "Timestamp",
                        ascending=False,
                    )
                    .copy()
                )


                if (
                    "Timestamp"
                    in display_events.columns
                ):
                    display_events[
                        "Timestamp"
                    ] = (
                        display_events[
                            "Timestamp"
                        ]
                        .dt.strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )
                    )


                st.dataframe(
                    display_events,
                    hide_index=True,
                    width="stretch",
                )


                st.caption(
                    f"{len(display_events)} "
                    "system events recorded"
                )


                if SYSTEM_EVENT_LOG_PATH.exists():

                    st.download_button(
                        "DOWNLOAD SYSTEM EVENT LOG",
                        data=(
                            SYSTEM_EVENT_LOG_PATH
                            .read_bytes()
                        ),
                        file_name=(
                            "system_events.csv"
                        ),
                        mime="text/csv",
                        width="stretch",
                    )


    battery_and_system_status()
