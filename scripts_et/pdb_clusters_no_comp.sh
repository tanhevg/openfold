#!/usr/bin/env bash
# process the sequence clusters file from RCSB to remove the computed structures (AlphaFold and ModelArchive)
# https://www.rcsb.org/docs/programmatic-access/file-download-services#sequence-clusters-data
SEQ_ID_PCT=40
FILE_WITH_COMP="clusters-by-entity-${SEQ_ID_PCT}.txt"
FILE_WITHOUT_COMP="clusters-by-entity-${SEQ_ID_PCT}-no-comp.txt"
wget "https://cdn.rcsb.org/resources/sequence/clusters/${FILE_WITH_COMP}"
sed -r 's/\b(AF|MA)_\w+\s?//g' "${FILE_WITH_COMP}" | grep -v '^$' > "${FILE_WITHOUT_COMP}"