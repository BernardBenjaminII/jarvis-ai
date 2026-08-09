#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"

echo
echo "============================================================"
echo "MARK I READINESS AUDIT"
echo "============================================================"
echo

##########################################################################
echo "=========================="
echo "MISSION CONTROL FILES"
echo "=========================="

find core/src/static/mission_control \
    -type f \
    | sort

echo
##########################################################################
echo "=========================="
echo "MISSION CONTROL HTML IDS"
echo "=========================="

grep -RhoE \
'id="[^"]+"' \
core/src/static/mission_control \
| sort | uniq

echo
##########################################################################
echo "=========================="
echo "DATA COMMANDS"
echo "=========================="

grep -RIn \
'data-command=' \
core/src/static/mission_control

echo
##########################################################################
echo "=========================="
echo "DATA VIEWS"
echo "=========================="

grep -RIn \
'data-view=' \
core/src/static/mission_control

echo
##########################################################################
echo "=========================="
echo "OPEN VIEW ACTIONS"
echo "=========================="

grep -RIn \
'data-open-view=' \
core/src/static/mission_control

echo
##########################################################################
echo "=========================="
echo "CLICK HANDLERS"
echo "=========================="

grep -RInE \
'addEventListener|onclick|querySelector|dispatchEvent' \
core/src/static/mission_control

echo
##########################################################################
echo "=========================="
echo "FETCH CALLS"
echo "=========================="

grep -RIn \
'fetch(' \
core/src/static/mission_control

echo
##########################################################################
echo "=========================="
echo "WEBSOCKETS"
echo "=========================="

grep -RInE \
'WebSocket|websocket' \
core/src

echo
##########################################################################
echo "=========================="
echo "API ROUTES"
echo "=========================="

grep -RIn \
'@router\.' \
core/src/routes

echo
##########################################################################
echo "=========================="
echo "CONVERSATION API"
echo "=========================="

grep -RIn \
'conversation' \
core/src/routes \
core/conversation

echo
##########################################################################
echo "=========================="
echo "KNOWLEDGE SEARCH"
echo "=========================="

grep -RInE \
'search_catalog|KnowledgeSearch|knowledge_search|search_for_director' \
core

echo
##########################################################################
echo "=========================="
echo "KNOWLEDGE AWARENESS"
echo "=========================="

grep -RIn \
'ExecutiveKnowledgeAwarenessService' \
core

echo
##########################################################################
echo "=========================="
echo "EXECUTIVE DIRECTOR"
echo "=========================="

grep -RInE \
'KnowledgeHandler|knowledge_retrieval|knowledge_summarization|knowledge_search' \
core/executive

echo
##########################################################################
echo "=========================="
echo "MISSION CONTROL PROJECTIONS"
echo "=========================="

grep -RIn \
'projection' \
core/src/static/mission_control \
core/src/routes \
core/integration

echo
##########################################################################
echo "=========================="
echo "KNOWLEDGE CENTER"
echo "=========================="

grep -RInE \
'knowledge|Knowledge' \
core/src/static/mission_control

echo
##########################################################################
echo "=========================="
echo "TODO / PLACEHOLDERS"
echo "=========================="

grep -RInE \
'TODO|FIXME|stub|placeholder|coming soon' \
core/src \
core/executive \
core/conversation

echo
##########################################################################
echo "=========================="
echo "RUNTIME ENTRYPOINTS"
echo "=========================="

grep -RInE \
'ExecutiveDirector|ConversationOrchestrator|ask|query|grounding|reasoning' \
core

echo
##########################################################################
echo
echo "============================================================"
echo "MARK I AUDIT COMPLETE"
echo "============================================================"
