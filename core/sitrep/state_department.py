"""Official State Department travel-advisory ArcGIS provider."""
from __future__ import annotations
import json, os
from datetime import datetime, timezone
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

DEFAULT_LAYER_URL = "https://services6.arcgis.com/R6wlO6UHmSzqm9Vs/arcgis/rest/services/Travel_Advisory_Levels__(2024)_View_Layer/FeatureServer/54"
LEVEL_TEXT = {1:"Exercise normal precautions",2:"Exercise increased caution",3:"Reconsider travel",4:"Do not travel"}
SEVERITY = {1:"info",2:"watch",3:"high",4:"critical"}

def _utc_now(): return datetime.now(timezone.utc)
def _epoch_ms(value):
    if not isinstance(value, (int,float)): return None
    try: return datetime.fromtimestamp(value/1000, tz=timezone.utc).isoformat()
    except (ValueError, OverflowError, OSError): return None
def _trusted_advisory_url(value):
    try:
        parsed=urlparse(str(value)); return parsed.scheme=="https" and parsed.hostname=="travel.state.gov" and "/traveladvisories/" in parsed.path
    except ValueError: return False

class StateDepartmentTravelAdvisoryProvider:
    provider_id="us_state_travel_advisories"
    publisher="U.S. Department of State"
    def __init__(self, *, layer_url=None, timeout_seconds=15.0, opener=urlopen, clock=_utc_now):
        self.layer_url=layer_url or os.getenv("JARVIS_SITREP_STATE_ARCGIS_URL", DEFAULT_LAYER_URL)
        self.timeout_seconds,self._opener,self._clock=timeout_seconds,opener,clock
    def collect(self):
        parameters=urlencode({"f":"json","where":"NAME IS NOT NULL AND LEVEL_ IS NOT NULL","outFields":"OBJECTID,NAME,LEVEL_,URL,ADVDATE,ISO_3,GlobalID,EditDate,AD_OD_Status,AD_OD_Text,AD_OD_Date","returnGeometry":"false","returnCentroid":"true","outSR":"4326","orderByFields":"ADVDATE DESC","resultRecordCount":"2000"})
        endpoint=f"{self.layer_url}/query?{parameters}"
        request=Request(endpoint,headers={"Accept":"application/json","User-Agent":"JARVIS-SITREP/2.0 (+local read-only collector)"})
        with self._opener(request,timeout=self.timeout_seconds) as response: payload=json.loads(response.read().decode("utf-8"))
        return self.parse(payload)
    def parse(self,payload):
        if not isinstance(payload,dict): raise ValueError("ArcGIS response is not an object")
        if payload.get("error"): raise ValueError(f"ArcGIS query failed: {payload['error']}")
        features=payload.get("features")
        if not isinstance(features,list) or not features: raise ValueError("State Department layer contained no features")
        retrieved_at=self._clock().astimezone(timezone.utc).isoformat(); incidents=[]
        for feature in features:
            attributes=feature.get("attributes") or {}; name=str(attributes.get("NAME") or "").strip(); url=str(attributes.get("URL") or "").strip()
            try: level=int(attributes.get("LEVEL_"))
            except (TypeError,ValueError): continue
            if not name or level not in LEVEL_TEXT or not _trusted_advisory_url(url): continue
            centroid=feature.get("centroid") or {}; latitude=centroid.get("y"); longitude=centroid.get("x")
            location={"latitude":latitude,"longitude":longitude} if isinstance(latitude,(int,float)) and isinstance(longitude,(int,float)) else None
            departure=str(attributes.get("AD_OD_Text") or "").strip()
            summary=f"Level {level}: {LEVEL_TEXT[level]}." + (f" {departure}" if departure else "")
            identity=str(attributes.get("GlobalID") or attributes.get("OBJECTID") or attributes.get("ISO_3") or name).strip("{}")
            incidents.append({"id":f"state-{identity}","kind":"travel_advisory","operational_state":"LIVE","severity":SEVERITY[level],"advisory_level":level,"region":name,"country_code":attributes.get("ISO_3"),"title":f"{name} Travel Advisory","summary":summary,"published_at":_epoch_ms(attributes.get("ADVDATE")),"updated_at":_epoch_ms(attributes.get("EditDate")),"departure":{"status":attributes.get("AD_OD_Status"),"text":departure or None,"date":attributes.get("AD_OD_Date")},"location":location,"source":{"provider_id":self.provider_id,"publisher":self.publisher,"delivery":"ArcGIS FeatureServer used by the official Travel Advisory Map","url":url,"layer_url":self.layer_url,"retrieved_at":retrieved_at,"authority":"primary"}})
        if not incidents: raise ValueError("State Department layer had no valid advisory records")
        incidents.sort(key=lambda item:(item["advisory_level"],item.get("published_at") or ""),reverse=True)
        return {"provider_id":self.provider_id,"publisher":self.publisher,"feed_url":self.layer_url,"retrieved_at":retrieved_at,"incidents":incidents}
