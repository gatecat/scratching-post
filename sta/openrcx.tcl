read_lef export/StdCellLib.lef
read_def export/corona_cts_export.def
extract_parasitics -ext_model_file ../../open_pdks/sky130/sky130A/libs.tech/openlane/rcx_rules.info
write_verilog export/corona_cts_export.v
write_spef export/corona_cts_export.spef
exit
