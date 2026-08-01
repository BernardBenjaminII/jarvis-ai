# Genesis VII-A0 — Pack 2

## Executive API and Live Transport

**Status:** Implemented  
**Pack:** 2 of 5  
**Depends on:** Genesis VII-A0 Pack 1

## Purpose

Pack 2 exposes the Executive backend services established by Pack 1 through
stable REST and WebSocket contracts.

It does not modify the current Executive UI.

The browser integration begins in Pack 3.

## REST API

Pack 2 establishes:

GET /operations/executive/dashboard
GET /operations/executive/health
GET /operations/executive/status
GET /operations/executive/metrics
GET /operations/executive/events
GET /operations/executive/live/status
