#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

if [[ $# -lt 2 ]]; then
	echo "Usage: $0 <processing|no_processing> <POSE|DSE|CARD> [exact_encoding] [amo_encoding] [datasets...]" >&2
	exit 2
fi

TO=${TO:-600}
MO=${MO:-14000}
PYTHON_BIN=${PYTHON_BIN:-python3}

mode=$1
encoding=$2
shift 2

exact_encoding=""
amo_encoding=""

if [[ $encoding == "CARD" ]]; then
	if [[ $# -lt 1 ]]; then
		echo "CARD requires at least one encoding id" >&2
		exit 2
	fi
	exact_encoding=$1
	shift
	if [[ $# -gt 0 && $1 =~ ^[0-9]+$ ]]; then
		amo_encoding=$1
		shift
	else
		amo_encoding=$exact_encoding
	fi
fi

case "$mode" in
	processing)
		script_name="main.py"
		;;
	no_processing)
		script_name="main_no_processing.py"
		;;
	*)
		echo "Unknown mode: $mode" >&2
		exit 2
		;;
esac

if [[ $# -gt 0 ]]; then
	DATASETS=("$@")
else
	mapfile -t DATASETS < <(find dataset -mindepth 1 -maxdepth 1 -type d | sort | xargs -n 1 basename)
fi

run_case() {
	local dataset=$1
	local group
	local log_file
	local -a cmd

	case "$encoding" in
		POSE)
			group="POSE"
			cmd=("$PYTHON_BIN" -u "$script_name" "$dataset" POSE)
			;;
		DSE)
			group="DSE"
			cmd=("$PYTHON_BIN" -u "$script_name" "$dataset" DSE)
			;;
		CARD)
			group="CARD_${exact_encoding}_${amo_encoding}"
			cmd=("$PYTHON_BIN" -u "$script_name" "$dataset" CARD "$exact_encoding" "$amo_encoding")
			;;
		*)
			echo "Unknown encoding: $encoding" >&2
			exit 2
			;;
	esac

	log_file="results/${mode}/${group}/${dataset}.log"
	mkdir -p "$(dirname "$log_file")"
	./runlim -r "$TO" -s "$MO" "${cmd[@]}" 2>&1 | tee "$log_file" || true
}

for dataset in "${DATASETS[@]}"; do
	run_case "$dataset"
done
