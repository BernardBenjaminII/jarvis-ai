#!/usr/bin/env bash
#
# legal_library_bootstrap.sh
#
# Bootstrap a foundational legal library using official public sources.
#

set -Eeuo pipefail

ROOT="${HOME}/Downloads/Legal_Studies"

mkdir -p "$ROOT"

download () {
    local url="$1"
    local outfile="$2"

    mkdir -p "$(dirname "$outfile")"

    if [[ -f "$outfile" ]]; then
        echo "[SKIP] $outfile"
        return
    fi

    echo
    echo "Downloading:"
    echo "  $url"

    curl \
        --location \
        --fail \
        --retry 5 \
        --retry-delay 2 \
        --continue-at - \
        --output "$outfile" \
        "$url"
}

########################################################################
# UNITED STATES
########################################################################

US="$ROOT/United_States"

mkdir -p "$US"

download \
"https://www.archives.gov/files/founding-docs/constitution_transcript.pdf" \
"$US/US_Constitution.pdf"

download \
"https://www.archives.gov/files/founding-docs/declaration_transcript.pdf" \
"$US/Declaration_of_Independence.pdf"

########################################################################
# MILITARY LAW
########################################################################

MIL="$ROOT/Military"

mkdir -p "$MIL"

download \
"https://jsc.defense.gov/Portals/99/Documents/MCM2024.pdf" \
"$MIL/Manual_for_Courts-Martial.pdf"

download \
"https://jsc.defense.gov/Portals/99/Documents/UCMJ2024.pdf" \
"$MIL/Uniform_Code_of_Military_Justice.pdf"

########################################################################
# CYBERSECURITY
########################################################################

CYBER="$ROOT/Cybersecurity"

mkdir -p "$CYBER"

download \
"https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf" \
"$CYBER/NIST_AI_RMF.pdf"

download \
"https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-61r3.pdf" \
"$CYBER/NIST_SP800-61r3.pdf"

download \
"https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-53r5.pdf" \
"$CYBER/NIST_SP800-53r5.pdf"

########################################################################
# CISA
########################################################################

CISA="$ROOT/CISA"

mkdir -p "$CISA"

download \
"https://www.cisa.gov/sites/default/files/2023-01/zero_trust_maturity_model_v2_508.pdf" \
"$CISA/Zero_Trust_Maturity_Model_v2.pdf"

########################################################################
# PRIVACY
########################################################################

PRIV="$ROOT/Privacy"

mkdir -p "$PRIV"

download \
"https://eur-lex.europa.eu/eli/reg/2016/679/oj" \
"$PRIV/GDPR.html"

########################################################################
# UNITED NATIONS
########################################################################

UN="$ROOT/United_Nations"

mkdir -p "$UN"

download \
"https://www.un.org/en/about-us/un-charter/full-text" \
"$UN/UN_Charter.html"

download \
"https://www.ohchr.org/sites/default/files/UDHR/Documents/UDHR_Translations/eng.pdf" \
"$UN/Universal_Declaration_of_Human_Rights.pdf"

########################################################################
# GENEVA CONVENTIONS
########################################################################

GENEVA="$ROOT/Geneva"

mkdir -p "$GENEVA"

download \
"https://ihl-databases.icrc.org/assets/treaties/380-GC-I-EN.pdf" \
"$GENEVA/Geneva_Convention_I.pdf"

########################################################################
# NATO
########################################################################

NATO="$ROOT/NATO"

mkdir -p "$NATO"

########################################################################
# AVIATION
########################################################################

FAA="$ROOT/Aviation"

mkdir -p "$FAA"

########################################################################
# PLACEHOLDERS
########################################################################

mkdir -p "$ROOT/Federal_Register"
mkdir -p "$ROOT/US_Code"
mkdir -p "$ROOT/CFR"
mkdir -p "$ROOT/Supreme_Court"
mkdir -p "$ROOT/DOJ"
mkdir -p "$ROOT/FBI"
mkdir -p "$ROOT/CIA"
mkdir -p "$ROOT/NSA"
mkdir -p "$ROOT/ODNI"
mkdir -p "$ROOT/ICC"
mkdir -p "$ROOT/ICJ"

########################################################################

echo
echo "==============================================="
echo "Initial Legal Library Created"
echo "==============================================="
echo
echo "Location:"
echo "    $ROOT"
echo
echo "Next recommendation:"
echo "    Build provider modules for:"
echo
echo "      • U.S. Code"
echo "      • Code of Federal Regulations"
echo "      • Federal Register"
echo "      • Supreme Court Opinions"
echo "      • DOJ manuals"
echo "      • CIA Reading Room"
echo "      • ODNI publications"
echo "      • NATO doctrine"
echo
