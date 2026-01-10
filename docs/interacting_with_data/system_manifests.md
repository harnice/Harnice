# Interacting with System Manifests

A table that relates reference designator to part number(s), and may contain other information indexed to the reference designator

##Commands:
??? info "`manifest.new()`"

    Synchronize the system harness manifest with the system connector list:
      - Remove nets that no longer exist in the connector list
      - Add nets that appear in the connector list but not yet in the manifest
      - Preserve all other column data for nets that still exist

??? info "`manifest.update_upstream()`"

    No documentation provided.

