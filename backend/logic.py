
import json
from datetime import datetime

data: dict = {}
objects: dict = {}
events: dict = {} 

def loadLog(log: bytes):
    global data
    data = json.loads(log.decode('utf-8'))
    return len(data)

def uploadLog(file: str):
    global data
    try:
        with open(file, 'r') as f:
            data = json.load(f)
    except:
        return False
    return True  
    
def getObjects():
    global objects
    objects = {obj['id']: obj for obj in data["objects"]}
    return len(objects)

def getObjectTypes():
    types: list = []
    for objT in data["objectTypes"]:
        types.append(objT["name"])
    return types

def getEvents():
    global events
    events = {obj['id']: obj for obj in data["events"]}
    return len(events)

def getEventTypes():
    types: list = []
    for evT in data["eventTypes"]:
        types.append(evT["name"])
    return types

# check value in range defined by operator and N
def checkOpN(nQ: int, op: str, n: int):
    if op == "<":
        return nQ < n
    elif op == "<=":
        return nQ <= n
    elif op == ">":
        return nQ > n
    elif op == ">=":
        return nQ >= n
    elif op == "=":
        return nQ == n
    elif op == "!=":
        return nQ != n
    return False

def checkAttr(actual, op, val):
    if isinstance(actual, int):
        val = int(val)
    if op == "<":
        return actual < val
    elif op == "<=":
        return actual <= val
    elif op == ">":
        return actual > val
    elif op == ">=":
        return actual >= val
    elif op == "=":
        return actual == val
    elif op == "!=":
        return actual != val
    return False

def checkPhi(instance, phi: dict):
    for condition in phi.values():
        if condition["attr"] == "timestamp":
            if checkAttr(instance["time"], condition["op"], condition["val"]):
                break
            else:
                return False
        for a in instance["attributes"]:
            if a["name"] == condition["attr"]:
                if checkAttr(a["value"], condition["op"], condition["val"]):
                    pass
                else:
                    return False
    return True

# evaluation Event pattern
def evalP(et: str, phiet: dict, op: str, n: int, q: str, ot: str, phiot: dict):
    global events, objects
    #print("Evaluating P")
    E: dict = {}
    for e in events.values():
        if e["type"] == et: # same event type
            if checkPhi(e, phiet): # phiet conditions
                nQ = 0
                for qual in e["relationships"]: # search for e2o
                    if qual["qualifier"] == q: # same e2o qualifier
                        o = objects.get(qual["objectId"]) # get correlated obj
                        if o["type"] == ot: # same object type
                            if checkPhi(o, phiot): # phiot conditions
                                nQ += 1
                if checkOpN(nQ, op, n): # check number of qualified e2o
                    E[e["id"]] = e
    return E

def hasObjRt(obj, rtPsi: str):
    for rt in obj["relationships"]:
        if rt["qualifier"] == rtPsi:
            return True
    return False

def hasObjRtInv(obj, rtPsi: str):
    global objects
    for o in objects.values():
        for rt in o["relationships"]:
            if rt["qualifier"] == rtPsi:
                if rt["objectId"] == obj["id"]:
                    return True, o
    return False, None

def convertTimestamp(iso_timestamp: str):
    return int((datetime.strptime(iso_timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")).timestamp())

def evalPsi(eA: dict, psi: list, opD: str, td: int, eB: dict):
    global objects
    ePsiIn: dict = {}
    ePsiOut: dict = {}
    eAtemp: dict = eA.copy()
    eAunr: dict = {}
    eBtemp: dict = eB.copy()
    eBunr: dict = {}
    coupleN = 0    
    for ea in eA.values():
        for qual1 in ea["relationships"]:
            oa = objects.get(qual1["objectId"]) # get correlated obj
            oSource = {}
            oSource[qual1["objectId"]] = oa
            psiCheck = False
            for rtPsi in psi: # iterate all rt in psi
                oTemp = {}
                for os in oSource.values():
                    if os is not None:
                        if hasObjRt(os, rtPsi):
                            oTemp[os["id"]] = os
                        else:
                            inv, oInv = hasObjRtInv(os, rtPsi)
                            if inv:
                                oTemp[oInv["id"]] = oInv
                if len(oTemp) == 0:
                    psiCheck = False
                    break
                else:
                    psiCheck = True
                    oSource = oTemp
            if not(psiCheck):
                break
            else:
                for eb in eB.values():
                    for qual2 in eb["relationships"]:
                        if qual2["objectId"] in oSource:
                            ePsiIn["couple_"+str(coupleN)] = [ea, eb]
                            coupleN += 1
    toRemove = []
    for cId, couple in ePsiIn.items():
        ts1 = convertTimestamp(couple[0]["time"])
        ts2 = convertTimestamp(couple[1]["time"])
        diff = abs(ts1-ts2)
        if not(checkOpN(diff, opD, td)):
           ePsiOut[cId] = couple
           toRemove.append(cId)
        eAtemp.pop(couple[0]["id"], None)
        eBtemp.pop(couple[1]["id"], None)
    for cId in toRemove:
        ePsiIn.pop(cId, None)
    for eUnr in eAunr.values():
        eAunr["aCoupleUnr_"+str(coupleN)] = [eUnr, {}]
        coupleN += 1
    for eUnr in eBunr.values():
        eBunr["bCoupleUnr_"+str(coupleN)] = [{}, eUnr]
        coupleN += 1
    return ePsiIn, ePsiOut, eAunr, eBunr

def evalFpU(fp: str, eP: dict):
    m: dict = {}
    nm: dict = {}
    if fp == "occurs":
        m = eP.copy()
    elif fp == "absent": 
        nm = eP.copy()
    return m, nm

def existsC(c1: dict, psi: list, c2: dict):
    global objects, events
    for eb in events.values():
        for qual1 in c1["relationships"]:
            oa = objects.get(qual1["objectId"]) # get correlated obj
            oSource = {}
            oSource[qual1["objectId"]] = oa
            psiCheck = False
            for rtPsi in psi: # iterate all rt in psi
                oTemp = {}
                for os in oSource.values():
                    if os is not None:
                        if hasObjRt(os, rtPsi):
                            oTemp[os["id"]] = os
                        else:
                            inv, oInv = hasObjRtInv(os, rtPsi)
                            if inv:
                                oTemp[oInv["id"]] = oInv
                if len(oTemp) == 0:
                    psiCheck = False
                    break
                else:
                    psiCheck = True
                    oSource = oTemp
            if not(psiCheck):
                break
            else:
                if eb["id"] != c2["id"]:
                    for qual2 in eb["relationships"]:
                        if qual2["objectId"] in oSource:
                            return True
    return False

def evalFpB(fp: dict, ePsiIn: dict, ePsiOut: dict, eAunr: dict, eBunr: dict):
    m: dict = {}
    nm: dict = {}
    fpName = fp.fp
    if fpName == "coabsent": 
        m = {}
        nm = eBunr.copy()
    elif fpName == "coexist": 
        m = ePsiIn.copy()
        temp: dict = eAunr.copy()
        temp.update(ePsiOut)
        nm = temp.copy()
    elif fpName == "corequisite": 
        m = ePsiIn.copy()
        temp: dict = eAunr.copy()
        temp.update(eBunr)
        temp.update(ePsiOut)
        nm = temp.copy()
    elif fpName == "precedes": 
        m = eAunr.copy()
        temp: dict = eBunr.copy()
        temp.update(ePsiOut)
        nm = temp.copy()
        for cId, couple in ePsiIn.items():
            ts1 = convertTimestamp(couple[0]["time"])
            ts2 = convertTimestamp(couple[1]["time"])
            if ts1 < ts2:
                m[cId] = couple
            else:
                nm[cId] = couple
    elif fpName == "leadsTo": 
        m = {}
        temp: dict = eAunr.copy()
        temp.update(eBunr)
        temp.update(ePsiOut)
        nm = temp.copy()
        for cId, couple in ePsiIn.items():
            ts1 = convertTimestamp(couple[0]["time"])
            ts2 = convertTimestamp(couple[1]["time"])
            if ts1 < ts2:
                m[cId] = couple
            else:
                nm[cId] = couple
    elif fpName == "xLeadsTo": 
        m = {}
        temp: dict = eAunr.copy()
        temp.update(eBunr)
        temp.update(ePsiOut)
        nm = temp.copy()
        for cId, couple in ePsiIn.items():
            ts1 = convertTimestamp(couple[0]["time"])
            ts2 = convertTimestamp(couple[1]["time"])
            if ts2 < ts1:
                nm[cId] = couple
            elif existsC(couple[0], fp.psi, couple[1]):
                nm[cId] = couple
            else:
                m[cId] = couple
    elif fpName == "exclusive": 
        temp: dict = eAunr.copy()
        temp.update(eBunr)
        temp.update(ePsiOut)
        m = temp.copy()
        nm = ePsiIn.copy()
    elif fpName == "alternative":
        temp: dict = eAunr.copy()
        temp.update(eBunr)
        temp.update(ePsiIn)
        temp.update(ePsiOut)
        m = temp.copy()
        nm = {}
    return m, nm

def evalOCCRu(ePa: dict, fp: dict):
    #print("Evaluating OCCRu")
    eA = evalP(ePa.et, ePa.phiet, ePa.op, ePa.n, ePa.q, ePa.ot, ePa.phiot)
    #print("eA len: "+str(len(eA)))
    m, nm = evalFpU(fp.fp, eA)
    #print("m len: "+str(len(m)))
    #print("nm len: "+str(len(nm)))
    return {"matching": m, "nonmatching": nm}

def evalOCCRb(ePa: dict, fp: dict, ePb: dict):
    eA = evalP(ePa.et, ePa.phiet, ePa.op, ePa.n, ePa.q, ePa.ot, ePa.phiot)
    print("eA len: "+str(len(eA)))
    eB = evalP(ePb.et, ePb.phiet, ePb.op, ePb.n, ePb.q, ePb.ot, ePb.phiot)
    print("eB len: "+str(len(eB)))
    ePsiIn, ePsiOut, eAunr, eBunr = evalPsi(eA, fp.psi, fp.opD, fp.td, eB)
    print("ePsiIn len: "+str(len(ePsiIn)))
    print("ePsiOut len: "+str(len(ePsiOut)))
    print("eAunr len: "+str(len(eAunr)))
    print("eBunr len: "+str(len(eBunr)))
    m, nm = evalFpB(fp, ePsiIn, ePsiOut, eAunr, eBunr)
    print("m len: "+str(len(m)))
    print("nm len: "+str(len(nm)))
    return {"matching": m, "nonmatching": nm}