from harnice import icd

ch_type_ids = {
    "adc": 1,
    "excite": 2
}

signal_to_contact = {
    "excite_pos": 1,
    "excite_neg": 2,
    "adc_1a": 3,
    "adc_1b": 4,
    "adc_2a": 5,
    "adc_2b": 6,
    "shield": 7
}

icd.new_icd()

for connector_number in range(1, 6):  # J1..J5
    connector_name = f"J{connector_number}"
    for input_ch in ["adc", "excite"]:
        channel_name = f"ch{connector_number}.{input_ch}"
        for signal in icd.signals_of_channel_type(input_ch, ch_type_ids):
            icd.write_signal(
                channel=channel_name,
                signal=signal,
                connector=connector_name,
                connector_mpn="DB9_F",
                contact=signal_to_contact.get(signal)
            )