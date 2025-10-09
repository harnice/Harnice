from harnice import signals_list

ch_type_ids = {"in": 1, "excite": 2, "sense": 1, "chassis": 3}

ch_type_id_lib_repo = "https://github.com/kenyonshutt/harnice-library-public"

signal_to_contact = {
    "in.pos": 1,
    "in.negexcite_neg": 8,
    "adc_1a": 3,
    "adc_1b": 4,
    "adc_2a": 5,
    "adc_2b": 6,
    "shield": 7,
}

signals_list.new_list()

for connector_number in range(1, 7):
    connector_name = f"J{connector_number}"
    for input_ch in ["adc", "excite"]:
        channel_name = f"ch{connector_number}.{input_ch}"
        channel_type_id = ch_type_ids.get(input_ch)
        for signal in signals_list.signals_of_channel_type_id(
            input_ch, channel_type_id, ch_type_id_lib_repo
        ):
            signals_list.write_signal(
                channel=channel_name,
                channel_type_id=channel_type_id,
                compatible_channel_ids=signals_list.compatible_channels(
                    input_ch, ch_type_ids, ch_type_id_lib_repo
                ),
                signal=signal,
                connector_name=connector_name,
                connector_mpn="DB9_F",
                contact=signal_to_contact.get(signal),
            )
