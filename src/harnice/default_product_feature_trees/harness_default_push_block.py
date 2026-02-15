def default_push_block():
    return """
# ensure the system that this harness was built from contains the complete updated instances list
post_harness_instances_list.push(
    system_base_directory,
    (system_pn, system_rev),
)
"""